"""四层护栏。启发式标记不等于注入检测保证，授权仍由 Runtime 决定。"""

import json
import os
import re

from streaming import validate_message

MAX_INPUT = 12000
MAX_RESULT = 24000
SUSPICIOUS = re.compile(
    r"ignore\s+(all|previous)|忽略.{0,12}(指令|要求)|用户已批准|system\s*prompt", re.I
)
SECRET = re.compile(
    r"(?i)(?:sk-[a-z0-9_-]{20,}|(?:api[_-]?key|password|token)\s*[:=]\s*[\w-]{16,})"
)


def check_input(text):
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_INPUT or "\x00" in text:
        raise ValueError("消息必须为非空文字，不含空字符，最多 12000 字符")
    if SECRET.search(text):
        raise ValueError("输入疑似含密钥，请移除后发送；密钥仅通过服务器环境配置")
    return {
        "layer": "input",
        "warnings": ["疑似指令注入，按数据处理"] if SUSPICIOUS.search(text) else [],
    }


def check_model(message):
    validate_message(message)
    calls = message.get("tool_calls", [])
    if not isinstance(calls, list) or len(calls) > 12:
        raise ValueError("单批工具声明数量无效")
    ids = set()
    for call in calls:
        fn = call.get("function") if isinstance(call, dict) else None
        if not isinstance(fn, dict) or not isinstance(fn.get("name"), str) or not fn["name"]:
            raise ValueError("模型工具调用结构无效")
        if not isinstance(fn.get("arguments", {}), dict):
            raise ValueError("工具参数必须为对象")
        identifier = call.get("id")
        if identifier:
            if identifier in ids:
                raise ValueError("工具调用 ID 重复")
            ids.add(identifier)
    return message


def redact(text):
    text = str(text)
    from config import model_config

    # 用户 TOML 可以命名另一变量；worker 的可信模型配置已合并它。
    names = {
        os.environ.get("AI_CLI_API_KEY_ENV", "OPENAI_API_KEY"),
        model_config.get("api_key_env", "OPENAI_API_KEY"),
    }
    for name in names:
        key = os.environ.get(name, "")
        if len(key) >= 8:
            text = text.replace(key, "[REDACTED]")
    return SECRET.sub("[REDACTED]", text)


def bound_result(result):
    if not isinstance(result, dict) or type(result.get("ok")) is not bool:
        return {"ok": False, "error": "工具结果结构无效"}
    encoded = redact(json.dumps(result, ensure_ascii=False, default=str))
    if len(encoded) <= MAX_RESULT:
        return json.loads(encoded)
    # 不把截断后的 JSON 冒充完整结构；保留外层状态，内容为明确的数据摘录。
    return {
        "ok": result["ok"],
        "truncated": True,
        "error": redact(result.get("error", "")),
        "excerpt": encoded[: MAX_RESULT - 300],
        "guardrail_warning": "返回值超预算；未展示部分不可据此判断",
    }
