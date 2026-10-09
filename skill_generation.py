"""模型生成 Skill 草稿，交给统一写入入口确认并保存。"""
from model_client import request_message
from skill_files import check_new_skill_target
from skills import MAX_SKILL_BYTES, check_skill_path
from tool_runtime import execute_tool


def generate_skill(name, purpose):
    named = check_skill_path(name)
    if not named["ok"]:
        return named
    path = "skills/" + name + "/SKILL.md"
    target = check_new_skill_target(path)
    if not target["ok"]:
        return target
    if not isinstance(purpose, str) or not purpose.strip() or len(purpose) > 2000:
        return {"ok": False, "error": "用途必须是 1～2000 字符的文字"}
    messages = [
        {"role": "system", "content": (
            "为 Python 终端编程助手生成一份中文 SKILL.md。只返回 Markdown 正文，"
            "不要外层代码围栏。包含用途、适用条件、步骤和验收标准。"
            "它是可复用的任务说明，不是程序；不要请求绕过权限、自动执行命令或虚构测试。"
            "实际读取、修改和测试应使用客户端提供的工具与权限流程。"
        )},
        {"role": "user", "content": "Skill 名称: " + name + "\n用途: " + purpose}
    ]
    try:
        reply = request_message(messages, use_tools=False, include_context=False)
        if not isinstance(reply, dict) or reply.get("tool_calls"):
            return {"ok": False, "error": "生成失败：模型应返回文字草稿，不能调用工具"}
        content = reply.get("content")
        if not isinstance(content, str) or not content.strip() or "\x00" in content:
            return {"ok": False, "error": "生成失败：模型未返回有效文字"}
        content = content.strip()
        if content.startswith("```") or len(content.encode("utf-8")) > MAX_SKILL_BYTES:
            return {"ok": False, "error": "生成失败：草稿含外层代码围栏或超过 32 KiB"}
        return execute_tool("create_skill", {"path": path, "new_content": content + "\n"}, source="user")
    except KeyboardInterrupt:
        return {'ok': False, 'cancelled': True, 'error': 'Skill 生成已取消；已完成的写入不会回滚'}
    except Exception as error:
        return {"ok": False, "error": "Skill 生成失败: " + type(error).__name__}
