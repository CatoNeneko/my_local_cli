# api_adapter.py：源码导读

把内部字典消息转换成兼容Chat Completions格式，再将非流式/SSE结果统一回来。

先读专题：[02-agent.md](../02-agent.md)。

实际源码：[api_adapter.py](../../../api_adapter.py)。

快照 SHA256：`41e127f2ef0fb07f2b666a0264015ca83160fddf0ce28a1cdd39e76aaf471c91`；115 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `from streaming import ModelResponseError, validate_message` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [wire_messages](#wire-messages) | [6](../../../api_adapter.py#L6) | 把内部消息转换为API格式，序列化工具参数并配对调用ID。 |
| [normalize](#normalize) | [33](../../../api_adapter.py#L33) | 把API工具参数字符串解析为内部字典，检查消息和调用ID。 |
| [collect_sse](#collect-sse) | [55](../../../api_adapter.py#L55) | 拼接SSE事件、文字与工具片段，只在完整完成标记后返回。 |

<a id="wire-messages"></a>
## wire_messages

把内部消息转换为API格式，序列化工具参数并配对调用ID。

```python
def wire_messages(messages)
```

位置：[6行](../../../api_adapter.py#L6) 至快照 30 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `messages` | `未显式注解` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ModelResponseError`、`call.get`、`enumerate`、`function.get`、`isinstance`、`item['tool_calls'].append`、`json.dumps`、`message.get`、`pending.append`、`pending.pop`、`result.append`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 7 | `(result, pending)` | `([], [])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 9 | `role` | `message['role']` | 消息身份字段，决定user/assistant/tool/system的协议解释。 |
| 10 | `item` | `{'role': role, 'content': message.get('content', '')}` | 遍历中的一项：字段、文件、消息或工具定义，类型取决于iter。 |
| 12 | `pending` | `[]` | 等待配对的工具结果/ID队列，或临时注册项映射。 |
| 13 | `item['tool_calls']` | `[]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 15 | `identifier` | `call.get('id') or f'call_{number}_{index}'` | 随机task_id、调用ID或建议ID；不同协议层用途不同。 |
| 19 | `function` | `call['function']` | 模型工具调用的function子字典，含name和arguments。 |
| 25 | `identifier` | `pending.pop(0)` | 随机task_id、调用ID或建议ID；不同协议层用途不同。 |
| 28 | `item['tool_call_id']` | `identifier` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 7 | 函数体 | 将 `([], [])` 赋给 `(result, pending)`。 |
| 8 | 函数体 | 遍历 `enumerate(messages)`，每次绑定 `(number, message)`。 |
| 9 | 函数体 / 循环每次 | 将 `message['role']` 赋给 `role`。 |
| 10 | 函数体 / 循环每次 | 将 `{'role': role, 'content': message.get('content', '')}` 赋给 `item`。 |
| 11 | 函数体 / 循环每次 | 条件 `role == 'assistant' and message.get('tool_calls')`：真时执行body，假时进入else/后续。 |
| 12 | 函数体 / 循环每次 / 条件为真 | 将 `[]` 赋给 `pending`。 |
| 13 | 函数体 / 循环每次 / 条件为真 | 将 `[]` 赋给 `item['tool_calls']`。 |
| 14 | 函数体 / 循环每次 / 条件为真 | 遍历 `enumerate(message['tool_calls'])`，每次绑定 `(index, call)`。 |
| 15 | 函数体 / 循环每次 / 条件为真 / 循环每次 | 将 `call.get('id') or f'call_{number}_{index}'` 赋给 `identifier`。 |
| 16 | 函数体 / 循环每次 / 条件为真 / 循环每次 | 条件 `not isinstance(identifier, str) or not identifier or identifier in pending`：真时执行body，假时进入else/后续。 |
| 17 | 函数体 / 循环每次 / 条件为真 / 循环每次 / 条件为真 | 抛出 `ModelResponseError('工具调用 ID 无效或重复')`。 |
| 18 | 函数体 / 循环每次 / 条件为真 / 循环每次 | 计算表达式/调用产生动作：`pending.append(identifier)`。 |
| 19 | 函数体 / 循环每次 / 条件为真 / 循环每次 | 将 `call['function']` 赋给 `function`。 |
| 20 | 函数体 / 循环每次 / 条件为真 / 循环每次 | 计算表达式/调用产生动作：`item['tool_calls'].append({'id': identifier, 'type': 'function', 'function': {'name': function['name'], 'arguments': json.dumps(function.get('arguments', {}), ensure_asci…（见完整源码）`。 |
| 22 | 函数体 / 循环每次 / 条件为假/elif | 条件 `role == 'tool'`：真时执行body，假时进入else/后续。 |
| 23 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 | 条件 `not pending`：真时执行body，假时进入else/后续。 |
| 24 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 / 条件为真 | 抛出 `ModelResponseError('工具结果没有对应调用')`。 |
| 25 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 | 将 `pending.pop(0)` 赋给 `identifier`。 |
| 26 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 | 条件 `message.get('tool_call_id', identifier) != identifier`：真时执行body，假时进入else/后续。 |
| 27 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 / 条件为真 | 抛出 `ModelResponseError('工具结果 ID 不匹配')`。 |
| 28 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 | 将 `identifier` 赋给 `item['tool_call_id']`。 |
| 29 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`result.append(item)`。 |
| 30 | 函数体 | 返回 `result`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L30：`result`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="normalize"></a>
## normalize

把API工具参数字符串解析为内部字典，检查消息和调用ID。

```python
def normalize(message)
```

位置：[33行](../../../api_adapter.py#L33) 至快照 52 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `message` | `未显式注解` | 单条聊天/协议消息字典；角色和字段随当前分支而定。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ModelResponseError`、`ValueError`、`isinstance`、`json.loads`、`len`、`message.get`、`result['tool_calls'].append`、`set`、`validate_message`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 36 | `result` | `{'role': 'assistant', 'content': '' if message.get('content') is None else message.get('content'), 'tool_calls': []}` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 39 | `function` | `call['function']` | 模型工具调用的function子字典，含name和arguments。 |
| 40 | `arguments` | `json.loads(function['arguments'])` | 外部或模型提交的工具参数，必须经schema检查。 |
| 41 | `identifier` | `call['id']` | 随机task_id、调用ID或建议ID；不同协议层用途不同。 |
| 49 | `identifiers` | `[call['id'] for call in result['tool_calls']]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 34 | 函数体 | 条件 `not isinstance(message, dict)`：真时执行body，假时进入else/后续。 |
| 35 | 函数体 / 条件为真 | 抛出 `ModelResponseError('API 缺少消息')`。 |
| 36 | 函数体 | 将 `{'role': 'assistant', 'content': '' if message.get('content') is None else message.get('content'), 'tool_calls': []}` 赋给 `result`。 |
| 37 | 函数体 | 遍历 `message.get('tool_calls') or []`，每次绑定 `call`。 |
| 38 | 函数体 / 循环每次 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 39 | 函数体 / 循环每次 / try | 将 `call['function']` 赋给 `function`。 |
| 40 | 函数体 / 循环每次 / try | 将 `json.loads(function['arguments'])` 赋给 `arguments`。 |
| 41 | 函数体 / 循环每次 / try | 将 `call['id']` 赋给 `identifier`。 |
| 42 | 函数体 / 循环每次 / try | 条件 `not isinstance(identifier, str) or not identifier`：真时执行body，假时进入else/后续。 |
| 43 | 函数体 / 循环每次 / try / 条件为真 | 抛出 `ValueError()`。 |
| 44 | 函数体 / 循环每次 / try | 计算表达式/调用产生动作：`result['tool_calls'].append({'id': identifier, 'type': 'function', 'function': {'name': function['name'], 'arguments': arguments}})`。 |
| 46 | 函数体 / 循环每次 | except (KeyError, TypeError, ValueError) as error：只处理匹配类型的异常。 |
| 47 | 函数体 / 循环每次 / except (KeyError, TypeError, ValueError) as error | 抛出 `ModelResponseError('API 工具调用格式错误')`，异常链关联 `error`。 |
| 48 | 函数体 | 计算表达式/调用产生动作：`validate_message(result)`。 |
| 49 | 函数体 | 将 `[call['id'] for call in result['tool_calls']]` 赋给 `identifiers`。 |
| 50 | 函数体 | 条件 `len(set(identifiers)) != len(identifiers)`：真时执行body，假时进入else/后续。 |
| 51 | 函数体 / 条件为真 | 抛出 `ModelResponseError('API 工具 ID 重复')`。 |
| 52 | 函数体 | 返回 `result`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L52：`result`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="collect-sse"></a>
## collect_sse

拼接SSE事件、文字与工具片段，只在完整完成标记后返回。

```python
def collect_sse(response, max_bytes, on_content=None)
```

位置：[55行](../../../api_adapter.py#L55) 至快照 115 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `response` | `未显式注解` | HTTP响应流或异步请求Future，依当前模块。 |
| `max_bytes` | `未显式注解` | 模型响应捕获字节上限。 |
| `on_content` | `未显式注解` | 收到流式文字时调用的函数引用，None表示不回调。 |

**调用表达式（静态提取，不含内层独立函数体）**：`'\n'.join`、`ModelResponseError`、`ValueError`、`calls.setdefault`、`choice.get`、`chunk.get`、`delta.get`、`event.append`、`isinstance`、`json.loads`、`len`、`line.decode`、`line.decode('utf-8').rstrip`、`line.startswith`、`line[5:].lstrip`、`normalize`、`on_content`、`part.get`、`part.get('function', {}).get`、`response.readline`、`sorted`、`str`、`type`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 56 | `(total, content, calls, event)` | `(0, '', {}, [])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 57 | `finished` | `False` | 兼容API已收到合法完成原因；后续异常片段不接受。 |
| 59 | `line` | `response.readline(max_bytes - total + 1)` | 当前行文字或网络逐行数据。 |
| 66 | `line` | `line.decode('utf-8').rstrip('\r\n')` | 当前行文字或网络逐行数据。 |
| 73 | `data` | `'\n'.join(event)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 74 | `event` | `[]` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |
| 80 | `chunk` | `json.loads(data)` | 本次读取的输出字节或流式JSON块。 |
| 83 | `choices` | `chunk.get('choices', [])` | 选择面板的(value,label)列表。 |
| 86 | `choice` | `choices[0]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 89 | `delta` | `choice.get('delta', {})` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 90 | `text` | `delta.get('content') or ''` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 97 | `index` | `part['index']` | 0起始位置或协议工具片段index。 |
| 100 | `target` | `calls.setdefault(index, {'id': '', 'function': {'name': '', 'arguments': ''}})` | 已选定的文件/目录或操作目标，提交前可能需要再次验证。 |
| 104 | `target['id']` | `part['id']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 107 | `reason` | `choice.get('finish_reason')` | 明确终止/审批/截断原因，不根据正文措辞推断。 |
| 111 | `finished` | `True` | 兼容API已收到合法完成原因；后续异常片段不接受。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 56 | 函数体 | 将 `(0, '', {}, [])` 赋给 `(total, content, calls, event)`。 |
| 57 | 函数体 | 将 `False` 赋给 `finished`。 |
| 58 | 函数体 | 循环检查 `True`，break/return/异常可结束。 |
| 59 | 函数体 / 循环每次 | 将 `response.readline(max_bytes - total + 1)` 赋给 `line`。 |
| 60 | 函数体 / 循环每次 | 更新已有变量：`total += len(line)`。 |
| 61 | 函数体 / 循环每次 | 条件 `total > max_bytes`：真时执行body，假时进入else/后续。 |
| 62 | 函数体 / 循环每次 / 条件为真 | 抛出 `ModelResponseError('模型响应超过大小上限')`。 |
| 63 | 函数体 / 循环每次 | 条件 `not line`：真时执行body，假时进入else/后续。 |
| 64 | 函数体 / 循环每次 / 条件为真 | 抛出 `ModelResponseError('API 流提前结束，工具未执行')`。 |
| 65 | 函数体 / 循环每次 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 66 | 函数体 / 循环每次 / try | 将 `line.decode('utf-8').rstrip('\r\n')` 赋给 `line`。 |
| 67 | 函数体 / 循环每次 | except UnicodeError as error：只处理匹配类型的异常。 |
| 68 | 函数体 / 循环每次 / except UnicodeError as error | 抛出 `ModelResponseError('API 流编码错误')`，异常链关联 `error`。 |
| 69 | 函数体 / 循环每次 | 条件 `line.startswith('data:')`：真时执行body，假时进入else/后续。 |
| 70 | 函数体 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`event.append(line[5:].lstrip(' '))`。 |
| 71 | 函数体 / 循环每次 | 条件 `line or not event`：真时执行body，假时进入else/后续。 |
| 72 | 函数体 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 73 | 函数体 / 循环每次 | 将 `'\n'.join(event)` 赋给 `data`。 |
| 74 | 函数体 / 循环每次 | 将 `[]` 赋给 `event`。 |
| 75 | 函数体 / 循环每次 | 条件 `data == '[DONE]'`：真时执行body，假时进入else/后续。 |
| 76 | 函数体 / 循环每次 / 条件为真 | 条件 `not finished`：真时执行body，假时进入else/后续。 |
| 77 | 函数体 / 循环每次 / 条件为真 / 条件为真 | 抛出 `ModelResponseError('API 流缺少完成原因')`。 |
| 78 | 函数体 / 循环每次 / 条件为真 | 返回 `normalize({'content': content, 'tool_calls': [calls[key] for key in sorted(calls)]})`，结束当前函数；具体分支见完整源码。 |
| 79 | 函数体 / 循环每次 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 80 | 函数体 / 循环每次 / try | 将 `json.loads(data)` 赋给 `chunk`。 |
| 81 | 函数体 / 循环每次 / try | 条件 `'error' in chunk`：真时执行body，假时进入else/后续。 |
| 82 | 函数体 / 循环每次 / try / 条件为真 | 抛出 `ValueError()`。 |
| 83 | 函数体 / 循环每次 / try | 将 `chunk.get('choices', [])` 赋给 `choices`。 |
| 84 | 函数体 / 循环每次 / try | 条件 `not choices`：真时执行body，假时进入else/后续。 |
| 85 | 函数体 / 循环每次 / try / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 86 | 函数体 / 循环每次 / try | 将 `choices[0]` 赋给 `choice`。 |
| 87 | 函数体 / 循环每次 / try | 条件 `finished`：真时执行body，假时进入else/后续。 |
| 88 | 函数体 / 循环每次 / try / 条件为真 | 抛出 `ValueError()`。 |
| 89 | 函数体 / 循环每次 / try | 将 `choice.get('delta', {})` 赋给 `delta`。 |
| 90 | 函数体 / 循环每次 / try | 将 `delta.get('content') or ''` 赋给 `text`。 |
| 91 | 函数体 / 循环每次 / try | 条件 `not isinstance(text, str)`：真时执行body，假时进入else/后续。 |
| 92 | 函数体 / 循环每次 / try / 条件为真 | 抛出 `ValueError()`。 |
| 93 | 函数体 / 循环每次 / try | 更新已有变量：`content += text`。 |
| 94 | 函数体 / 循环每次 / try | 条件 `text and on_content`：真时执行body，假时进入else/后续。 |
| 95 | 函数体 / 循环每次 / try / 条件为真 | 计算表达式/调用产生动作：`on_content(text)`。 |
| 96 | 函数体 / 循环每次 / try | 遍历 `delta.get('tool_calls') or []`，每次绑定 `part`。 |
| 97 | 函数体 / 循环每次 / try / 循环每次 | 将 `part['index']` 赋给 `index`。 |
| 98 | 函数体 / 循环每次 / try / 循环每次 | 条件 `type(index) is not int or not 0 <= index < 64`：真时执行body，假时进入else/后续。 |
| 99 | 函数体 / 循环每次 / try / 循环每次 / 条件为真 | 抛出 `ValueError()`。 |
| 100 | 函数体 / 循环每次 / try / 循环每次 | 将 `calls.setdefault(index, {'id': '', 'function': {'name': '', 'arguments': ''}})` 赋给 `target`。 |
| 101 | 函数体 / 循环每次 / try / 循环每次 | 条件 `part.get('id')`：真时执行body，假时进入else/后续。 |
| 102 | 函数体 / 循环每次 / try / 循环每次 / 条件为真 | 条件 `target['id'] and target['id'] != part['id']`：真时执行body，假时进入else/后续。 |
| 103 | 函数体 / 循环每次 / try / 循环每次 / 条件为真 / 条件为真 | 抛出 `ValueError()`。 |
| 104 | 函数体 / 循环每次 / try / 循环每次 / 条件为真 | 将 `part['id']` 赋给 `target['id']`。 |
| 105 | 函数体 / 循环每次 / try / 循环每次 | 遍历 `('name', 'arguments')`，每次绑定 `field`。 |
| 106 | 函数体 / 循环每次 / try / 循环每次 / 循环每次 | 更新已有变量：`target['function'][field] += part.get('function', {}).get(field, '')`。 |
| 107 | 函数体 / 循环每次 / try | 将 `choice.get('finish_reason')` 赋给 `reason`。 |
| 108 | 函数体 / 循环每次 / try | 条件 `reason is not None`：真时执行body，假时进入else/后续。 |
| 109 | 函数体 / 循环每次 / try / 条件为真 | 条件 `reason not in ('stop', 'tool_calls')`：真时执行body，假时进入else/后续。 |
| 110 | 函数体 / 循环每次 / try / 条件为真 / 条件为真 | 抛出 `ModelResponseError('API 响应未完整完成: ' + str(reason))`。 |
| 111 | 函数体 / 循环每次 / try / 条件为真 | 将 `True` 赋给 `finished`。 |
| 112 | 函数体 / 循环每次 | except (ValueError, KeyError, TypeError, AttributeError) as error：只处理匹配类型的异常。 |
| 113 | 函数体 / 循环每次 / except (ValueError, KeyError, TypeError, AttributeError) as error | 条件 `isinstance(error, ModelResponseError)`：真时执行body，假时进入else/后续。 |
| 114 | 函数体 / 循环每次 / except (ValueError, KeyError, TypeError, AttributeError) as error / 条件为真 | 抛出 `None`。 |
| 115 | 函数体 / 循环每次 / except (ValueError, KeyError, TypeError, AttributeError) as error | 抛出 `ModelResponseError('API SSE 数据格式错误')`，异常链关联 `error`。 |

**实际返回分支**：

- L78：`normalize({'content': content, 'tool_calls': [calls[key] for key in sorted(calls)]})`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L38, L65, L79。
- 推导式/生成器表达式：循环建容器或逐个产生：L49, L78。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """OpenAI 兼容 Chat Completions；内部消息仍统一使用字典参数。"""
0002 | import json
0003 | from streaming import ModelResponseError, validate_message
0004 | 
0005 | 
0006 | def wire_messages(messages):
0007 |     result, pending = [], []
0008 |     for number, message in enumerate(messages):
0009 |         role = message['role']
0010 |         item = {'role': role, 'content': message.get('content', '')}
0011 |         if role == 'assistant' and message.get('tool_calls'):
0012 |             pending = []
0013 |             item['tool_calls'] = []
0014 |             for index, call in enumerate(message['tool_calls']):
0015 |                 identifier = call.get('id') or f'call_{number}_{index}'
0016 |                 if not isinstance(identifier, str) or not identifier or identifier in pending:
0017 |                     raise ModelResponseError('工具调用 ID 无效或重复')
0018 |                 pending.append(identifier)
0019 |                 function = call['function']
0020 |                 item['tool_calls'].append({'id': identifier, 'type': 'function', 'function': {
0021 |                     'name': function['name'], 'arguments': json.dumps(function.get('arguments', {}), ensure_ascii=False)}})
0022 |         elif role == 'tool':
0023 |             if not pending:
0024 |                 raise ModelResponseError('工具结果没有对应调用')
0025 |             identifier = pending.pop(0)
0026 |             if message.get('tool_call_id', identifier) != identifier:
0027 |                 raise ModelResponseError('工具结果 ID 不匹配')
0028 |             item['tool_call_id'] = identifier
0029 |         result.append(item)
0030 |     return result
0031 | 
0032 | 
0033 | def normalize(message):
0034 |     if not isinstance(message, dict):
0035 |         raise ModelResponseError('API 缺少消息')
0036 |     result = {'role': 'assistant', 'content': '' if message.get('content') is None else message.get('content'), 'tool_calls': []}
0037 |     for call in message.get('tool_calls') or []:
0038 |         try:
0039 |             function = call['function']
0040 |             arguments = json.loads(function['arguments'])
0041 |             identifier = call['id']
0042 |             if not isinstance(identifier, str) or not identifier:
0043 |                 raise ValueError()
0044 |             result['tool_calls'].append({'id': identifier, 'type': 'function', 'function': {
0045 |                 'name': function['name'], 'arguments': arguments}})
0046 |         except (KeyError, TypeError, ValueError) as error:
0047 |             raise ModelResponseError('API 工具调用格式错误') from error
0048 |     validate_message(result)
0049 |     identifiers = [call['id'] for call in result['tool_calls']]
0050 |     if len(set(identifiers)) != len(identifiers):
0051 |         raise ModelResponseError('API 工具 ID 重复')
0052 |     return result
0053 | 
0054 | 
0055 | def collect_sse(response, max_bytes, on_content=None):
0056 |     total, content, calls, event = 0, '', {}, []
0057 |     finished = False
0058 |     while True:
0059 |         line = response.readline(max_bytes-total+1)
0060 |         total += len(line)
0061 |         if total > max_bytes:
0062 |             raise ModelResponseError('模型响应超过大小上限')
0063 |         if not line:
0064 |             raise ModelResponseError('API 流提前结束，工具未执行')
0065 |         try:
0066 |             line = line.decode('utf-8').rstrip('\r\n')
0067 |         except UnicodeError as error:
0068 |             raise ModelResponseError('API 流编码错误') from error
0069 |         if line.startswith('data:'):
0070 |             event.append(line[5:].lstrip(' '))
0071 |         if line or not event:
0072 |             continue
0073 |         data = '\n'.join(event)
0074 |         event = []
0075 |         if data == '[DONE]':
0076 |             if not finished:
0077 |                 raise ModelResponseError('API 流缺少完成原因')
0078 |             return normalize({'content': content, 'tool_calls': [calls[key] for key in sorted(calls)]})
0079 |         try:
0080 |             chunk = json.loads(data)
0081 |             if 'error' in chunk:
0082 |                 raise ValueError()
0083 |             choices = chunk.get('choices', [])
0084 |             if not choices:
0085 |                 continue
0086 |             choice = choices[0]
0087 |             if finished:
0088 |                 raise ValueError()
0089 |             delta = choice.get('delta', {})
0090 |             text = delta.get('content') or ''
0091 |             if not isinstance(text, str):
0092 |                 raise ValueError()
0093 |             content += text
0094 |             if text and on_content:
0095 |                 on_content(text)
0096 |             for part in delta.get('tool_calls') or []:
0097 |                 index = part['index']
0098 |                 if type(index) is not int or not 0 <= index < 64:
0099 |                     raise ValueError()
0100 |                 target = calls.setdefault(index, {'id': '', 'function': {'name': '', 'arguments': ''}})
0101 |                 if part.get('id'):
0102 |                     if target['id'] and target['id'] != part['id']:
0103 |                         raise ValueError()
0104 |                     target['id'] = part['id']
0105 |                 for field in ('name', 'arguments'):
0106 |                     target['function'][field] += part.get('function', {}).get(field, '')
0107 |             reason = choice.get('finish_reason')
0108 |             if reason is not None:
0109 |                 if reason not in ('stop', 'tool_calls'):
0110 |                     raise ModelResponseError('API 响应未完整完成: ' + str(reason))
0111 |                 finished = True
0112 |         except (ValueError, KeyError, TypeError, AttributeError) as error:
0113 |             if isinstance(error, ModelResponseError):
0114 |                 raise
0115 |             raise ModelResponseError('API SSE 数据格式错误') from error
```
