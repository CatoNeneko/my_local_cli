"""可信本地 Hook：执行前可拒绝，执行后失败只附加警告，不伪装回滚。"""

from copy import deepcopy

from config import hooks_config


def deny_configured_tools(context):
    denied = hooks_config.get("denied_tools", [])
    if not isinstance(denied, list) or not all(isinstance(name, str) for name in denied):
        return {"ok": False, "error": "Hook 拒绝名单配置无效"}
    if context["name"] in denied:
        return {"ok": False, "error": "Hook 策略拒绝工具: " + context["name"]}
    return {"ok": True}


def report_write_result(context):
    if context["operation"] == "write":
        status = "成功" if context["result"]["ok"] else "失败或未执行"
        print("[Hook] " + context["name"] + ": " + status)
    return {"ok": True}


HOOK_HANDLERS = {
    "deny_configured_tools": deny_configured_tools,
    "report_write_result": report_write_result,
}


def run_hooks(event, context):
    names = hooks_config.get(event)
    if not isinstance(names, list):
        return {"ok": False, "error": "缺少有效的 Hook 配置: " + event}
    for name in names:
        try:
            if not isinstance(name, str) or name not in HOOK_HANDLERS:
                raise ValueError("未知 Hook")
            # 回调只收到快照，不能通过修改字典改变待执行参数或结果。
            result = HOOK_HANDLERS[name](deepcopy(context))
            if not isinstance(result, dict) or type(result.get("ok")) is not bool:
                raise ValueError("Hook 返回格式无效")
            if not result["ok"]:
                return {
                    "ok": False,
                    "error": "Hook " + name + ": " + str(result.get("error", "拒绝")),
                }
        except Exception as error:
            return {"ok": False, "error": "Hook " + str(name) + " 失败: " + type(error).__name__}
    return {"ok": True}
