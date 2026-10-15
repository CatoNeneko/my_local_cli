# streaming.py：源码导读

Ollama逐行JSON收集；完整done之前不返回可执行工具请求。

先读专题：[02-agent.md](../02-agent.md)。

实际源码：[streaming.py](../../../streaming.py)。

快照 SHA256：`cb1d7e1e4afb0757e69f90c3a0a2047353d6fe54104ee576aef502ea055a86c3`；77 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [parse_json](#parse-json) | [9](../../../streaming.py#L9) | 从UTF-8字节解析JSON对象，拒绝服务error和非法结构。 |
| [validate_message](#validate-message) | [21](../../../streaming.py#L21) | 检查模型消息、文本字段和工具调用结构，格式坏则抛专用异常。 |
| [collect_stream](#collect-stream) | [40](../../../streaming.py#L40) | 收集Ollama NDJSON，累计文字/思考/调用，等done。 |

<a id="parse-json"></a>
## parse_json

从UTF-8字节解析JSON对象，拒绝服务error和非法结构。

```python
def parse_json(raw)
```

位置：[9行](../../../streaming.py#L9) 至快照 18 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `raw` | `未显式注解` | 未解码字节/完整输出快照，按编码与限额再处理。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ModelResponseError`、`isinstance`、`json.loads`、`raw.decode`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 11 | `value` | `json.loads(raw.decode('utf-8'))` | 正在检查的通用值；其实际类型以赋值与后续校验为准。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 10 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 11 | 函数体 / try | 将 `json.loads(raw.decode('utf-8'))` 赋给 `value`。 |
| 12 | 函数体 | except (UnicodeError, json.JSONDecodeError) as error：只处理匹配类型的异常。 |
| 13 | 函数体 / except (UnicodeError, json.JSONDecodeError) as error | 抛出 `ModelResponseError('模型响应不是有效的 UTF-8 JSON')`，异常链关联 `error`。 |
| 14 | 函数体 | 条件 `not isinstance(value, dict)`：真时执行body，假时进入else/后续。 |
| 15 | 函数体 / 条件为真 | 抛出 `ModelResponseError('模型响应必须是字典')`。 |
| 16 | 函数体 | 条件 `'error' in value`：真时执行body，假时进入else/后续。 |
| 17 | 函数体 / 条件为真 | 抛出 `ModelResponseError('模型服务报告错误: ' + str(value['error'])[:500])`。 |
| 18 | 函数体 | 返回 `value`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L18：`value`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="validate-message"></a>
## validate_message

检查模型消息、文本字段和工具调用结构，格式坏则抛专用异常。

```python
def validate_message(message)
```

位置：[21行](../../../streaming.py#L21) 至快照 37 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `message` | `未显式注解` | 单条聊天/协议消息字典；角色和字段随当前分支而定。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ModelResponseError`、`call.get`、`function.get`、`isinstance`、`message.get`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 27 | `calls` | `message.get('tool_calls', [])` | 工具调用计数或按index缓存的调用集合；来源表达式决定类型。 |
| 31 | `function` | `call.get('function') if isinstance(call, dict) else None` | 模型工具调用的function子字典，含name和arguments。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 22 | 函数体 | 条件 `not isinstance(message, dict)`：真时执行body，假时进入else/后续。 |
| 23 | 函数体 / 条件为真 | 抛出 `ModelResponseError('message 必须是字典')`。 |
| 24 | 函数体 | 遍历 `('content', 'thinking')`，每次绑定 `field`。 |
| 25 | 函数体 / 循环每次 | 条件 `not isinstance(message.get(field, ''), str)`：真时执行body，假时进入else/后续。 |
| 26 | 函数体 / 循环每次 / 条件为真 | 抛出 `ModelResponseError(field + ' 必须是字符串')`。 |
| 27 | 函数体 | 将 `message.get('tool_calls', [])` 赋给 `calls`。 |
| 28 | 函数体 | 条件 `not isinstance(calls, list)`：真时执行body，假时进入else/后续。 |
| 29 | 函数体 / 条件为真 | 抛出 `ModelResponseError('tool_calls 必须是列表')`。 |
| 30 | 函数体 | 遍历 `calls`，每次绑定 `call`。 |
| 31 | 函数体 / 循环每次 | 将 `call.get('function') if isinstance(call, dict) else None` 赋给 `function`。 |
| 32 | 函数体 / 循环每次 | 条件 `not isinstance(function, dict)`：真时执行body，假时进入else/后续。 |
| 33 | 函数体 / 循环每次 / 条件为真 | 抛出 `ModelResponseError('工具调用缺少 function')`。 |
| 34 | 函数体 / 循环每次 | 条件 `not isinstance(function.get('name'), str) or not function['name']`：真时执行body，假时进入else/后续。 |
| 35 | 函数体 / 循环每次 / 条件为真 | 抛出 `ModelResponseError('工具名称必须是非空字符串')`。 |
| 36 | 函数体 / 循环每次 | 条件 `not isinstance(function.get('arguments', {}), dict)`：真时执行body，假时进入else/后续。 |
| 37 | 函数体 / 循环每次 / 条件为真 | 抛出 `ModelResponseError('Ollama 工具参数必须是完整字典')`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="collect-stream"></a>
## collect_stream

收集Ollama NDJSON，累计文字/思考/调用，等done。

```python
def collect_stream(response, max_bytes, on_content=None)
```

位置：[40行](../../../streaming.py#L40) 至快照 77 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `response` | `未显式注解` | HTTP响应流或异步请求Future，依当前模块。 |
| `max_bytes` | `未显式注解` | 模型响应捕获字节上限。 |
| `on_content` | `未显式注解` | 收到流式文字时调用的函数引用，None表示不回调。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ModelResponseError`、`call['function'].get`、`chunk.get`、`len`、`line.strip`、`message.get`、`message['tool_calls'].append`、`on_content`、`parse_json`、`part.get`、`response.readline`、`seen_indices.add`、`set`、`type`、`validate_message`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 41 | `message` | `{'role': 'assistant', 'content': '', 'tool_calls': []}` | 单条聊天/协议消息字典；角色和字段随当前分支而定。 |
| 42 | `received_bytes` | `0` | 模型响应已接收字节计数。 |
| 43 | `seen_indices` | `set()` | Ollama工具索引去重集合，拒绝重复/非法索引。 |
| 46 | `line` | `response.readline(max_bytes - received_bytes + 1)` | 当前行文字或网络逐行数据。 |
| 58 | `chunk` | `parse_json(line)` | 本次读取的输出字节或流式JSON块。 |
| 59 | `part` | `chunk.get('message', {})` | 流式消息/工具参数的一个片段。 |
| 64 | `index` | `call['function'].get('index')` | 0起始位置或协议工具片段index。 |
| 70 | `content` | `part.get('content', '')` | 文件正文、消息文字或累计响应；看role与来源。 |
| 73 | `message['thinking']` | `message.get('thinking', '') + part['thinking']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 41 | 函数体 | 将 `{'role': 'assistant', 'content': '', 'tool_calls': []}` 赋给 `message`。 |
| 42 | 函数体 | 将 `0` 赋给 `received_bytes`。 |
| 43 | 函数体 | 将 `set()` 赋给 `seen_indices`。 |
| 44 | 函数体 | 循环检查 `True`，break/return/异常可结束。 |
| 45 | 函数体 / 循环每次 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 46 | 函数体 / 循环每次 / try | 将 `response.readline(max_bytes - received_bytes + 1)` 赋给 `line`。 |
| 47 | 函数体 / 循环每次 | except TimeoutError：只处理匹配类型的异常。 |
| 48 | 函数体 / 循环每次 / except TimeoutError | 抛出 `None`。 |
| 49 | 函数体 / 循环每次 | except OSError as error：只处理匹配类型的异常。 |
| 50 | 函数体 / 循环每次 / except OSError as error | 抛出 `ModelResponseError('流式读取失败: ' + type(error).__name__)`，异常链关联 `error`。 |
| 51 | 函数体 / 循环每次 | 条件 `not line`：真时执行body，假时进入else/后续。 |
| 52 | 函数体 / 循环每次 / 条件为真 | 抛出 `ModelResponseError('流式响应提前结束，未收到 done 标记；本次未完成响应中的工具调用未执行')`。 |
| 53 | 函数体 / 循环每次 | 更新已有变量：`received_bytes += len(line)`。 |
| 54 | 函数体 / 循环每次 | 条件 `received_bytes > max_bytes`：真时执行body，假时进入else/后续。 |
| 55 | 函数体 / 循环每次 / 条件为真 | 抛出 `ModelResponseError('模型响应超过大小上限')`。 |
| 56 | 函数体 / 循环每次 | 条件 `not line.strip()`：真时执行body，假时进入else/后续。 |
| 57 | 函数体 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 58 | 函数体 / 循环每次 | 将 `parse_json(line)` 赋给 `chunk`。 |
| 59 | 函数体 / 循环每次 | 将 `chunk.get('message', {})` 赋给 `part`。 |
| 60 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`validate_message(part)`。 |
| 61 | 函数体 / 循环每次 | 条件 `type(chunk.get('done')) is not bool`：真时执行body，假时进入else/后续。 |
| 62 | 函数体 / 循环每次 / 条件为真 | 抛出 `ModelResponseError('流式响应缺少布尔类型 done 标记')`。 |
| 63 | 函数体 / 循环每次 | 遍历 `part.get('tool_calls', [])`，每次绑定 `call`。 |
| 64 | 函数体 / 循环每次 / 循环每次 | 将 `call['function'].get('index')` 赋给 `index`。 |
| 65 | 函数体 / 循环每次 / 循环每次 | 条件 `index is not None`：真时执行body，假时进入else/后续。 |
| 66 | 函数体 / 循环每次 / 循环每次 / 条件为真 | 条件 `type(index) is not int or index < 0 or index in seen_indices`：真时执行body，假时进入else/后续。 |
| 67 | 函数体 / 循环每次 / 循环每次 / 条件为真 / 条件为真 | 抛出 `ModelResponseError('流式工具调用 index 无效或重复')`。 |
| 68 | 函数体 / 循环每次 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`seen_indices.add(index)`。 |
| 69 | 函数体 / 循环每次 / 循环每次 | 计算表达式/调用产生动作：`message['tool_calls'].append(call)`。 |
| 70 | 函数体 / 循环每次 | 将 `part.get('content', '')` 赋给 `content`。 |
| 71 | 函数体 / 循环每次 | 更新已有变量：`message['content'] += content`。 |
| 72 | 函数体 / 循环每次 | 条件 `part.get('thinking')`：真时执行body，假时进入else/后续。 |
| 73 | 函数体 / 循环每次 / 条件为真 | 将 `message.get('thinking', '') + part['thinking']` 赋给 `message['thinking']`。 |
| 74 | 函数体 / 循环每次 | 条件 `content and on_content is not None`：真时执行body，假时进入else/后续。 |
| 75 | 函数体 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`on_content(content)`。 |
| 76 | 函数体 / 循环每次 | 条件 `chunk['done']`：真时执行body，假时进入else/后续。 |
| 77 | 函数体 / 循环每次 / 条件为真 | 返回 `message`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L77：`message`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- class：对象状态与方法/继承：L5。
- try/except/finally：异常与保证清理：L10, L45。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """Ollama NDJSON 响应收集；结束标记到达前不返回可执行工具调用。"""
0002 | import json
0003 | 
0004 | 
0005 | class ModelResponseError(ValueError):
0006 |     pass
0007 | 
0008 | 
0009 | def parse_json(raw):
0010 |     try:
0011 |         value = json.loads(raw.decode("utf-8"))
0012 |     except (UnicodeError, json.JSONDecodeError) as error:
0013 |         raise ModelResponseError("模型响应不是有效的 UTF-8 JSON") from error
0014 |     if not isinstance(value, dict):
0015 |         raise ModelResponseError("模型响应必须是字典")
0016 |     if "error" in value:
0017 |         raise ModelResponseError("模型服务报告错误: " + str(value["error"])[:500])
0018 |     return value
0019 | 
0020 | 
0021 | def validate_message(message):
0022 |     if not isinstance(message, dict):
0023 |         raise ModelResponseError("message 必须是字典")
0024 |     for field in ("content", "thinking"):
0025 |         if not isinstance(message.get(field, ""), str):
0026 |             raise ModelResponseError(field + " 必须是字符串")
0027 |     calls = message.get("tool_calls", [])
0028 |     if not isinstance(calls, list):
0029 |         raise ModelResponseError("tool_calls 必须是列表")
0030 |     for call in calls:
0031 |         function = call.get("function") if isinstance(call, dict) else None
0032 |         if not isinstance(function, dict):
0033 |             raise ModelResponseError("工具调用缺少 function")
0034 |         if not isinstance(function.get("name"), str) or not function["name"]:
0035 |             raise ModelResponseError("工具名称必须是非空字符串")
0036 |         if not isinstance(function.get("arguments", {}), dict):
0037 |             raise ModelResponseError("Ollama 工具参数必须是完整字典")
0038 | 
0039 | 
0040 | def collect_stream(response, max_bytes, on_content=None):
0041 |     message = {"role": "assistant", "content": "", "tool_calls": []}
0042 |     received_bytes = 0
0043 |     seen_indices = set()
0044 |     while True:
0045 |         try:
0046 |             line = response.readline(max_bytes - received_bytes + 1)
0047 |         except TimeoutError:
0048 |             raise
0049 |         except OSError as error:
0050 |             raise ModelResponseError("流式读取失败: " + type(error).__name__) from error
0051 |         if not line:
0052 |             raise ModelResponseError("流式响应提前结束，未收到 done 标记；本次未完成响应中的工具调用未执行")
0053 |         received_bytes += len(line)
0054 |         if received_bytes > max_bytes:
0055 |             raise ModelResponseError("模型响应超过大小上限")
0056 |         if not line.strip():
0057 |             continue
0058 |         chunk = parse_json(line)
0059 |         part = chunk.get("message", {})
0060 |         validate_message(part)
0061 |         if type(chunk.get("done")) is not bool:
0062 |             raise ModelResponseError("流式响应缺少布尔类型 done 标记")
0063 |         for call in part.get("tool_calls", []):
0064 |             index = call["function"].get("index")
0065 |             if index is not None:
0066 |                 if type(index) is not int or index < 0 or index in seen_indices:
0067 |                     raise ModelResponseError("流式工具调用 index 无效或重复")
0068 |                 seen_indices.add(index)
0069 |             message["tool_calls"].append(call)
0070 |         content = part.get("content", "")
0071 |         message["content"] += content
0072 |         if part.get("thinking"):
0073 |             message["thinking"] = message.get("thinking", "") + part["thinking"]
0074 |         if content and on_content is not None:
0075 |             on_content(content)
0076 |         if chunk["done"]:
0077 |             return message
```
