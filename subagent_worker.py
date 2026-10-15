"""独立开发子代理：复用 Runtime，修改通过任务审批，终端使用沙箱。"""

import contextlib
import json
import sys
import time
import os
import signal


def main():
    payload = json.loads(sys.stdin.buffer.read(262145))
    if sys.platform == "linux":
        import ctypes

        ctypes.CDLL(None).prctl(1, signal.SIGTERM)
        if os.getppid() != payload["owner_pid"]:
            return {"ok": False, "error": "任务宿主已退出，子代理未执行"}
    from config import model_config, approval_config
    from workspace import use_workspace
    from tool_registry import TOOL_REGISTRY
    from model_client import request_message
    from tool_runtime import execute_tool
    import tool_runtime

    allowed = {
        "read_file",
        "list_files",
        "search_file",
        "search_project",
        "edit_file",
        "create_file",
        "apply_changes",
        "run_tests",
        "start_pty",
        "list_tasks",
        "task_status",
        "task_wait",
        "task_input",
        "task_cancel",
    }
    for name in list(TOOL_REGISTRY):
        if name not in allowed:
            del TOOL_REGISTRY[name]
    from agent_proposals import PROPOSALS, propose_edit, propose_file
    from tool_registry import tool_spec, string_parameter

    for name, handler in (("propose_edit", propose_edit), ("propose_file", propose_file)):
        TOOL_REGISTRY[name] = tool_spec(
            "暂存文件修改建议，不写入；必须提供完整文件内容，由父代理审批后应用。",
            "read",
            {
                "path": string_parameter("项目文件路径", 1),
                "new_content": {"type": "string", "maxLength": 16000},
            },
            ["path", "new_content"],
            handler,
        )
    model_config.update(payload["model_config"])
    approval_config.update(payload["approval_config"])
    from harness.tasks.approvals import TaskApprovalStore

    approvals = TaskApprovalStore(payload["approval_db"])
    import permissions

    pending_diff = {"value": ""}
    tool_runtime.show_diff = lambda diff: pending_diff.update(value=diff)

    def confirm(name, target, details=""):
        diff = pending_diff["value"]
        pending_diff["value"] = ""
        if diff and diff not in details:
            details += "\n" + diff
        request = approvals.create(
            payload["task_id"], payload["approval_token"], name, target, details
        )
        while True:
            decision = approvals.poll(payload["task_id"], payload["approval_token"], request["id"])
            if decision["status"] in ("approved", "rejected"):
                return approvals.consume(
                    payload["task_id"], payload["approval_token"], request["id"]
                )
            if decision["status"] != "pending":
                return False
            time.sleep(0.2)

    permissions.confirm_tool = confirm
    context = payload.get("web_context")
    if context:
        from harness.tasks.runtime import TASK_BACKEND
        from web.task_service import TaskClient

        TASK_BACKEND.set(
            TaskClient(
                context["socket_path"], context["session_id"], context["run_id"], payload["task_id"]
            )
        )
    messages = list(payload["instructions"]) + [
        {
            "role": "system",
            "content": "你是独立开发子代理。完成指定任务，可以读取、修改、新建文件、运行测试及使用沙箱 PTY。修改必须通过 Runtime 的审批和冲突检查。不要要求用户替你操作终端；用 task_input/task_wait，并可用 list_tasks 查询后台任务。不能继续创建子代理。也可用 propose_edit/propose_file 仅提交建议。只依据真实工具结果汇报改动和验证。",
        },
        {"role": "user", "content": "关注目录: " + payload["path"] + "\n任务: " + payload["task"]},
    ]
    calls = 0
    operations = []
    with use_workspace(payload["workspace"]), contextlib.redirect_stdout(sys.stderr):
        # 子代理不访问父会话，审计仍通过共享执行入口记录。
        for _ in range(min(8, payload["agent_config"]["max_rounds"])):
            message = request_message(messages, include_context=False)
            if not message.get("tool_calls"):
                return {
                    "ok": True,
                    "reply": message["content"][:4000],
                    "reply_truncated": len(message["content"]) > 4000,
                    "tool_calls": calls,
                    "proposals": list(PROPOSALS),
                    "operations": operations,
                }
            messages.append(message)
            for call in message["tool_calls"]:
                calls += 1
                if calls > min(12, payload["agent_config"]["max_tool_calls"]):
                    return {"ok": False, "error": "子代理工具预算耗尽"}
                function = call["function"]
                from approval import task_scope

                with task_scope(payload["task"]):
                    result = execute_tool(function["name"], function.get("arguments", {}))
                operations.append(
                    {
                        "tool": function["name"],
                        "path": function.get("arguments", {}).get("path"),
                        "ok": result.get("ok") is True,
                        "changed": result.get("changed", False),
                        "exit_code": result.get("exit_code"),
                        "task_id": result.get("task_id"),
                    }
                )
                item = {
                    "role": "tool",
                    "tool_name": function["name"],
                    "content": json.dumps(result, ensure_ascii=False),
                }
                if call.get("id"):
                    item["tool_call_id"] = call["id"]
                messages.append(item)
    return {"ok": False, "error": "子代理轮次预算耗尽"}


if __name__ == "__main__":
    try:
        result = main()
    except Exception as error:
        result = {"ok": False, "error": "子代理失败: " + type(error).__name__}
    print(json.dumps(result, ensure_ascii=False))
