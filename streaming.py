"""Ollama NDJSON 响应收集；结束标记到达前不返回可执行工具调用。"""
import json


class ModelResponseError(ValueError):
    pass


def parse_json(raw):
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ModelResponseError("模型响应不是有效的 UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ModelResponseError("模型响应必须是字典")
    if "error" in value:
        raise ModelResponseError("模型服务报告错误: " + str(value["error"])[:500])
    return value


def validate_message(message):
    if not isinstance(message, dict):
        raise ModelResponseError("message 必须是字典")
    for field in ("content", "thinking"):
        if not isinstance(message.get(field, ""), str):
            raise ModelResponseError(field + " 必须是字符串")
    calls = message.get("tool_calls", [])
    if not isinstance(calls, list):
        raise ModelResponseError("tool_calls 必须是列表")
    for call in calls:
        function = call.get("function") if isinstance(call, dict) else None
        if not isinstance(function, dict):
            raise ModelResponseError("工具调用缺少 function")
        if not isinstance(function.get("name"), str) or not function["name"]:
            raise ModelResponseError("工具名称必须是非空字符串")
        if not isinstance(function.get("arguments", {}), dict):
            raise ModelResponseError("Ollama 工具参数必须是完整字典")


def collect_stream(response, max_bytes, on_content=None):
    message = {"role": "assistant", "content": "", "tool_calls": []}
    received_bytes = 0
    seen_indices = set()
    while True:
        try:
            line = response.readline(max_bytes - received_bytes + 1)
        except TimeoutError:
            raise
        except OSError as error:
            raise ModelResponseError("流式读取失败: " + type(error).__name__) from error
        if not line:
            raise ModelResponseError("流式响应提前结束，未收到 done 标记；本次未完成响应中的工具调用未执行")
        received_bytes += len(line)
        if received_bytes > max_bytes:
            raise ModelResponseError("模型响应超过大小上限")
        if not line.strip():
            continue
        chunk = parse_json(line)
        part = chunk.get("message", {})
        validate_message(part)
        if type(chunk.get("done")) is not bool:
            raise ModelResponseError("流式响应缺少布尔类型 done 标记")
        for call in part.get("tool_calls", []):
            index = call["function"].get("index")
            if index is not None:
                if type(index) is not int or index < 0 or index in seen_indices:
                    raise ModelResponseError("流式工具调用 index 无效或重复")
                seen_indices.add(index)
            message["tool_calls"].append(call)
        content = part.get("content", "")
        message["content"] += content
        if part.get("thinking"):
            message["thinking"] = message.get("thinking", "") + part["thinking"]
        if content and on_content is not None:
            on_content(content)
        if chunk["done"]:
            return message
