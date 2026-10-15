"""所有模型工具的共享执行入口：验证、授权、执行、规范结果和记录。"""

from audit import record_tool_event
import json
from jsonschema import Draft202012Validator
from permissions import (
    authorize_external_tool,
    authorize_tool,
    check_tool_policy,
    resolve_project_path,
)
from tool_registry import TOOL_REGISTRY
from hooks import run_hooks
from tool_display import tool_started, tool_finished, show_diff, emit, short_text


def validate_arguments(spec, arguments):
    if not isinstance(arguments, dict):
        return {"ok": False, "error": "工具参数必须是字典"}
    schema = spec["parameters"]
    normalized = dict(spec.get("defaults", {}))
    normalized.update(arguments)
    error = next(Draft202012Validator(schema).iter_errors(normalized), None)
    if error is not None:
        location = ".".join(str(part) for part in error.path) or "参数"
        return {"ok": False, "error": "工具参数不符合声明: " + location}
    return {"ok": True, "arguments": normalized}


def _execute_tool(name, arguments, source):
    if not isinstance(name, str) or name not in TOOL_REGISTRY:
        return {"ok": False, "error": "未知工具"}
    spec = TOOL_REGISTRY[name]
    operation = spec.get("operation")
    policy = check_tool_policy(operation, source)
    if not policy["ok"]:
        return policy
    validated = validate_arguments(spec, arguments)
    if not validated["ok"]:
        return validated
    normalized = validated["arguments"]
    if spec.get("kind") in ("task", "task_list"):
        from harness.tasks.runtime import task_access
        from approval import authorize_action

        access = None
        if spec.get("kind") == "task":
            access = task_access(normalized["task_id"])
            if not access.get("ok"):
                return access
        hooks = run_hooks(
            "before_tool",
            {"name": name, "operation": operation, "source": source, "arguments": normalized},
        )
        if not hooks["ok"]:
            return hooks
        approved = authorize_action(
            name,
            operation,
            normalized.get("task_id", "current_session"),
            source,
            json.dumps(normalized, ensure_ascii=False),
            prepared={"task_access": access},
        )
        if not approved["ok"]:
            return approved
        return spec["handler"](**normalized)
    if spec.get("kind") == "mcp":
        hook_result = run_hooks(
            "before_tool",
            {"name": name, "operation": operation, "source": source, "arguments": normalized},
        )
        if not hook_result["ok"]:
            return hook_result
        details = spec["connection"]["details"]
        details += "\n工具参数: " + json.dumps(normalized, ensure_ascii=False)
        authorization = authorize_external_tool(name, spec["server_name"], source, details)
        if not authorization["ok"]:
            return authorization
        return spec["handler"](normalized)
    if "path" not in normalized:
        return {"ok": False, "error": "当前执行器要求声明 path 参数"}
    original_path = normalized["path"]
    checked = resolve_project_path(original_path)
    if not checked["ok"]:
        return checked
    normalized["path"] = checked["path"]

    hook_result = run_hooks(
        "before_tool",
        {"name": name, "operation": operation, "source": source, "arguments": normalized},
    )
    if not hook_result["ok"]:
        return hook_result

    if operation == "write":
        from approval import write_boundary, record_decision

        boundary = write_boundary(normalized["path"])
        if not boundary["ok"]:
            record_decision(name, "rule", "deny", "client_control")
            return boundary

    prepared = None
    if spec.get("prepare") is not None:
        # 准备阶段保留原始路径，让新建工具也能检查其中的符号链接。
        prepared = spec["prepare"](**{**normalized, "path": original_path})
        if not isinstance(prepared, dict) or type(prepared.get("ok")) is not bool:
            return {"ok": False, "error": "工具准备结果格式错误"}
        if not prepared["ok"]:
            return prepared
        if operation == "write" and prepared.get("changed") is False:
            return {"ok": True, "changed": False, "message": "文件内容没有变化"}
        if "diff" in prepared:
            show_diff(prepared["diff"])

    details = spec.get("details", "")
    if "keyword" in normalized:
        details = "关键词: " + normalized["keyword"]
    if prepared is not None:
        details = prepared.get("details", details)
    authorized = authorize_tool(name, operation, original_path, source, details, prepared=prepared)
    if not authorized["ok"]:
        return authorized
    if authorized["path"] != normalized["path"]:
        return {"ok": False, "error": "工具准备期间路径目标已变化，请重新提交"}

    from contextlib import nullcontext
    from harness.infrastructure.workspace_locks import workspace_write_lock
    from permissions import PROJECT_ROOT

    lock = workspace_write_lock(PROJECT_ROOT) if operation == "write" else nullcontext()
    # 审批和准备不持锁；最终提交串行，handler 在锁内检查原文件是否变化。
    with lock:
        if prepared is not None:
            return spec["handler"](prepared)
        return spec["handler"](**normalized)


def _execute_and_normalize(name, arguments, source="model"):
    """source 由可信调用方指定，不从模型 arguments 中读取。"""
    tool_started(name, arguments)
    try:
        result = _execute_tool(name, arguments, source)
    except KeyboardInterrupt:
        result = {
            "ok": False,
            "cancelled": True,
            "error": "工具已取消；已完成的操作不会回滚，写入或外部操作请检查实际状态",
        }
    except Exception as error:
        error_type = type(error).__name__
        emit("工具执行异常: " + error_type + " " + short_text(error), "ansired")
        result = {"ok": False, "error": "工具执行异常: " + error_type}
    if not isinstance(result, dict) or type(result.get("ok")) is not bool:
        result = {"ok": False, "error": "工具返回结果必须包含布尔类型的 ok"}
    spec = TOOL_REGISTRY.get(name) if isinstance(name, str) else None
    if spec is not None:
        try:
            hook_result = run_hooks(
                "after_tool",
                {
                    "name": name,
                    "operation": spec.get("operation"),
                    "source": source,
                    "arguments": arguments,
                    "result": result,
                },
            )
        except KeyboardInterrupt:
            result = {**result, "cancelled": True}
            hook_result = {"ok": False, "error": "执行后 Hook 已取消；工具结果保留"}
        if not hook_result["ok"]:
            result = dict(result)
            result["hook_warning"] = hook_result["error"]
    return result


def execute_tool(name, arguments, source="model"):
    from approval import decision_scope

    with decision_scope() as decisions:
        result = _execute_and_normalize(name, arguments, source)
        if decisions:
            result = {**result, "approval": list(decisions)}
        record_tool_event(name if isinstance(name, str) else "invalid_tool", result)
        tool_finished(name, result)
        return result
