"""OpenAI 兼容 Chat Completions；内部消息仍统一使用字典参数。"""

import json
from streaming import ModelResponseError, validate_message


def wire_messages(messages):
    result, pending = [], []
    for number, message in enumerate(messages):
        role = message["role"]
        item = {"role": role, "content": message.get("content", "")}
        # 部分兼容 API 需要回传此不透明协议字段；它不是 UI 正文或授权。
        reasoning = message.get("reasoning_content")
        if role == "assistant" and reasoning is not None:
            if not isinstance(reasoning, str):
                raise ModelResponseError("reasoning_content 必须是字符串")
            item["reasoning_content"] = reasoning
        if role == "assistant" and message.get("tool_calls"):
            pending = []
            item["tool_calls"] = []
            for index, call in enumerate(message["tool_calls"]):
                identifier = call.get("id") or f"call_{number}_{index}"
                if not isinstance(identifier, str) or not identifier or identifier in pending:
                    raise ModelResponseError("工具调用 ID 无效或重复")
                pending.append(identifier)
                function = call["function"]
                item["tool_calls"].append(
                    {
                        "id": identifier,
                        "type": "function",
                        "function": {
                            "name": function["name"],
                            "arguments": json.dumps(
                                function.get("arguments", {}), ensure_ascii=False
                            ),
                        },
                    }
                )
        elif role == "tool":
            if not pending:
                raise ModelResponseError("工具结果没有对应调用")
            identifier = pending.pop(0)
            if message.get("tool_call_id", identifier) != identifier:
                raise ModelResponseError("工具结果 ID 不匹配")
            item["tool_call_id"] = identifier
        result.append(item)
    return result


def normalize(message):
    if not isinstance(message, dict):
        raise ModelResponseError("API 缺少消息")
    result = {
        "role": "assistant",
        "content": "" if message.get("content") is None else message.get("content"),
        "tool_calls": [],
    }
    if message.get("reasoning_content") is not None:
        if not isinstance(message["reasoning_content"], str):
            raise ModelResponseError("reasoning_content 必须是字符串")
        result["reasoning_content"] = message["reasoning_content"]
    for call in message.get("tool_calls") or []:
        try:
            function = call["function"]
            arguments = json.loads(function["arguments"])
            identifier = call["id"]
            if not isinstance(identifier, str) or not identifier:
                raise ValueError()
            result["tool_calls"].append(
                {
                    "id": identifier,
                    "type": "function",
                    "function": {"name": function["name"], "arguments": arguments},
                }
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ModelResponseError("API 工具调用格式错误") from error
    validate_message(result)
    identifiers = [call["id"] for call in result["tool_calls"]]
    if len(set(identifiers)) != len(identifiers):
        raise ModelResponseError("API 工具 ID 重复")
    return result


def collect_sse(response, max_bytes, on_content=None):
    total, content, calls, event = 0, "", {}, []
    reasoning = None
    finished = False
    while True:
        line = response.readline(max_bytes - total + 1)
        total += len(line)
        if total > max_bytes:
            raise ModelResponseError("模型响应超过大小上限")
        if not line:
            raise ModelResponseError("API 流提前结束，工具未执行")
        try:
            line = line.decode("utf-8").rstrip("\r\n")
        except UnicodeError as error:
            raise ModelResponseError("API 流编码错误") from error
        if line.startswith("data:"):
            event.append(line[5:].lstrip(" "))
        if line or not event:
            continue
        data = "\n".join(event)
        event = []
        if data == "[DONE]":
            if not finished:
                raise ModelResponseError("API 流缺少完成原因")
            return normalize(
                {
                    "content": content,
                    "reasoning_content": reasoning,
                    "tool_calls": [calls[key] for key in sorted(calls)],
                }
            )
        try:
            chunk = json.loads(data)
            if "error" in chunk:
                raise ValueError()
            choices = chunk.get("choices", [])
            if not choices:
                continue
            choice = choices[0]
            if finished:
                raise ValueError()
            delta = choice.get("delta") or {}
            fragment = delta.get("reasoning_content")
            if fragment is not None:
                if not isinstance(fragment, str):
                    raise ValueError()
                reasoning = (reasoning or "") + fragment
            text = delta.get("content") or ""
            if not isinstance(text, str):
                raise ValueError()
            content += text
            if text and on_content:
                on_content(text)
            for part in delta.get("tool_calls") or []:
                index = part["index"]
                if type(index) is not int or not 0 <= index < 64:
                    raise ValueError()
                target = calls.setdefault(
                    index, {"id": "", "function": {"name": "", "arguments": ""}}
                )
                if part.get("id"):
                    if target["id"] and target["id"] != part["id"]:
                        raise ValueError()
                    target["id"] = part["id"]
                for field in ("name", "arguments"):
                    target["function"][field] += part.get("function", {}).get(field, "")
            reason = choice.get("finish_reason")
            if reason is not None:
                if reason not in ("stop", "tool_calls"):
                    raise ModelResponseError("API 响应未完整完成: " + str(reason))
                finished = True
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            if isinstance(error, ModelResponseError):
                raise
            raise ModelResponseError("API SSE 数据格式错误") from error
