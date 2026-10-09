from config import model_config
from tools import get_tool_definitions
from context_window import prepare_context
import json
import os
import urllib.request
from api_adapter import wire_messages, normalize, collect_sse
from streaming import ModelResponseError, collect_stream, parse_json, validate_message


class NoAuthRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ModelResponseError("携带 API 密钥的请求拒绝重定向")


def request_message(messages, *, use_tools=True, include_context=True, stream=False, on_content=None, timeout=120):
    if type(timeout) not in (int, float) or not 0 < timeout <= 120:
        raise ModelResponseError("模型请求超时必须在 0–120 秒之间")
    max_bytes = model_config.get("max_response_bytes")
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ModelResponseError("模型响应大小上限必须是正整数")
    tools = get_tool_definitions() if use_tools else []
    if use_tools and include_context:
        from compaction import maybe_compact
        maybe_compact(messages, tools)
    context = prepare_context(messages, tools, include_context)
    if context["omitted_messages"]:
        print("[上下文] 本次省略", context["omitted_messages"], "条历史消息；完整记录仍保存在磁盘")
    data = {
        "model": model_config["model"],
        "messages": context["messages"],
        "stream": stream,
        "tools": tools
    }

    provider = model_config.get('provider', 'ollama')
    key = ""
    headers = {'Content-Type': 'application/json'}
    base = model_config['base_url'].rstrip('/')
    if provider == 'openai':
        data['messages'] = wire_messages(data['messages'])
        if not tools:
            data.pop('tools')
        endpoint = base + '/chat/completions' if base.endswith('/v1') else base + '/v1/chat/completions'
        key = os.environ.get(model_config.get('api_key_env', 'OPENAI_API_KEY'), '')
        if key:
            headers['Authorization'] = 'Bearer ' + key
    elif provider == 'ollama':
        endpoint = base + '/api/chat'
    else:
        raise ModelResponseError('未知模型 provider')
    request_body = json.dumps(data, ensure_ascii=False).encode("utf-8")

    request = urllib.request.Request(
        url=endpoint,
        data=request_body,
        headers=headers,
        method="POST"
    )

    opener = urllib.request.build_opener(NoAuthRedirect()).open if key else urllib.request.urlopen
    with opener(request, timeout=timeout) as response:
        if stream:
            return (collect_sse if provider == "openai" else collect_stream)(response, max_bytes, on_content)
        try:
            raw = response.read(max_bytes + 1)
        except TimeoutError:
            raise
        except OSError as error:
            raise ModelResponseError("读取模型响应失败: " + type(error).__name__) from error
    if len(raw) > max_bytes:
        raise ModelResponseError("模型响应超过大小上限")
    result = parse_json(raw)
    if provider == 'openai':
        try:
            choice = result['choices'][0]
            if choice.get('finish_reason') not in ('stop', 'tool_calls'):
                raise ModelResponseError('API 响应未完整完成')
            message = normalize(choice['message'])
        except (KeyError, IndexError, TypeError) as error:
            raise ModelResponseError('API 缺少 choices 消息') from error
    else:
        message = result.get("message")
    validate_message(message)
    if on_content is not None and message.get("content"):
        on_content(message["content"])
    return message

def generate_reply(messages):
    # 保留旧接口，复用同一个请求实现，不再维护两套流式解析。
    from console_output import ConsoleOutput
    output = ConsoleOutput()
    try:
        message = request_message(messages, use_tools=False, stream=model_config['stream'], on_content=output.write)
    finally:
        output.end()
    return message.get('content', '')
