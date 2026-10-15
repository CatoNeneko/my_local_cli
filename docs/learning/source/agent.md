# agent.py：源码导读

主模型工具循环：按轮次请求、顺序执行、保存完整调用链。不是并行子代理调度器。

先读专题：[02-agent.md](../02-agent.md)。

实际源码：[agent.py](../../../agent.py)。

快照 SHA256：`bcccc513c8e17c27260a3f0d5deff61479030330650c1df67689e81b01ff3d9f`；101 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 1 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `from config import agent_config, model_config` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `from history import append_messages` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `from model_client import request_message` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `from tools import execute_tool` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `from context_window import ContextBudgetError` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [run_agent](#run-agent) | [10](../../../agent.py#L10) | 取最近用户任务，设置审批task_scope，再运行内部循环。 |
| [_run_agent](#-run-agent) | [17](../../../agent.py#L17) | 控制模型轮次和工具次数，执行结果补齐后成批保存，再请求模型。 |

<a id="run-agent"></a>
## run_agent

取最近用户任务，设置审批task_scope，再运行内部循环。

```python
def run_agent(messages, output=None)
```

位置：[10行](../../../agent.py#L10) 至快照 14 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `messages` | `未显式注解` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |
| `output` | `未显式注解` | ConsoleOutput对象、缓冲或UI输出接口，具体按签名位置。 |

**调用表达式（静态提取，不含内层独立函数体）**：`_run_agent`、`message.get`、`next`、`reversed`、`task_scope`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 12 | `task` | `next((message.get('content', '') for message in reversed(messages) if message.get('role') == 'user'), '')` | 本轮用户目标或子代理独立任务文字，不等于授权。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 11 | 函数体 | 在此处导入依赖：`from approval import task_scope`；局部导入可延迟加载或避免循环。 |
| 12 | 函数体 | 将 `next((message.get('content', '') for message in reversed(messages) if message.get('role') == 'user'), '')` 赋给 `task`。 |
| 13 | 函数体 | 进入资源/状态范围：`task_scope(task)`；退出执行清理。 |
| 14 | 函数体 / with范围 | 返回 `_run_agent(messages, output)`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L14：`_run_agent(messages, output)`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="-run-agent"></a>
## _run_agent

控制模型轮次和工具次数，执行结果补齐后成批保存，再请求模型。

```python
def _run_agent(messages, output=None)
```

位置：[17行](../../../agent.py#L17) 至快照 101 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `messages` | `未显式注解` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |
| `output` | `未显式注解` | ConsoleOutput对象、缓冲或UI输出接口，具体按签名位置。 |

**调用表达式（静态提取，不含内层独立函数体）**：`append_messages`、`assistant_message.get`、`bool`、`dict`、`execute_tool`、`function.get`、`isinstance`、`json.dumps`、`messages.extend`、`output.begin`、`output.end`、`range`、`request_message`、`result.get`、`round_messages.append`、`str`、`tool_call.get`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 18 | `tool_count` | `0` | 本次主任务累计执行尝试次数，跨模型轮次计数。 |
| 19 | `max_tool_calls` | `agent_config['max_tool_calls']` | 本次任务允许的总工具调用次数上限，当前从agent_config读取。 |
| 23 | `assistant_message` | `request_message(messages)` | 本轮模型完整响应，包含content和可选tool_calls。 |
| 27 | `assistant_message` | `request_message(messages, stream=model_config['stream'], on_content=output.write)` | 本轮模型完整响应，包含content和可选tool_calls。 |
| 39 | `content` | `assistant_message.get('content', '')` | 文件正文、消息文字或累计响应；看role与来源。 |
| 42 | `tool_calls` | `assistant_message.get('tool_calls', [])` | 当前模型返回的工具调用列表，必须先检查列表与单项结构。 |
| 53 | `function` | `tool_call.get('function')` | 模型工具调用的function子字典，含name和arguments。 |
| 56 | `name` | `function.get('name')` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| 60 | `assistant_message` | `dict(assistant_message)` | 本轮模型完整响应，包含content和可选tool_calls。 |
| 61 | `assistant_message['role']` | `'assistant'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 62 | `assistant_message['content']` | `content` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 63 | `round_messages` | `[assistant_message]` | 本轮assistant工具请求与对应tool结果，整批持久化。 |
| 64 | `budget_exhausted` | `False` | 工具总次数超预算标志，用于补齐未执行结果后停止。 |
| 65 | `cancelled` | `False` | 当前任务/工具发生取消，之后不应继续执行同批动作。 |
| 68 | `function` | `tool_call['function']` | 模型工具调用的function子字典，含name和arguments。 |
| 69 | `name` | `function['name']` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| 70 | `arguments` | `function.get('arguments', {})` | 外部或模型提交的工具参数，必须经schema检查。 |
| 72 | `result` | `{'ok': False, 'cancelled': True, 'error': '任务已取消，工具未执行'}` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 75 | `budget_exhausted` | `True` | 工具总次数超预算标志，用于补齐未执行结果后停止。 |
| 76 | `result` | `{'ok': False, 'error': '调用预算耗尽，工具未执行'}` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 80 | `result` | `execute_tool(name, arguments)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 82 | `result` | `{'ok': False, 'cancelled': True, 'error': '工具已取消；已完成操作不会回滚'}` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 83 | `cancelled` | `bool(result.get('cancelled'))` | 当前任务/工具发生取消，之后不应继续执行同批动作。 |
| 85 | `tool_message` | `{'role': 'tool', 'tool_name': name, 'content': json.dumps(result, ensure_ascii=False)}` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 91 | `tool_message['tool_call_id']` | `tool_call['id']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 18 | 函数体 | 将 `0` 赋给 `tool_count`。 |
| 19 | 函数体 | 将 `agent_config['max_tool_calls']` 赋给 `max_tool_calls`。 |
| 20 | 函数体 | 遍历 `range(agent_config['max_rounds'])`，每次绑定 `round_number`。 |
| 21 | 函数体 / 循环每次 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 22 | 函数体 / 循环每次 / try | 条件 `output is None`：真时执行body，假时进入else/后续。 |
| 23 | 函数体 / 循环每次 / try / 条件为真 | 将 `request_message(messages)` 赋给 `assistant_message`。 |
| 25 | 函数体 / 循环每次 / try / 条件为假/elif | 计算表达式/调用产生动作：`output.begin()`。 |
| 26 | 函数体 / 循环每次 / try / 条件为假/elif | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 27 | 函数体 / 循环每次 / try / 条件为假/elif / try | 将 `request_message(messages, stream=model_config['stream'], on_content=output.write)` 赋给 `assistant_message`。 |
| 31 | 函数体 / 循环每次 / try / 条件为假/elif / finally保证清理 | 计算表达式/调用产生动作：`output.end()`。 |
| 32 | 函数体 / 循环每次 | except ContextBudgetError as error：只处理匹配类型的异常。 |
| 33 | 函数体 / 循环每次 / except ContextBudgetError as error | 返回 `'上下文请求已停止：' + str(error)`，结束当前函数；具体分支见完整源码。 |
| 34 | 函数体 / 循环每次 | except KeyboardInterrupt：只处理匹配类型的异常。 |
| 35 | 函数体 / 循环每次 / except KeyboardInterrupt | 返回 `'已取消当前模型生成；此前完成的工具操作不会回滚。'`，结束当前函数；具体分支见完整源码。 |
| 36 | 函数体 / 循环每次 | 条件 `not isinstance(assistant_message, dict)`：真时执行body，假时进入else/后续。 |
| 37 | 函数体 / 循环每次 / 条件为真 | 返回 `'模型返回格式错误：消息必须是字典。'`，结束当前函数；具体分支见完整源码。 |
| 39 | 函数体 / 循环每次 | 将 `assistant_message.get('content', '')` 赋给 `content`。 |
| 40 | 函数体 / 循环每次 | 条件 `not isinstance(content, str)`：真时执行body，假时进入else/后续。 |
| 41 | 函数体 / 循环每次 / 条件为真 | 返回 `'模型返回格式错误：content 必须是字符串。'`，结束当前函数；具体分支见完整源码。 |
| 42 | 函数体 / 循环每次 | 将 `assistant_message.get('tool_calls', [])` 赋给 `tool_calls`。 |
| 43 | 函数体 / 循环每次 | 条件 `not isinstance(tool_calls, list)`：真时执行body，假时进入else/后续。 |
| 44 | 函数体 / 循环每次 / 条件为真 | 返回 `'模型返回格式错误：tool_calls 必须是列表。'`，结束当前函数；具体分支见完整源码。 |
| 45 | 函数体 / 循环每次 | 条件 `not tool_calls`：真时执行body，假时进入else/后续。 |
| 47 | 函数体 / 循环每次 / 条件为真 | 返回 `content`，结束当前函数；具体分支见完整源码。 |
| 50 | 函数体 / 循环每次 | 遍历 `tool_calls`，每次绑定 `tool_call`。 |
| 51 | 函数体 / 循环每次 / 循环每次 | 条件 `not isinstance(tool_call, dict)`：真时执行body，假时进入else/后续。 |
| 52 | 函数体 / 循环每次 / 循环每次 / 条件为真 | 返回 `'模型返回格式错误：单条工具调用必须是字典。'`，结束当前函数；具体分支见完整源码。 |
| 53 | 函数体 / 循环每次 / 循环每次 | 将 `tool_call.get('function')` 赋给 `function`。 |
| 54 | 函数体 / 循环每次 / 循环每次 | 条件 `not isinstance(function, dict)`：真时执行body，假时进入else/后续。 |
| 55 | 函数体 / 循环每次 / 循环每次 / 条件为真 | 返回 `'模型返回格式错误：缺少有效的 function。'`，结束当前函数；具体分支见完整源码。 |
| 56 | 函数体 / 循环每次 / 循环每次 | 将 `function.get('name')` 赋给 `name`。 |
| 57 | 函数体 / 循环每次 / 循环每次 | 条件 `not isinstance(name, str) or not name`：真时执行body，假时进入else/后续。 |
| 58 | 函数体 / 循环每次 / 循环每次 / 条件为真 | 返回 `'模型返回格式错误：工具名称必须是非空字符串。'`，结束当前函数；具体分支见完整源码。 |
| 60 | 函数体 / 循环每次 | 将 `dict(assistant_message)` 赋给 `assistant_message`。 |
| 61 | 函数体 / 循环每次 | 将 `'assistant'` 赋给 `assistant_message['role']`。 |
| 62 | 函数体 / 循环每次 | 将 `content` 赋给 `assistant_message['content']`。 |
| 63 | 函数体 / 循环每次 | 将 `[assistant_message]` 赋给 `round_messages`。 |
| 64 | 函数体 / 循环每次 | 将 `False` 赋给 `budget_exhausted`。 |
| 65 | 函数体 / 循环每次 | 将 `False` 赋给 `cancelled`。 |
| 67 | 函数体 / 循环每次 | 遍历 `tool_calls`，每次绑定 `tool_call`。 |
| 68 | 函数体 / 循环每次 / 循环每次 | 将 `tool_call['function']` 赋给 `function`。 |
| 69 | 函数体 / 循环每次 / 循环每次 | 将 `function['name']` 赋给 `name`。 |
| 70 | 函数体 / 循环每次 / 循环每次 | 将 `function.get('arguments', {})` 赋给 `arguments`。 |
| 71 | 函数体 / 循环每次 / 循环每次 | 条件 `cancelled`：真时执行body，假时进入else/后续。 |
| 72 | 函数体 / 循环每次 / 循环每次 / 条件为真 | 将 `{'ok': False, 'cancelled': True, 'error': '任务已取消，工具未执行'}` 赋给 `result`。 |
| 73 | 函数体 / 循环每次 / 循环每次 / 条件为假/elif | 条件 `tool_count >= max_tool_calls`：真时执行body，假时进入else/后续。 |
| 75 | 函数体 / 循环每次 / 循环每次 / 条件为假/elif / 条件为真 | 将 `True` 赋给 `budget_exhausted`。 |
| 76 | 函数体 / 循环每次 / 循环每次 / 条件为假/elif / 条件为真 | 将 `{'ok': False, 'error': '调用预算耗尽，工具未执行'}` 赋给 `result`。 |
| 78 | 函数体 / 循环每次 / 循环每次 / 条件为假/elif / 条件为假/elif | 更新已有变量：`tool_count += 1`。 |
| 79 | 函数体 / 循环每次 / 循环每次 / 条件为假/elif / 条件为假/elif | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 80 | 函数体 / 循环每次 / 循环每次 / 条件为假/elif / 条件为假/elif / try | 将 `execute_tool(name, arguments)` 赋给 `result`。 |
| 81 | 函数体 / 循环每次 / 循环每次 / 条件为假/elif / 条件为假/elif | except KeyboardInterrupt：只处理匹配类型的异常。 |
| 82 | 函数体 / 循环每次 / 循环每次 / 条件为假/elif / 条件为假/elif / except KeyboardInterrupt | 将 `{'ok': False, 'cancelled': True, 'error': '工具已取消；已完成操作不会回滚'}` 赋给 `result`。 |
| 83 | 函数体 / 循环每次 / 循环每次 / 条件为假/elif / 条件为假/elif | 将 `bool(result.get('cancelled'))` 赋给 `cancelled`。 |
| 85 | 函数体 / 循环每次 / 循环每次 | 将 `{'role': 'tool', 'tool_name': name, 'content': json.dumps(result, ensure_ascii=False)}` 赋给 `tool_message`。 |
| 90 | 函数体 / 循环每次 / 循环每次 | 条件 `tool_call.get('id')`：真时执行body，假时进入else/后续。 |
| 91 | 函数体 / 循环每次 / 循环每次 / 条件为真 | 将 `tool_call['id']` 赋给 `tool_message['tool_call_id']`。 |
| 92 | 函数体 / 循环每次 / 循环每次 | 计算表达式/调用产生动作：`round_messages.append(tool_message)`。 |
| 94 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`append_messages(round_messages)`。 |
| 95 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`messages.extend(round_messages)`。 |
| 96 | 函数体 / 循环每次 | 条件 `cancelled`：真时执行body，假时进入else/后续。 |
| 97 | 函数体 / 循环每次 / 条件为真 | 返回 `'已取消当前任务并返回输入；已完成的操作不会回滚，请检查写入或外部操作的实际状态。'`，结束当前函数；具体分支见完整源码。 |
| 98 | 函数体 / 循环每次 | 条件 `budget_exhausted`：真时执行body，假时进入else/后续。 |
| 99 | 函数体 / 循环每次 / 条件为真 | 返回 `'已达到工具调用总次数上限，请缩小任务范围。'`，结束当前函数；具体分支见完整源码。 |
| 101 | 函数体 | 返回 `'已达到工具调用轮次上限，请缩小任务范围。'`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L33：`'上下文请求已停止：' + str(error)`。
- L35：`'已取消当前模型生成；此前完成的工具操作不会回滚。'`。
- L37：`'模型返回格式错误：消息必须是字典。'`。
- L41：`'模型返回格式错误：content 必须是字符串。'`。
- L44：`'模型返回格式错误：tool_calls 必须是列表。'`。
- L47：`content`。
- L52：`'模型返回格式错误：单条工具调用必须是字典。'`。
- L55：`'模型返回格式错误：缺少有效的 function。'`。
- L58：`'模型返回格式错误：工具名称必须是非空字符串。'`。
- L97：`'已取消当前任务并返回输入；已完成的操作不会回滚，请检查写入或外部操作的实际状态。'`。
- L99：`'已达到工具调用总次数上限，请缩小任务范围。'`。
- L101：`'已达到工具调用轮次上限，请缩小任务范围。'`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- with/yield：资源/状态生命周期或逐个生成：L13。
- try/except/finally：异常与保证清理：L21, L26, L79。
- 推导式/生成器表达式：循环建容器或逐个产生：L12。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | import json
0002 | 
0003 | from config import agent_config, model_config
0004 | from history import append_messages
0005 | from model_client import request_message
0006 | from tools import execute_tool
0007 | from context_window import ContextBudgetError
0008 | 
0009 | 
0010 | def run_agent(messages, output=None):
0011 |     from approval import task_scope
0012 |     task = next((message.get('content', '') for message in reversed(messages) if message.get('role') == 'user'), '')
0013 |     with task_scope(task):
0014 |         return _run_agent(messages, output)
0015 | 
0016 | 
0017 | def _run_agent(messages, output=None):
0018 |     tool_count = 0
0019 |     max_tool_calls = agent_config["max_tool_calls"]
0020 |     for round_number in range(agent_config["max_rounds"]):
0021 |         try:
0022 |             if output is None:
0023 |                 assistant_message = request_message(messages)
0024 |             else:
0025 |                 output.begin()
0026 |                 try:
0027 |                     assistant_message = request_message(
0028 |                         messages, stream=model_config['stream'], on_content=output.write
0029 |                     )
0030 |                 finally:
0031 |                     output.end()
0032 |         except ContextBudgetError as error:
0033 |             return "上下文请求已停止：" + str(error)
0034 |         except KeyboardInterrupt:
0035 |             return "已取消当前模型生成；此前完成的工具操作不会回滚。"
0036 |         if not isinstance(assistant_message, dict):
0037 |             return "模型返回格式错误：消息必须是字典。"
0038 | 
0039 |         content = assistant_message.get("content", "")
0040 |         if not isinstance(content, str):
0041 |             return "模型返回格式错误：content 必须是字符串。"
0042 |         tool_calls = assistant_message.get("tool_calls", [])
0043 |         if not isinstance(tool_calls, list):
0044 |             return "模型返回格式错误：tool_calls 必须是列表。"
0045 |         if not tool_calls:
0046 |             # 最终文字回复仍由主循环保存，避免重复记录。
0047 |             return content
0048 | 
0049 |         # 先验证整批结构，防止执行到一半才发现无法识别的调用。
0050 |         for tool_call in tool_calls:
0051 |             if not isinstance(tool_call, dict):
0052 |                 return "模型返回格式错误：单条工具调用必须是字典。"
0053 |             function = tool_call.get("function")
0054 |             if not isinstance(function, dict):
0055 |                 return "模型返回格式错误：缺少有效的 function。"
0056 |             name = function.get("name")
0057 |             if not isinstance(name, str) or not name:
0058 |                 return "模型返回格式错误：工具名称必须是非空字符串。"
0059 | 
0060 |         assistant_message = dict(assistant_message)
0061 |         assistant_message["role"] = "assistant"
0062 |         assistant_message["content"] = content
0063 |         round_messages = [assistant_message]
0064 |         budget_exhausted = False
0065 |         cancelled = False
0066 | 
0067 |         for tool_call in tool_calls:
0068 |             function = tool_call["function"]
0069 |             name = function["name"]
0070 |             arguments = function.get("arguments", {})
0071 |             if cancelled:
0072 |                 result = {'ok': False, 'cancelled': True, 'error': '任务已取消，工具未执行'}
0073 |             elif tool_count >= max_tool_calls:
0074 |                 # 不执行超预算调用，但补齐结果，使保存的消息链完整。
0075 |                 budget_exhausted = True
0076 |                 result = {"ok": False, "error": "调用预算耗尽，工具未执行"}
0077 |             else:
0078 |                 tool_count += 1
0079 |                 try:
0080 |                     result = execute_tool(name, arguments)
0081 |                 except KeyboardInterrupt:
0082 |                     result = {'ok': False, 'cancelled': True, 'error': '工具已取消；已完成操作不会回滚'}
0083 |                 cancelled = bool(result.get('cancelled'))
0084 | 
0085 |             tool_message = {
0086 |                 "role": "tool",
0087 |                 "tool_name": name,
0088 |                 "content": json.dumps(result, ensure_ascii=False)
0089 |             }
0090 |             if tool_call.get("id"):
0091 |                 tool_message["tool_call_id"] = tool_call["id"]
0092 |             round_messages.append(tool_message)
0093 | 
0094 |         append_messages(round_messages)
0095 |         messages.extend(round_messages)
0096 |         if cancelled:
0097 |             return '已取消当前任务并返回输入；已完成的操作不会回滚，请检查写入或外部操作的实际状态。'
0098 |         if budget_exhausted:
0099 |             return "已达到工具调用总次数上限，请缩小任务范围。"
0100 | 
0101 |     return "已达到工具调用轮次上限，请缩小任务范围。"
```
