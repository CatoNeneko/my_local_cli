# context_window.py：源码导读

按完整用户轮次组织消息，在字符预算中选最近历史，注入当前规则与摘要。

先读专题：[04-context.md](../04-context.md)。

实际源码：[context_window.py](../../../context_window.py)。

快照 SHA256：`b344d3c77f19acf5703c0192dd005815b4d4a07fbe2cc9e98df61252231fd9f3`；102 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `from config import context_config, model_config` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `from project_instructions import build_model_messages` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [valid_turn](#valid-turn) | [12](../../../context_window.py#L12) | 按assistant工具请求与后续tool顺序消耗pending，判断链完整。 |
| [split_turns](#split-turns) | [37](../../../context_window.py#L37) | 每条user开始新轮，跳开头无用户的残留。 |
| [request_size](#request-size) | [50](../../../context_window.py#L50) | 序列化真实协议近似请求，计字符而非token。 |
| [prepare_context](#prepare-context) | [60](../../../context_window.py#L60) | 注入规则/摘要，在预算里从新向旧保留完整轮。 |

<a id="valid-turn"></a>
## valid_turn

按assistant工具请求与后续tool顺序消耗pending，判断链完整。

```python
def valid_turn(turn)
```

位置：[12行](../../../context_window.py#L12) 至快照 34 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `turn` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`call.get`、`call['function'].get`、`isinstance`、`message.get`、`pending.append`、`pending.pop`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 13 | `pending` | `[]` | 等待配对的工具结果/ID队列，或临时注册项映射。 |
| 15 | `role` | `message.get('role')` | 消息身份字段，决定user/assistant/tool/system的协议解释。 |
| 19 | `calls` | `message.get('tool_calls', [])` | 工具调用计数或按index缓存的调用集合；来源表达式决定类型。 |
| 25 | `name` | `call['function'].get('name')` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 13 | 函数体 | 将 `[]` 赋给 `pending`。 |
| 14 | 函数体 | 遍历 `turn`，每次绑定 `message`。 |
| 15 | 函数体 / 循环每次 | 将 `message.get('role')` 赋给 `role`。 |
| 16 | 函数体 / 循环每次 | 条件 `role == 'assistant'`：真时执行body，假时进入else/后续。 |
| 17 | 函数体 / 循环每次 / 条件为真 | 条件 `pending`：真时执行body，假时进入else/后续。 |
| 18 | 函数体 / 循环每次 / 条件为真 / 条件为真 | 返回 `False`，结束当前函数；具体分支见完整源码。 |
| 19 | 函数体 / 循环每次 / 条件为真 | 将 `message.get('tool_calls', [])` 赋给 `calls`。 |
| 20 | 函数体 / 循环每次 / 条件为真 | 条件 `not isinstance(calls, list)`：真时执行body，假时进入else/后续。 |
| 21 | 函数体 / 循环每次 / 条件为真 / 条件为真 | 返回 `False`，结束当前函数；具体分支见完整源码。 |
| 22 | 函数体 / 循环每次 / 条件为真 | 遍历 `calls`，每次绑定 `call`。 |
| 23 | 函数体 / 循环每次 / 条件为真 / 循环每次 | 条件 `not isinstance(call, dict) or not isinstance(call.get('function'), dict)`：真时执行body，假时进入else/后续。 |
| 24 | 函数体 / 循环每次 / 条件为真 / 循环每次 / 条件为真 | 返回 `False`，结束当前函数；具体分支见完整源码。 |
| 25 | 函数体 / 循环每次 / 条件为真 / 循环每次 | 将 `call['function'].get('name')` 赋给 `name`。 |
| 26 | 函数体 / 循环每次 / 条件为真 / 循环每次 | 条件 `not isinstance(name, str) or not name`：真时执行body，假时进入else/后续。 |
| 27 | 函数体 / 循环每次 / 条件为真 / 循环每次 / 条件为真 | 返回 `False`，结束当前函数；具体分支见完整源码。 |
| 28 | 函数体 / 循环每次 / 条件为真 / 循环每次 | 计算表达式/调用产生动作：`pending.append(name)`。 |
| 29 | 函数体 / 循环每次 / 条件为假/elif | 条件 `role == 'tool'`：真时执行body，假时进入else/后续。 |
| 30 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 | 条件 `not pending or message.get('tool_name') != pending.pop(0)`：真时执行body，假时进入else/后续。 |
| 31 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 / 条件为真 | 返回 `False`，结束当前函数；具体分支见完整源码。 |
| 32 | 函数体 / 循环每次 / 条件为假/elif / 条件为假/elif | 条件 `role != 'user'`：真时执行body，假时进入else/后续。 |
| 33 | 函数体 / 循环每次 / 条件为假/elif / 条件为假/elif / 条件为真 | 返回 `False`，结束当前函数；具体分支见完整源码。 |
| 34 | 函数体 | 返回 `not pending`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L18：`False`。
- L21：`False`。
- L24：`False`。
- L27：`False`。
- L31：`False`。
- L33：`False`。
- L34：`not pending`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="split-turns"></a>
## split_turns

每条user开始新轮，跳开头无用户的残留。

```python
def split_turns(messages)
```

位置：[37行](../../../context_window.py#L37) 至快照 47 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `messages` | `未显式注解` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ContextBudgetError`、`isinstance`、`message.get`、`turns.append`、`turns[-1].append`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 38 | `turns` | `[]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 38 | 函数体 | 将 `[]` 赋给 `turns`。 |
| 39 | 函数体 | 遍历 `messages`，每次绑定 `message`。 |
| 40 | 函数体 / 循环每次 | 条件 `not isinstance(message, dict)`：真时执行body，假时进入else/后续。 |
| 41 | 函数体 / 循环每次 / 条件为真 | 抛出 `ContextBudgetError('聊天消息格式无效')`。 |
| 42 | 函数体 / 循环每次 | 条件 `message.get('role') == 'user'`：真时执行body，假时进入else/后续。 |
| 43 | 函数体 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`turns.append([message])`。 |
| 44 | 函数体 / 循环每次 / 条件为假/elif | 条件 `turns`：真时执行body，假时进入else/后续。 |
| 45 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 | 计算表达式/调用产生动作：`turns[-1].append(message)`。 |
| 47 | 函数体 | 返回 `turns`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L47：`turns`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="request-size"></a>
## request_size

序列化真实协议近似请求，计字符而非token。

```python
def request_size(messages, tools)
```

位置：[50行](../../../context_window.py#L50) 至快照 57 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `messages` | `未显式注解` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |
| `tools` | `未显式注解` | 发给模型的工具声明列表，不含handler函数对象。 |

**调用表达式（静态提取，不含内层独立函数体）**：`json.dumps`、`len`、`model_config.get`、`wire_messages`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 53 | `messages` | `wire_messages(messages)` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 51 | 函数体 | 条件 `model_config.get('provider') == 'openai'`：真时执行body，假时进入else/后续。 |
| 52 | 函数体 / 条件为真 | 在此处导入依赖：`from api_adapter import wire_messages`；局部导入可延迟加载或避免循环。 |
| 53 | 函数体 / 条件为真 | 将 `wire_messages(messages)` 赋给 `messages`。 |
| 54 | 函数体 | 返回 `len(json.dumps({'model': model_config['model'], 'messages': messages, 'stream': False, 'tools': tools}, ensure_ascii=False))`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L54：`len(json.dumps({'model': model_config['model'], 'messages': messages, 'stream': False, 'tools': tools}, ensure_ascii=False))`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="prepare-context"></a>
## prepare_context

注入规则/摘要，在预算里从新向旧保留完整轮。

```python
def prepare_context(messages, tools, include_context=True)
```

位置：[60行](../../../context_window.py#L60) 至快照 102 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `messages` | `未显式注解` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |
| `tools` | `未显式注解` | 发给模型的工具声明列表，不含handler函数对象。 |
| `include_context` | `未显式注解` | 是否注入项目与会话上下文；独立请求通常关闭。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ContextBudgetError`、`build_model_messages`、`context_config.get`、`context_view`、`isinstance`、`len`、`messages[start].get`、`prefix.append`、`range`、`request_size`、`split_turns`、`summary_message`、`type`、`valid_turn`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 61 | `budget` | `context_config.get('max_request_chars')` | 模型请求的序列化字符预算。 |
| 62 | `turn_limit` | `context_config.get('max_history_turns')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 66 | `view` | `context_view(messages) if include_context else {'messages': messages, 'summary': '', 'covered': 0}` | 验证摘要后得到的历史视图：summary、covered、messages。 |
| 67 | `messages` | `view['messages']` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |
| 68 | `prefix` | `build_model_messages([]) if include_context else []` | 系统规则/摘要前缀；模糊/路径函数中则是待补全名字前缀。 |
| 71 | `start` | `0` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 76 | `turns` | `split_turns(messages[start:])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 79 | `selected` | `[]` | 界面高亮索引，某些主循环分支为选择结果；看当前层次。 |
| 80 | `kept` | `0` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 82 | `turn` | `turns[index]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 87 | `candidate` | `turn + selected` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 92 | `selected` | `candidate` | 界面高亮索引，某些主循环分支为选择结果；看当前层次。 |
| 96 | `final` | `prefix + selected` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 61 | 函数体 | 将 `context_config.get('max_request_chars')` 赋给 `budget`。 |
| 62 | 函数体 | 将 `context_config.get('max_history_turns')` 赋给 `turn_limit`。 |
| 63 | 函数体 | 条件 `type(budget) is not int or budget <= 0 or type(turn_limit) is not int or (turn_limit <= 0)`：真时执行body，假时进入else/后续。 |
| 64 | 函数体 / 条件为真 | 抛出 `ContextBudgetError('上下文预算必须是正整数')`。 |
| 65 | 函数体 | 在此处导入依赖：`from compaction import context_view, summary_message`；局部导入可延迟加载或避免循环。 |
| 66 | 函数体 | 将 `context_view(messages) if include_context else {'messages': messages, 'summary': '', 'covered': 0}` 赋给 `view`。 |
| 67 | 函数体 | 将 `view['messages']` 赋给 `messages`。 |
| 68 | 函数体 | 将 `build_model_messages([]) if include_context else []` 赋给 `prefix`。 |
| 69 | 函数体 | 条件 `view['summary']`：真时执行body，假时进入else/后续。 |
| 70 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`prefix.append(summary_message(view['summary']))`。 |
| 71 | 函数体 | 将 `0` 赋给 `start`。 |
| 73 | 函数体 | 循环检查 `start < len(messages) and isinstance(messages[start], dict) and (messages[start].get('role') == 'system')`，break/return/异常可结束。 |
| 74 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`prefix.append(messages[start])`。 |
| 75 | 函数体 / 循环每次 | 更新已有变量：`start += 1`。 |
| 76 | 函数体 | 将 `split_turns(messages[start:])` 赋给 `turns`。 |
| 77 | 函数体 | 条件 `request_size(prefix, tools) > budget`：真时执行body，假时进入else/后续。 |
| 78 | 函数体 / 条件为真 | 抛出 `ContextBudgetError('系统规则、Skills 和工具声明已超预算，请减少规则或工具')`。 |
| 79 | 函数体 | 将 `[]` 赋给 `selected`。 |
| 80 | 函数体 | 将 `0` 赋给 `kept`。 |
| 81 | 函数体 | 遍历 `range(len(turns) - 1, -1, -1)`，每次绑定 `index`。 |
| 82 | 函数体 / 循环每次 | 将 `turns[index]` 赋给 `turn`。 |
| 83 | 函数体 / 循环每次 | 条件 `not valid_turn(turn)`：真时执行body，假时进入else/后续。 |
| 84 | 函数体 / 循环每次 / 条件为真 | 条件 `index == len(turns) - 1`：真时执行body，假时进入else/后续。 |
| 85 | 函数体 / 循环每次 / 条件为真 / 条件为真 | 抛出 `ContextBudgetError('最新一轮工具调用与结果不完整，请检查或清空当前会话')`。 |
| 86 | 函数体 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 87 | 函数体 / 循环每次 | 将 `turn + selected` 赋给 `candidate`。 |
| 88 | 函数体 / 循环每次 | 条件 `request_size(prefix + candidate, tools) > budget`：真时执行body，假时进入else/后续。 |
| 89 | 函数体 / 循环每次 / 条件为真 | 条件 `not selected`：真时执行body，假时进入else/后续。 |
| 90 | 函数体 / 循环每次 / 条件为真 / 条件为真 | 抛出 `ContextBudgetError('最新一轮消息超预算，请缩小附件、工具结果或输入，或调整上下文预算')`。 |
| 91 | 函数体 / 循环每次 / 条件为真 | break结束最近一层循环。 |
| 92 | 函数体 / 循环每次 | 将 `candidate` 赋给 `selected`。 |
| 93 | 函数体 / 循环每次 | 更新已有变量：`kept += 1`。 |
| 94 | 函数体 / 循环每次 | 条件 `kept >= turn_limit`：真时执行body，假时进入else/后续。 |
| 95 | 函数体 / 循环每次 / 条件为真 | break结束最近一层循环。 |
| 96 | 函数体 | 将 `prefix + selected` 赋给 `final`。 |
| 97 | 函数体 | 返回 `{'messages': final, 'chars': request_size(final, tools), 'budget': budget, 'total_turns': len(turns), 'sent_turns': kept, 'summarized_messages': view['covered'], 'summary…（见完整源码）`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L97：`{'messages': final, 'chars': request_size(final, tools), 'budget': budget, 'total_turns': len(turns), 'sent_turns': kept, 'summarized_messages': view['covered'], 'summary_chars': len(view['summary']), 'omitted_…（见完整源码）`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- class：对象状态与方法/继承：L8。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """构造有界请求上下文；磁盘历史不裁剪，工具链按用户轮次保留。"""
0002 | import json
0003 | 
0004 | from config import context_config, model_config
0005 | from project_instructions import build_model_messages
0006 | 
0007 | 
0008 | class ContextBudgetError(ValueError):
0009 |     pass
0010 | 
0011 | 
0012 | def valid_turn(turn):
0013 |     pending = []
0014 |     for message in turn:
0015 |         role = message.get("role")
0016 |         if role == "assistant":
0017 |             if pending:
0018 |                 return False
0019 |             calls = message.get("tool_calls", [])
0020 |             if not isinstance(calls, list):
0021 |                 return False
0022 |             for call in calls:
0023 |                 if not isinstance(call, dict) or not isinstance(call.get("function"), dict):
0024 |                     return False
0025 |                 name = call["function"].get("name")
0026 |                 if not isinstance(name, str) or not name:
0027 |                     return False
0028 |                 pending.append(name)
0029 |         elif role == "tool":
0030 |             if not pending or message.get("tool_name") != pending.pop(0):
0031 |                 return False
0032 |         elif role != "user":
0033 |             return False
0034 |     return not pending
0035 | 
0036 | 
0037 | def split_turns(messages):
0038 |     turns = []
0039 |     for message in messages:
0040 |         if not isinstance(message, dict):
0041 |             raise ContextBudgetError("聊天消息格式无效")
0042 |         if message.get("role") == "user":
0043 |             turns.append([message])
0044 |         elif turns:
0045 |             turns[-1].append(message)
0046 |         # 没有对应用户轮次的开头残留消息不发送，避免孤立工具结果。
0047 |     return turns
0048 | 
0049 | 
0050 | def request_size(messages, tools):
0051 |     if model_config.get("provider") == "openai":
0052 |         from api_adapter import wire_messages
0053 |         messages = wire_messages(messages)
0054 |     return len(json.dumps({
0055 |         "model": model_config["model"], "messages": messages,
0056 |         "stream": False, "tools": tools
0057 |     }, ensure_ascii=False))
0058 | 
0059 | 
0060 | def prepare_context(messages, tools, include_context=True):
0061 |     budget = context_config.get("max_request_chars")
0062 |     turn_limit = context_config.get("max_history_turns")
0063 |     if type(budget) is not int or budget <= 0 or type(turn_limit) is not int or turn_limit <= 0:
0064 |         raise ContextBudgetError("上下文预算必须是正整数")
0065 |     from compaction import context_view, summary_message
0066 |     view = context_view(messages) if include_context else {'messages': messages, 'summary': '', 'covered': 0}
0067 |     messages = view['messages']
0068 |     prefix = build_model_messages([]) if include_context else []
0069 |     if view['summary']:
0070 |         prefix.append(summary_message(view['summary']))
0071 |     start = 0
0072 |     # Skill 生成请求带有自己的 system 提示，也始终保留。
0073 |     while start < len(messages) and isinstance(messages[start], dict) and messages[start].get("role") == "system":
0074 |         prefix.append(messages[start])
0075 |         start += 1
0076 |     turns = split_turns(messages[start:])
0077 |     if request_size(prefix, tools) > budget:
0078 |         raise ContextBudgetError("系统规则、Skills 和工具声明已超预算，请减少规则或工具")
0079 |     selected = []
0080 |     kept = 0
0081 |     for index in range(len(turns) - 1, -1, -1):
0082 |         turn = turns[index]
0083 |         if not valid_turn(turn):
0084 |             if index == len(turns) - 1:
0085 |                 raise ContextBudgetError("最新一轮工具调用与结果不完整，请检查或清空当前会话")
0086 |             continue
0087 |         candidate = turn + selected
0088 |         if request_size(prefix + candidate, tools) > budget:
0089 |             if not selected:
0090 |                 raise ContextBudgetError("最新一轮消息超预算，请缩小附件、工具结果或输入，或调整上下文预算")
0091 |             break
0092 |         selected = candidate
0093 |         kept += 1
0094 |         if kept >= turn_limit:
0095 |             break
0096 |     final = prefix + selected
0097 |     return {
0098 |         "messages": final, "chars": request_size(final, tools), "budget": budget,
0099 |         "total_turns": len(turns), "sent_turns": kept,
0100 |         "summarized_messages": view["covered"], "summary_chars": len(view["summary"]),
0101 |         "omitted_messages": len(messages) - start - len(selected)
0102 |     }
```
