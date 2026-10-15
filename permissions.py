"""共享路径边界与授权策略；模型参数不能改变策略或调用来源。"""

import os
from pathlib import Path

from config import permission_config
from tool_display import safe_text


PROJECT_ROOT = Path(__file__).resolve().parent


def resolve_project_path(path):
    if not isinstance(path, str) or not path or "\x00" in path:
        return {"ok": False, "error": "路径必须是非空字符串，且不能包含空字符"}
    try:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / candidate
        resolved_path = candidate.resolve()
        if not resolved_path.is_relative_to(PROJECT_ROOT):
            return {"ok": False, "error": "禁止访问项目目录之外的文件"}
        # 对真实目标检查，避免通过项目内符号链接读取受保护内容。
        relative = resolved_path.relative_to(PROJECT_ROOT)
        if any(part in permission_config["blocked_names"] for part in relative.parts):
            return {"ok": False, "error": "禁止访问项目内部环境、控制配置或私有记录"}
        return {"ok": True, "path": str(resolved_path)}
    except (OSError, ValueError, RuntimeError):
        return {"ok": False, "error": "无法解析文件路径"}


def confirm_tool(name, path, details=""):
    from terminal_input import request_confirmation

    prompt = "请求调用 " + name + "\n目标: " + path
    if details:
        prompt += "\n参数: " + details
    return request_confirmation(safe_text(prompt))


def authorize_tool(name, operation, path, source="model", details="", *, prepared=None):
    # 缺少策略或未知来源一律拒绝，不默认放行新工具。
    policy_result = check_tool_policy(operation, source)
    if not policy_result["ok"]:
        return policy_result
    checked = resolve_project_path(path)
    if not checked["ok"]:
        return checked
    from approval import authorize_action

    approved = authorize_action(
        name, operation, checked["path"], source, details, prepared=prepared
    )
    if not approved["ok"]:
        return approved
    rechecked = resolve_project_path(path)
    if not rechecked["ok"]:
        return rechecked
    if rechecked["path"] != checked["path"]:
        return {"ok": False, "error": "确认期间路径目标已变化，请重新提交"}
    return rechecked


def check_tool_policy(operation, source):
    policy = permission_config["confirmation"].get(source)
    if not isinstance(policy, dict) or operation not in policy:
        return {"ok": False, "error": "缺少有效的工具权限策略"}
    if type(policy[operation]) is not bool:
        return {"ok": False, "error": "确认策略必须是布尔值"}
    return {"ok": True, "requires_confirmation": policy[operation]}


def authorize_external_tool(name, target, source="model", details=""):
    """外部服务采用 execute 策略；其路径参数不能假装受本地文件边界保护。"""
    policy = check_tool_policy("execute", source)
    if not policy["ok"]:
        return policy
    from approval import record_decision

    accepted = not policy["requires_confirmation"] or confirm_tool(name, target, details)
    decision = record_decision(
        name,
        "human" if policy["requires_confirmation"] else "rule",
        "allow" if accepted else "deny",
        "external_service",
    )
    return {
        "ok": accepted,
        "approval": [decision],
        **({} if accepted else {"error": "用户拒绝执行外部服务"}),
    }


def protected_project_paths(root):
    """找到需要在沙箱中遮蔽的路径，使用同一拒绝名单并跳过受保护目录。"""
    blocked = set(permission_config["blocked_names"])
    found = []

    def fail(error):
        raise error

    for directory, directories, files in os.walk(root, followlinks=False, onerror=fail):
        for name in list(directories):
            item = Path(directory) / name
            if name in blocked:
                directories.remove(name)
                found.append((item.relative_to(root), True))
            elif item.is_symlink():
                directories.remove(name)
        for name in files:
            if name in blocked:
                item = Path(directory) / name
                found.append((item.relative_to(root), False))
    return found
