# model_client.py：源码导读

统一HTTP模型访问；上下文、协议选择、有限响应与回调。

先读专题：[02-agent.md](../02-agent.md)。

实际源码：[model_client.py](../../../model_client.py)。

快照 SHA256：`cb15dc6f0490c88938612b2bb5055b2a8aa81a0d34608ee10f138c2ac76a9c9c`；97 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 1 | `from config import model_config` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 2 | `from tools import get_tool_definitions` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `from context_window import prepare_context` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `import os` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `import urllib.request` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `from api_adapter import wire_messages, normalize, collect_sse` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `from streaming import ModelResponseError, collect_stream, parse_json, validate_message` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [NoAuthRedirect.redirect_request](#noauthredirect-redirect-request) | [12](../../../model_client.py#L12) | 携带密钥请求不允许HTTP重定向。 |
| [request_message](#request-message) | [16](../../../model_client.py#L16) | 请求上下文、动态声明、HTTP协议分流、响应限额与统一消息返回。 |
| [generate_reply](#generate-reply) | [89](../../../model_client.py#L89) | 保留旧文字接口，禁工具请求并复用流式输出。 |

<a id="noauthredirect-redirect-request"></a>
## NoAuthRedirect.redirect_request

携带密钥请求不允许HTTP重定向。

```python
def redirect_request(self, request, fp, code, msg, headers, newurl)
```

位置：[12行](../../../model_client.py#L12) 至快照 13 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `request` | `未显式注解` | HTTP Request对象或协议请求，不等于模型回复。 |
| `fp` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `code` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `msg` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `headers` | `未显式注解` | Content-Type与可选授权HTTP头，不写入聊天。 |
| `newurl` | `未显式注解` | HTTP重定向目标，携带密钥时拒绝跳转。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ModelResponseError`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 13 | 函数体 | 抛出 `ModelResponseError('携带 API 密钥的请求拒绝重定向')`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="request-message"></a>
## request_message

请求上下文、动态声明、HTTP协议分流、响应限额与统一消息返回。

```python
def request_message(messages, *, use_tools=True, include_context=True, stream=False, on_content=None, timeout=120)
```

位置：[16行](../../../model_client.py#L16) 至快照 87 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `messages` | `未显式注解` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |
| `use_tools` | `未显式注解` | 是否向模型提供工具声明；独立审查/摘要禁用。 |
| `include_context` | `未显式注解` | 是否注入项目与会话上下文；独立请求通常关闭。 |
| `stream` | `未显式注解` | 本次请求是否分块返回；不自动等于所有接口都流式。 |
| `on_content` | `未显式注解` | 收到流式文字时调用的函数引用，None表示不回调。 |
| `timeout` | `未显式注解` | 操作/任务超时秒数。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ModelResponseError`、`NoAuthRedirect`、`base.endswith`、`choice.get`、`collect_sse if provider == 'openai' else collect_stream`、`data.pop`、`get_tool_definitions`、`json.dumps`、`json.dumps(data, ensure_ascii=False).encode`、`len`、`maybe_compact`、`message.get`、`model_config.get`、`model_config['base_url'].rstrip`、`normalize`、`on_content`、`opener`、`os.environ.get`、`parse_json`、`prepare_context`、`print`、`response.read`、`result.get`、`type`、`urllib.request.Request`、`urllib.request.build_opener`、`validate_message`、`wire_messages`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 19 | `max_bytes` | `model_config.get('max_response_bytes')` | 模型响应捕获字节上限。 |
| 22 | `tools` | `get_tool_definitions() if use_tools else []` | 发给模型的工具声明列表，不含handler函数对象。 |
| 26 | `context` | `prepare_context(messages, tools, include_context)` | 资源上下文或准备的模型请求上下文；看当前来源区分。 |
| 29 | `data` | `{'model': model_config['model'], 'messages': context['messages'], 'stream': stream, 'tools': tools}` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 36 | `provider` | `model_config.get('provider', 'ollama')` | ollama/openai协议选择，不是主Codex模型配置。 |
| 37 | `key` | `''` | 环境读取的密钥或普通字典键，必须以当前函数来源区分；密钥不能记录。 |
| 38 | `headers` | `{'Content-Type': 'application/json'}` | Content-Type与可选授权HTTP头，不写入聊天。 |
| 39 | `base` | `model_config['base_url'].rstrip('/')` | 去掉末尾斜杠的模型服务地址，用于构造endpoint。 |
| 41 | `data['messages']` | `wire_messages(data['messages'])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 44 | `endpoint` | `base + '/chat/completions' if base.endswith('/v1') else base + '/v1/chat/completions'` | 本次模型HTTP POST目标URL。 |
| 45 | `key` | `os.environ.get(model_config.get('api_key_env', 'OPENAI_API_KEY'), '')` | 环境读取的密钥或普通字典键，必须以当前函数来源区分；密钥不能记录。 |
| 47 | `headers['Authorization']` | `'Bearer ' + key` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 49 | `endpoint` | `base + '/api/chat'` | 本次模型HTTP POST目标URL。 |
| 52 | `request_body` | `json.dumps(data, ensure_ascii=False).encode('utf-8')` | 将请求字典编码成UTF-8字节，用于HTTP发送。 |
| 54 | `request` | `urllib.request.Request(url=endpoint, data=request_body, headers=headers, method='POST')` | HTTP Request对象或协议请求，不等于模型回复。 |
| 61 | `opener` | `urllib.request.build_opener(NoAuthRedirect()).open if key else urllib.request.urlopen` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 66 | `raw` | `response.read(max_bytes + 1)` | 未解码字节/完整输出快照，按编码与限额再处理。 |
| 73 | `result` | `parse_json(raw)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 76 | `choice` | `result['choices'][0]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 79 | `message` | `normalize(choice['message'])` | 单条聊天/协议消息字典；角色和字段随当前分支而定。 |
| 83 | `message` | `result.get('message')` | 单条聊天/协议消息字典；角色和字段随当前分支而定。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 17 | 函数体 | 条件 `type(timeout) not in (int, float) or not 0 < timeout <= 120`：真时执行body，假时进入else/后续。 |
| 18 | 函数体 / 条件为真 | 抛出 `ModelResponseError('模型请求超时必须在 0–120 秒之间')`。 |
| 19 | 函数体 | 将 `model_config.get('max_response_bytes')` 赋给 `max_bytes`。 |
| 20 | 函数体 | 条件 `type(max_bytes) is not int or max_bytes <= 0`：真时执行body，假时进入else/后续。 |
| 21 | 函数体 / 条件为真 | 抛出 `ModelResponseError('模型响应大小上限必须是正整数')`。 |
| 22 | 函数体 | 将 `get_tool_definitions() if use_tools else []` 赋给 `tools`。 |
| 23 | 函数体 | 条件 `use_tools and include_context`：真时执行body，假时进入else/后续。 |
| 24 | 函数体 / 条件为真 | 在此处导入依赖：`from compaction import maybe_compact`；局部导入可延迟加载或避免循环。 |
| 25 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`maybe_compact(messages, tools)`。 |
| 26 | 函数体 | 将 `prepare_context(messages, tools, include_context)` 赋给 `context`。 |
| 27 | 函数体 | 条件 `context['omitted_messages']`：真时执行body，假时进入else/后续。 |
| 28 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`print('[上下文] 本次省略', context['omitted_messages'], '条历史消息；完整记录仍保存在磁盘')`。 |
| 29 | 函数体 | 将 `{'model': model_config['model'], 'messages': context['messages'], 'stream': stream, 'tools': tools}` 赋给 `data`。 |
| 36 | 函数体 | 将 `model_config.get('provider', 'ollama')` 赋给 `provider`。 |
| 37 | 函数体 | 将 `''` 赋给 `key`。 |
| 38 | 函数体 | 将 `{'Content-Type': 'application/json'}` 赋给 `headers`。 |
| 39 | 函数体 | 将 `model_config['base_url'].rstrip('/')` 赋给 `base`。 |
| 40 | 函数体 | 条件 `provider == 'openai'`：真时执行body，假时进入else/后续。 |
| 41 | 函数体 / 条件为真 | 将 `wire_messages(data['messages'])` 赋给 `data['messages']`。 |
| 42 | 函数体 / 条件为真 | 条件 `not tools`：真时执行body，假时进入else/后续。 |
| 43 | 函数体 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`data.pop('tools')`。 |
| 44 | 函数体 / 条件为真 | 将 `base + '/chat/completions' if base.endswith('/v1') else base + '/v1/chat/completions'` 赋给 `endpoint`。 |
| 45 | 函数体 / 条件为真 | 将 `os.environ.get(model_config.get('api_key_env', 'OPENAI_API_KEY'), '')` 赋给 `key`。 |
| 46 | 函数体 / 条件为真 | 条件 `key`：真时执行body，假时进入else/后续。 |
| 47 | 函数体 / 条件为真 / 条件为真 | 将 `'Bearer ' + key` 赋给 `headers['Authorization']`。 |
| 48 | 函数体 / 条件为假/elif | 条件 `provider == 'ollama'`：真时执行body，假时进入else/后续。 |
| 49 | 函数体 / 条件为假/elif / 条件为真 | 将 `base + '/api/chat'` 赋给 `endpoint`。 |
| 51 | 函数体 / 条件为假/elif / 条件为假/elif | 抛出 `ModelResponseError('未知模型 provider')`。 |
| 52 | 函数体 | 将 `json.dumps(data, ensure_ascii=False).encode('utf-8')` 赋给 `request_body`。 |
| 54 | 函数体 | 将 `urllib.request.Request(url=endpoint, data=request_body, headers=headers, method='POST')` 赋给 `request`。 |
| 61 | 函数体 | 将 `urllib.request.build_opener(NoAuthRedirect()).open if key else urllib.request.urlopen` 赋给 `opener`。 |
| 62 | 函数体 | 进入资源/状态范围：`opener(request, timeout=timeout)` 绑定 `response`；退出执行清理。 |
| 63 | 函数体 / with范围 | 条件 `stream`：真时执行body，假时进入else/后续。 |
| 64 | 函数体 / with范围 / 条件为真 | 返回 `(collect_sse if provider == 'openai' else collect_stream)(response, max_bytes, on_content)`，结束当前函数；具体分支见完整源码。 |
| 65 | 函数体 / with范围 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 66 | 函数体 / with范围 / try | 将 `response.read(max_bytes + 1)` 赋给 `raw`。 |
| 67 | 函数体 / with范围 | except TimeoutError：只处理匹配类型的异常。 |
| 68 | 函数体 / with范围 / except TimeoutError | 抛出 `None`。 |
| 69 | 函数体 / with范围 | except OSError as error：只处理匹配类型的异常。 |
| 70 | 函数体 / with范围 / except OSError as error | 抛出 `ModelResponseError('读取模型响应失败: ' + type(error).__name__)`，异常链关联 `error`。 |
| 71 | 函数体 | 条件 `len(raw) > max_bytes`：真时执行body，假时进入else/后续。 |
| 72 | 函数体 / 条件为真 | 抛出 `ModelResponseError('模型响应超过大小上限')`。 |
| 73 | 函数体 | 将 `parse_json(raw)` 赋给 `result`。 |
| 74 | 函数体 | 条件 `provider == 'openai'`：真时执行body，假时进入else/后续。 |
| 75 | 函数体 / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 76 | 函数体 / 条件为真 / try | 将 `result['choices'][0]` 赋给 `choice`。 |
| 77 | 函数体 / 条件为真 / try | 条件 `choice.get('finish_reason') not in ('stop', 'tool_calls')`：真时执行body，假时进入else/后续。 |
| 78 | 函数体 / 条件为真 / try / 条件为真 | 抛出 `ModelResponseError('API 响应未完整完成')`。 |
| 79 | 函数体 / 条件为真 / try | 将 `normalize(choice['message'])` 赋给 `message`。 |
| 80 | 函数体 / 条件为真 | except (KeyError, IndexError, TypeError) as error：只处理匹配类型的异常。 |
| 81 | 函数体 / 条件为真 / except (KeyError, IndexError, TypeError) as error | 抛出 `ModelResponseError('API 缺少 choices 消息')`，异常链关联 `error`。 |
| 83 | 函数体 / 条件为假/elif | 将 `result.get('message')` 赋给 `message`。 |
| 84 | 函数体 | 计算表达式/调用产生动作：`validate_message(message)`。 |
| 85 | 函数体 | 条件 `on_content is not None and message.get('content')`：真时执行body，假时进入else/后续。 |
| 86 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`on_content(message['content'])`。 |
| 87 | 函数体 | 返回 `message`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L64：`(collect_sse if provider == 'openai' else collect_stream)(response, max_bytes, on_content)`。
- L87：`message`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="generate-reply"></a>
## generate_reply

保留旧文字接口，禁工具请求并复用流式输出。

```python
def generate_reply(messages)
```

位置：[89行](../../../model_client.py#L89) 至快照 97 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `messages` | `未显式注解` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ConsoleOutput`、`message.get`、`output.end`、`request_message`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 92 | `output` | `ConsoleOutput()` | ConsoleOutput对象、缓冲或UI输出接口，具体按签名位置。 |
| 94 | `message` | `request_message(messages, use_tools=False, stream=model_config['stream'], on_content=output.write)` | 单条聊天/协议消息字典；角色和字段随当前分支而定。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 91 | 函数体 | 在此处导入依赖：`from console_output import ConsoleOutput`；局部导入可延迟加载或避免循环。 |
| 92 | 函数体 | 将 `ConsoleOutput()` 赋给 `output`。 |
| 93 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 94 | 函数体 / try | 将 `request_message(messages, use_tools=False, stream=model_config['stream'], on_content=output.write)` 赋给 `message`。 |
| 96 | 函数体 / finally保证清理 | 计算表达式/调用产生动作：`output.end()`。 |
| 97 | 函数体 | 返回 `message.get('content', '')`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L97：`message.get('content', '')`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- class：对象状态与方法/继承：L11。
- with/yield：资源/状态生命周期或逐个生成：L62。
- try/except/finally：异常与保证清理：L65, L75, L93。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | from config import model_config
0002 | from tools import get_tool_definitions
0003 | from context_window import prepare_context
0004 | import json
0005 | import os
0006 | import urllib.request
0007 | from api_adapter import wire_messages, normalize, collect_sse
0008 | from streaming import ModelResponseError, collect_stream, parse_json, validate_message
0009 | 
0010 | 
0011 | class NoAuthRedirect(urllib.request.HTTPRedirectHandler):
0012 |     def redirect_request(self, request, fp, code, msg, headers, newurl):
0013 |         raise ModelResponseError("携带 API 密钥的请求拒绝重定向")
0014 | 
0015 | 
0016 | def request_message(messages, *, use_tools=True, include_context=True, stream=False, on_content=None, timeout=120):
0017 |     if type(timeout) not in (int, float) or not 0 < timeout <= 120:
0018 |         raise ModelResponseError("模型请求超时必须在 0–120 秒之间")
0019 |     max_bytes = model_config.get("max_response_bytes")
0020 |     if type(max_bytes) is not int or max_bytes <= 0:
0021 |         raise ModelResponseError("模型响应大小上限必须是正整数")
0022 |     tools = get_tool_definitions() if use_tools else []
0023 |     if use_tools and include_context:
0024 |         from compaction import maybe_compact
0025 |         maybe_compact(messages, tools)
0026 |     context = prepare_context(messages, tools, include_context)
0027 |     if context["omitted_messages"]:
0028 |         print("[上下文] 本次省略", context["omitted_messages"], "条历史消息；完整记录仍保存在磁盘")
0029 |     data = {
0030 |         "model": model_config["model"],
0031 |         "messages": context["messages"],
0032 |         "stream": stream,
0033 |         "tools": tools
0034 |     }
0035 | 
0036 |     provider = model_config.get('provider', 'ollama')
0037 |     key = ""
0038 |     headers = {'Content-Type': 'application/json'}
0039 |     base = model_config['base_url'].rstrip('/')
0040 |     if provider == 'openai':
0041 |         data['messages'] = wire_messages(data['messages'])
0042 |         if not tools:
0043 |             data.pop('tools')
0044 |         endpoint = base + '/chat/completions' if base.endswith('/v1') else base + '/v1/chat/completions'
0045 |         key = os.environ.get(model_config.get('api_key_env', 'OPENAI_API_KEY'), '')
0046 |         if key:
0047 |             headers['Authorization'] = 'Bearer ' + key
0048 |     elif provider == 'ollama':
0049 |         endpoint = base + '/api/chat'
0050 |     else:
0051 |         raise ModelResponseError('未知模型 provider')
0052 |     request_body = json.dumps(data, ensure_ascii=False).encode("utf-8")
0053 | 
0054 |     request = urllib.request.Request(
0055 |         url=endpoint,
0056 |         data=request_body,
0057 |         headers=headers,
0058 |         method="POST"
0059 |     )
0060 | 
0061 |     opener = urllib.request.build_opener(NoAuthRedirect()).open if key else urllib.request.urlopen
0062 |     with opener(request, timeout=timeout) as response:
0063 |         if stream:
0064 |             return (collect_sse if provider == "openai" else collect_stream)(response, max_bytes, on_content)
0065 |         try:
0066 |             raw = response.read(max_bytes + 1)
0067 |         except TimeoutError:
0068 |             raise
0069 |         except OSError as error:
0070 |             raise ModelResponseError("读取模型响应失败: " + type(error).__name__) from error
0071 |     if len(raw) > max_bytes:
0072 |         raise ModelResponseError("模型响应超过大小上限")
0073 |     result = parse_json(raw)
0074 |     if provider == 'openai':
0075 |         try:
0076 |             choice = result['choices'][0]
0077 |             if choice.get('finish_reason') not in ('stop', 'tool_calls'):
0078 |                 raise ModelResponseError('API 响应未完整完成')
0079 |             message = normalize(choice['message'])
0080 |         except (KeyError, IndexError, TypeError) as error:
0081 |             raise ModelResponseError('API 缺少 choices 消息') from error
0082 |     else:
0083 |         message = result.get("message")
0084 |     validate_message(message)
0085 |     if on_content is not None and message.get("content"):
0086 |         on_content(message["content"])
0087 |     return message
0088 | 
0089 | def generate_reply(messages):
0090 |     # 保留旧接口，复用同一个请求实现，不再维护两套流式解析。
0091 |     from console_output import ConsoleOutput
0092 |     output = ConsoleOutput()
0093 |     try:
0094 |         message = request_message(messages, use_tools=False, stream=model_config['stream'], on_content=output.write)
0095 |     finally:
0096 |         output.end()
0097 |     return message.get('content', '')
```
