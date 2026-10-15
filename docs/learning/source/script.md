# script.py：源码导读

实际交互命令循环与会话协调；命令分支continue，自然语言进入agent。

先读专题：[02-agent.md](../02-agent.md)。

实际源码：[script.py](../../../script.py)。

快照 SHA256：`1412d8ba85c739a69dd5df098bbf64b0a98cdbbd0ed02888f7a83d732f82a72d`；458 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 1 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 2 | `import shlex` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import urllib.error` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `from tools import search_file, search_project, get_tool_definitions` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `from tools import read_file` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `from config import model_config` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `from agent import run_agent` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `from permissions import resolve_project_path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 9 | `from history import clear_history, load_history, append_message` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 10 | `from mcp_manager import MCPManager` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 11 | `from config import mcp_config` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 12 | `from project_instructions import load_project_instructions, instruction_state` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 13 | `from skills import activate_skill, clear_skills, list_skills` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 14 | `from skill_generation import generate_skill` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 15 | `from sessions import SessionManager` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 16 | `from context_window import ContextBudgetError, prepare_context` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 17 | `from console_output import ConsoleOutput` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 18 | `from streaming import ModelResponseError` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 19 | `from command_help import show_help` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 20 | `from terminal_input import TerminalInput` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 21 | `from path_input import parse_path_arguments` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 22 | `from contextlib import nullcontext` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 23 | `from attachments import prepare_attachments` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 24 | `from tool_display import safe_text` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [show_history](#show-history) | [27](../../../script.py#L27) | 按保存消息逐条打印role与content。 |
| [attach_files](#attach-files) | [35](../../../script.py#L35) | 仅完整准备成功才保存附件并加入messages。 |
| [main](#main) | [46](../../../script.py#L46) | 选择workspace上下文，运行_main，finally清理所有owned任务。 |
| [_main](#-main) | [57](../../../script.py#L57) | 初始化会话/输入/规则/MCP，循环分派命令与保存自然语言任务和回复。 |

<a id="show-history"></a>
## show_history

按保存消息逐条打印role与content。

```python
def show_history(messages)
```

位置：[27行](../../../script.py#L27) 至快照 32 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `messages` | `未显式注解` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`print`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 28 | 函数体 | 条件 `not messages`：真时执行body，假时进入else/后续。 |
| 29 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`print("there's no messages")`。 |
| 31 | 函数体 / 条件为假/elif | 遍历 `messages`，每次绑定 `message`。 |
| 32 | 函数体 / 条件为假/elif / 循环每次 | 计算表达式/调用产生动作：`print(message['role'] + ': ' + message['content'])`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="attach-files"></a>
## attach_files

仅完整准备成功才保存附件并加入messages。

```python
def attach_files(paths, messages)
```

位置：[35行](../../../script.py#L35) 至快照 42 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `paths` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `messages` | `未显式注解` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`', '.join`、`append_message`、`messages.append`、`prepare_attachments`、`print`、`safe_text`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 36 | `result` | `prepare_attachments(paths)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 36 | 函数体 | 将 `prepare_attachments(paths)` 赋给 `result`。 |
| 37 | 函数体 | 条件 `not result['ok']`：真时执行body，假时进入else/后续。 |
| 38 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`print(safe_text(result['error']))`。 |
| 39 | 函数体 / 条件为真 | 返回 `None`，结束当前函数；具体分支见完整源码。 |
| 40 | 函数体 | 计算表达式/调用产生动作：`append_message(result['message'])`。 |
| 41 | 函数体 | 计算表达式/调用产生动作：`messages.append(result['message'])`。 |
| 42 | 函数体 | 计算表达式/调用产生动作：`print('已添加附件:', safe_text(', '.join(result['paths'])))`。 |

**实际返回分支**：

- L39：`None`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="main"></a>
## main

选择workspace上下文，运行_main，finally清理所有owned任务。

```python
def main(*, initial_session=None, plain=False, no_mcp=False, workspace=None)
```

位置：[46行](../../../script.py#L46) 至快照 54 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `initial_session` | `未显式注解` | 启动指定会话名称；None使用default。 |
| `plain` | `未显式注解` | 强制普通input而非增强TTY。 |
| `no_mcp` | `未显式注解` | 本次运行禁止启动/刷新MCP。 |
| `workspace` | `未显式注解` | 目标项目目录，不是助手安装环境。 |

**调用表达式（静态提取，不含内层独立函数体）**：`_main`、`close_tasks`、`nullcontext`、`use_workspace`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 48 | `context` | `use_workspace(workspace) if workspace is not None else nullcontext()` | 资源上下文或准备的模型请求上下文；看当前来源区分。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 47 | 函数体 | 在此处导入依赖：`from workspace import use_workspace`；局部导入可延迟加载或避免循环。 |
| 48 | 函数体 | 将 `use_workspace(workspace) if workspace is not None else nullcontext()` 赋给 `context`。 |
| 49 | 函数体 | 进入资源/状态范围：`context`；退出执行清理。 |
| 50 | 函数体 / with范围 | 在此处导入依赖：`from process_tasks import close_tasks`；局部导入可延迟加载或避免循环。 |
| 51 | 函数体 / with范围 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 52 | 函数体 / with范围 / try | 返回 `_main(initial_session=initial_session, plain=plain, no_mcp=no_mcp)`，结束当前函数；具体分支见完整源码。 |
| 54 | 函数体 / with范围 / finally保证清理 | 计算表达式/调用产生动作：`close_tasks()`。 |

**实际返回分支**：

- L52：`_main(initial_session=initial_session, plain=plain, no_mcp=no_mcp)`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="-main"></a>
## _main

初始化会话/输入/规则/MCP，循环分派命令与保存自然语言任务和回复。

```python
def _main(*, initial_session=None, plain=False, no_mcp=False)
```

位置：[57行](../../../script.py#L57) 至快照 451 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `initial_session` | `未显式注解` | 启动指定会话名称；None使用default。 |
| `plain` | `未显式注解` | 强制普通input而非增强TTY。 |
| `no_mcp` | `未显式注解` | 本次运行禁止启动/刷新MCP。 |

**调用表达式（静态提取，不含内层独立函数体）**：`', '.join`、`({} if no_mcp else mcp_manager.load_configured()).items`、`ConsoleOutput`、`MCPManager`、`SessionManager`、`TerminalInput`、`ValueError`、`activate_skill`、`append_message`、`argument.partition`、`argument.split`、`argument.strip`、`attach_files`、`clear_history`、`clear_skills`、`compact_messages`、`content.splitlines`、`context_view`、`execute_tool`、`generate_skill`、`get_tool_definitions`、`json.dumps`、`len`、`list_skills`、`list_tasks`、`load_history`、`load_project_instructions`、`mcp_manager.connect`、`mcp_manager.load_configured`、`mcp_manager.refresh`、`mcp_manager.tool_names`、`messages.append`、`messages.clear`、`output.final`、`parse_path_arguments`、`prepare_context`、`print`、`read_file`、`rest.split`、`rest.strip`、`result.get`、`run_agent`、`safe_text`、`search_file`、`search_project`、`session_manager.export`、`session_manager.list_sessions`、`session_manager.rename`、`session_manager.switch`、`shlex.split`、`show_help`、`show_history`、`str`、`terminal.confirmations`、`terminal.pick_file`、`terminal.pick_files`、`terminal.read`、`terminal.read(session_manager.current_name).strip`、`user_text.partition`、`user_text.split`、`user_text.startswith`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 59 | `session_manager` | `SessionManager()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 60 | `initial_messages` | `None` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 62 | `result` | `session_manager.switch(initial_session)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 65 | `initial_messages` | `result['messages']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 66 | `terminal` | `TerminalInput(plain=plain)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 74 | `instruction_result` | `load_project_instructions()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 82 | `messages` | `load_history() if initial_messages is None else initial_messages` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |
| 85 | `user_text` | `terminal.read(session_manager.current_name).strip()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 89 | `selected` | `terminal.pick_files()` | 界面高亮索引，某些主循环分支为选择结果；看当前层次。 |
| 91 | `path` | `terminal.pick_file()` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| 92 | `selected` | `[path] if path is not None else None` | 界面高亮索引，某些主循环分支为选择结果；看当前层次。 |
| 97 | `path_arguments` | `None` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 98 | `(command, separator, argument)` | `user_text.partition(' ')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 101 | `path_arguments` | `parse_path_arguments(argument)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 129 | `result` | `session_manager.export(messages)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 134 | `result` | `session_manager.list_sessions()` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 139 | `marker` | `' (当前)' if name == session_manager.current_name else ''` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 149 | `parts` | `user_text.split(maxsplit=2)` | split得到的参数片段列表，须先检查数量。 |
| 153 | `result` | `session_manager.rename(parts[2])` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 158 | `name` | `user_text.split(maxsplit=1)[1]` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| 159 | `result` | `session_manager.switch(name)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 161 | `messages` | `result['messages']` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |
| 168 | `mode` | `argument.strip()` | 流式/审批等当前模式字符串。 |
| 172 | `approval_config['mode']` | `mode` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 181 | `option` | `argument.strip()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 183 | `context_config['auto_compact']` | `option == 'auto on'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 186 | `view` | `context_view(messages)` | 验证摘要后得到的历史视图：summary、covered、messages。 |
| 189 | `result` | `compact_messages(messages)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 197 | `context` | `prepare_context(messages, get_tool_definitions())` | 资源上下文或准备的模型请求上下文；看当前来源区分。 |
| 214 | `path` | `path_arguments[0]` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| 215 | `result` | `read_file(path)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 221 | `content` | `result['content']` | 文件正文、消息文字或累计响应；看role与来源。 |
| 222 | `line_number` | `1` | 人可读1起始行号，不是字符/字节偏移。 |
| 229 | `path` | `path_arguments[0]` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| 234 | `(path, keyword)` | `path_arguments` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 238 | `result` | `search_project(path, keyword)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 253 | `(path, keyword)` | `path_arguments` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 257 | `result` | `search_file(path, keyword)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 272 | `parts` | `user_text.split(maxsplit=1)` | split得到的参数片段列表，须先检查数量。 |
| 273 | `model_config['model']` | `parts[1]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 279 | `stream_type` | `'on'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 281 | `stream_type` | `'off'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 286 | `parts` | `user_text.split(maxsplit=1)` | split得到的参数片段列表，须先检查数量。 |
| 287 | `mode` | `parts[1]` | 流式/审批等当前模式字符串。 |
| 289 | `model_config['stream']` | `True` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 292 | `model_config['stream']` | `False` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 300 | `result` | `list_skills()` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 307 | `status` | `'已启用' if skill['active'] else '未启用'` | UI提示或项目规则状态，非自动代表成功。 |
| 317 | `parts` | `user_text.split(maxsplit=3)` | split得到的参数片段列表，须先检查数量。 |
| 322 | `result` | `generate_skill(parts[2], parts[3])` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 327 | `name` | `user_text.split(maxsplit=1)[1]` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| 328 | `result` | `activate_skill(name)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 345 | `(action, _, rest)` | `argument.partition(' ')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 346 | `actions` | `{'open': 'open_page', 'read': 'read_page', 'click': 'click', 'fill': 'fill', 'wait': 'wait_text', 'screenshot': 'screenshot', 'clo…（见完整源码）` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 352 | `args` | `{'url': rest.strip()}` | 解析启动参数Namespace或工具参数字典，按来源区分。 |
| 354 | `args` | `{'ref': rest.strip()}` | 解析启动参数Namespace或工具参数字典，按来源区分。 |
| 356 | `(ref, value)` | `rest.split(' ', 1)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 357 | `args` | `{'ref': ref, 'value': value}` | 解析启动参数Namespace或工具参数字典，按来源区分。 |
| 359 | `args` | `{'text': rest}` | 解析启动参数Namespace或工具参数字典，按来源区分。 |
| 363 | `args` | `{}` | 解析启动参数Namespace或工具参数字典，按来源区分。 |
| 364 | `connected` | `mcp_manager.connect('browser')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 369 | `result` | `execute_tool('mcp__browser__' + actions[action], args, source='user')` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 376 | `names` | `mcp_manager.tool_names()` | 合法会话/工具/附件名称集合，具体看返回结构。 |
| 385 | `result` | `mcp_manager.refresh(name)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 401 | `arguments` | `{'argv': shlex.split(argument)}` | 外部或模型提交的工具参数，必须经schema检查。 |
| 402 | `name` | `'start_pty'` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| 404 | `(name, arguments)` | `('spawn_agent', {'task': argument})` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 406 | `(identifier, proposal)` | `argument.split()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 407 | `(name, arguments)` | `('apply_agent_proposal', {'task_id': identifier, 'proposal_id': proposal})` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 409 | `(name, arguments)` | `('task_status', {'task_id': argument.strip()})` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 411 | `(name, arguments)` | `('task_cancel', {'task_id': argument.strip()})` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 413 | `(identifier, text)` | `argument.split(' ', 1)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 414 | `(name, arguments)` | `('task_input', {'task_id': identifier, 'text': text + '\n'})` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 415 | `result` | `execute_tool(name, arguments, source='user')` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 425 | `message` | `{'role': 'user', 'content': user_text}` | 单条聊天/协议消息字典；角色和字段随当前分支而定。 |
| 432 | `output` | `ConsoleOutput()` | ConsoleOutput对象、缓冲或UI输出接口，具体按签名位置。 |
| 433 | `reply` | `run_agent(messages, output=output)` | 模型最终文字或明确终止说明。 |
| 448 | `message` | `{'role': 'assistant', 'content': reply}` | 单条聊天/协议消息字典；角色和字段随当前分支而定。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 58 | 函数体 | 计算表达式/调用产生动作：`clear_skills()`。 |
| 59 | 函数体 | 将 `SessionManager()` 赋给 `session_manager`。 |
| 60 | 函数体 | 将 `None` 赋给 `initial_messages`。 |
| 61 | 函数体 | 条件 `initial_session`：真时执行body，假时进入else/后续。 |
| 62 | 函数体 / 条件为真 | 将 `session_manager.switch(initial_session)` 赋给 `result`。 |
| 63 | 函数体 / 条件为真 | 条件 `not result['ok']`：真时执行body，假时进入else/后续。 |
| 64 | 函数体 / 条件为真 / 条件为真 | 抛出 `ValueError(result['error'])`。 |
| 65 | 函数体 / 条件为真 | 将 `result['messages']` 赋给 `initial_messages`。 |
| 66 | 函数体 | 将 `TerminalInput(plain=plain)` 赋给 `terminal`。 |
| 67 | 函数体 | 计算表达式/调用产生动作：`print('Local AI CLI \| 直接描述任务，/help 查看命令')`。 |
| 68 | 函数体 | 在此处导入依赖：`from permissions import PROJECT_ROOT`；局部导入可延迟加载或避免循环。 |
| 69 | 函数体 | 计算表达式/调用产生动作：`print('工作目录:', PROJECT_ROOT)`。 |
| 70 | 函数体 | 在此处导入依赖：`from config import approval_config`；局部导入可延迟加载或避免循环。 |
| 71 | 函数体 | 计算表达式/调用产生动作：`print('审批模式:', approval_config['mode'])`。 |
| 72 | 函数体 | 条件 `terminal.session is not None`：真时执行body，假时进入else/后续。 |
| 73 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`print('Enter 发送 \| Alt+Enter 换行 \| Tab 补全')`。 |
| 74 | 函数体 | 将 `load_project_instructions()` 赋给 `instruction_result`。 |
| 75 | 函数体 | 计算表达式/调用产生动作：`print(instruction_result['message'])`。 |
| 76 | 函数体 | 进入资源/状态范围：`terminal.confirmations()`, `MCPManager()` 绑定 `mcp_manager`；退出执行清理。 |
| 77 | 函数体 / with范围 | 遍历 `({} if no_mcp else mcp_manager.load_configured()).items()`，每次绑定 `(name, result)`。 |
| 78 | 函数体 / with范围 / 循环每次 | 条件 `result['ok']`：真时执行body，假时进入else/后续。 |
| 79 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('MCP 已加载:', name)`。 |
| 81 | 函数体 / with范围 / 循环每次 / 条件为假/elif | 计算表达式/调用产生动作：`print('MCP 加载失败:', name, result['error'])`。 |
| 82 | 函数体 / with范围 | 将 `load_history() if initial_messages is None else initial_messages` 赋给 `messages`。 |
| 84 | 函数体 / with范围 | 循环检查 `True`，break/return/异常可结束。 |
| 85 | 函数体 / with范围 / 循环每次 | 将 `terminal.read(session_manager.current_name).strip()` 赋给 `user_text`。 |
| 87 | 函数体 / with范围 / 循环每次 | 条件 `user_text in ('/files', '/browse')`：真时执行body，假时进入else/后续。 |
| 88 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `user_text == '/files'`：真时执行body，假时进入else/后续。 |
| 89 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 将 `terminal.pick_files()` 赋给 `selected`。 |
| 91 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif | 将 `terminal.pick_file()` 赋给 `path`。 |
| 92 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif | 将 `[path] if path is not None else None` 赋给 `selected`。 |
| 93 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `selected`：真时执行body，假时进入else/后续。 |
| 94 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`attach_files(selected, messages)`。 |
| 95 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 97 | 函数体 / with范围 / 循环每次 | 将 `None` 赋给 `path_arguments`。 |
| 98 | 函数体 / with范围 / 循环每次 | 将 `user_text.partition(' ')` 赋给 `(command, separator, argument)`。 |
| 99 | 函数体 / with范围 / 循环每次 | 条件 `command in ('/read', '/attach', '/search', '/grep')`：真时执行body，假时进入else/后续。 |
| 100 | 函数体 / with范围 / 循环每次 / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 101 | 函数体 / with范围 / 循环每次 / 条件为真 / try | 将 `parse_path_arguments(argument)` 赋给 `path_arguments`。 |
| 102 | 函数体 / with范围 / 循环每次 / 条件为真 / try | 条件 `command in ('/read', '/attach') and path_arguments[1]`：真时执行body，假时进入else/后续。 |
| 103 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为真 | 抛出 `ValueError('路径含空格时请使用引号；此命令只接受一个路径')`。 |
| 104 | 函数体 / with范围 / 循环每次 / 条件为真 | except ValueError as error：只处理匹配类型的异常。 |
| 105 | 函数体 / with范围 / 循环每次 / 条件为真 / except ValueError as error | 计算表达式/调用产生动作：`print(error)`。 |
| 106 | 函数体 / with范围 / 循环每次 / 条件为真 / except ValueError as error | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 108 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/exit'`：真时执行body，假时进入else/后续。 |
| 109 | 函数体 / with范围 / 循环每次 / 条件为真 | break结束最近一层循环。 |
| 111 | 函数体 / with范围 / 循环每次 | 条件 `user_text == ''`：真时执行body，假时进入else/后续。 |
| 112 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 114 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/help'`：真时执行body，假时进入else/后续。 |
| 115 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`show_help()`。 |
| 116 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 118 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/history'`：真时执行body，假时进入else/后续。 |
| 119 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`show_history(messages)`。 |
| 120 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 122 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/clear'`：真时执行body，假时进入else/后续。 |
| 123 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`clear_history()`。 |
| 124 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`messages.clear()`。 |
| 125 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('assistant: messages cleared')`。 |
| 126 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 128 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/save'`：真时执行body，假时进入else/后续。 |
| 129 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `session_manager.export(messages)` 赋给 `result`。 |
| 130 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('已导出: ' + result['path'] if result['ok'] else result['error'])`。 |
| 131 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 133 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/sessions'`：真时执行body，假时进入else/后续。 |
| 134 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `session_manager.list_sessions()` 赋给 `result`。 |
| 135 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `not result['ok']`：真时执行body，假时进入else/后续。 |
| 136 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print(result['error'])`。 |
| 138 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif | 遍历 `result['names']`，每次绑定 `name`。 |
| 139 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 循环每次 | 将 `' (当前)' if name == session_manager.current_name else ''` 赋给 `marker`。 |
| 140 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 循环每次 | 计算表达式/调用产生动作：`print(name + marker)`。 |
| 141 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 143 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/session'`：真时执行body，假时进入else/后续。 |
| 144 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('当前会话:', session_manager.current_name)`。 |
| 145 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('用法: /session <名称>，不存在时创建')`。 |
| 146 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 148 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/session rename' or user_text.startswith('/session rename ')`：真时执行body，假时进入else/后续。 |
| 149 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `user_text.split(maxsplit=2)` 赋给 `parts`。 |
| 150 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `len(parts) != 3`：真时执行body，假时进入else/后续。 |
| 151 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print('用法: /session rename <新名称>')`。 |
| 152 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 153 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `session_manager.rename(parts[2])` 赋给 `result`。 |
| 154 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print(result['message'] if result['ok'] else result['error'])`。 |
| 155 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 157 | 函数体 / with范围 / 循环每次 | 条件 `user_text.startswith('/session ')`：真时执行body，假时进入else/后续。 |
| 158 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `user_text.split(maxsplit=1)[1]` 赋给 `name`。 |
| 159 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `session_manager.switch(name)` 赋给 `result`。 |
| 160 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `result['ok']`：真时执行body，假时进入else/后续。 |
| 161 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 将 `result['messages']` 赋给 `messages`。 |
| 162 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print('已切换会话:', name, '消息数:', len(messages))`。 |
| 164 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif | 计算表达式/调用产生动作：`print(result['error'])`。 |
| 165 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 167 | 函数体 / with范围 / 循环每次 | 条件 `command == '/approval'`：真时执行body，假时进入else/后续。 |
| 168 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `argument.strip()` 赋给 `mode`。 |
| 169 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `not mode`：真时执行body，假时进入else/后续。 |
| 170 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print('当前审批模式:', approval_config['mode'])`。 |
| 171 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif | 条件 `mode in ('auto', 'manual')`：真时执行body，假时进入else/后续。 |
| 172 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 条件为真 | 将 `mode` 赋给 `approval_config['mode']`。 |
| 173 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 条件为真 | 计算表达式/调用产生动作：`print('审批模式已切换:', mode)`。 |
| 175 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 条件为假/elif | 计算表达式/调用产生动作：`print('用法: /approval [auto\|manual]')`。 |
| 176 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 178 | 函数体 / with范围 / 循环每次 | 条件 `command == '/compact'`：真时执行body，假时进入else/后续。 |
| 179 | 函数体 / with范围 / 循环每次 / 条件为真 | 在此处导入依赖：`from config import context_config`；局部导入可延迟加载或避免循环。 |
| 180 | 函数体 / with范围 / 循环每次 / 条件为真 | 在此处导入依赖：`from compaction import compact_messages, context_view`；局部导入可延迟加载或避免循环。 |
| 181 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `argument.strip()` 赋给 `option`。 |
| 182 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `option in ('auto on', 'auto off')`：真时执行body，假时进入else/后续。 |
| 183 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 将 `option == 'auto on'` 赋给 `context_config['auto_compact']`。 |
| 184 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print('自动压缩:', 'on' if context_config['auto_compact'] else 'off')`。 |
| 185 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif | 条件 `option == 'status'`：真时执行body，假时进入else/后续。 |
| 186 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 条件为真 | 将 `context_view(messages)` 赋给 `view`。 |
| 187 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 条件为真 | 计算表达式/调用产生动作：`print('自动压缩:', context_config['auto_compact'], '摘要字符:', len(view['summary']), '已摘要消息:', view['covered'])`。 |
| 188 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 条件为假/elif | 条件 `not option`：真时执行body，假时进入else/后续。 |
| 189 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 条件为假/elif / 条件为真 | 将 `compact_messages(messages)` 赋给 `result`。 |
| 190 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 条件为假/elif / 条件为真 | 计算表达式/调用产生动作：`print(result['message'] if result['ok'] else result['error'])`。 |
| 192 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 条件为假/elif / 条件为假/elif | 计算表达式/调用产生动作：`print('用法: /compact，/compact status，/compact auto on\|off')`。 |
| 193 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 195 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/context'`：真时执行body，假时进入else/后续。 |
| 196 | 函数体 / with范围 / 循环每次 / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 197 | 函数体 / with范围 / 循环每次 / 条件为真 / try | 将 `prepare_context(messages, get_tool_definitions())` 赋给 `context`。 |
| 198 | 函数体 / with范围 / 循环每次 / 条件为真 / try | 计算表达式/调用产生动作：`print('请求字符预算:', context['chars'], '/', context['budget'])`。 |
| 199 | 函数体 / with范围 / 循环每次 / 条件为真 / try | 计算表达式/调用产生动作：`print('发送用户轮次:', context['sent_turns'], '/', context['total_turns'])`。 |
| 200 | 函数体 / with范围 / 循环每次 / 条件为真 / try | 计算表达式/调用产生动作：`print('省略历史消息:', context['omitted_messages'])`。 |
| 201 | 函数体 / with范围 / 循环每次 / 条件为真 / try | 计算表达式/调用产生动作：`print('已摘要消息:', context['summarized_messages'], '摘要字符:', context['summary_chars'])`。 |
| 202 | 函数体 / with范围 / 循环每次 / 条件为真 | except ContextBudgetError as error：只处理匹配类型的异常。 |
| 203 | 函数体 / with范围 / 循环每次 / 条件为真 / except ContextBudgetError as error | 计算表达式/调用产生动作：`print('上下文超限或无效:', error)`。 |
| 204 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 206 | 函数体 / with范围 / 循环每次 | 条件 `user_text == ''`：真时执行body，假时进入else/后续。 |
| 207 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 209 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/model'`：真时执行body，假时进入else/后续。 |
| 210 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('current model:' + model_config['model'])`。 |
| 211 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 213 | 函数体 / with范围 / 循环每次 | 条件 `user_text.startswith('/read ')`：真时执行body，假时进入else/后续。 |
| 214 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `path_arguments[0]` 赋给 `path`。 |
| 215 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `read_file(path)` 赋给 `result`。 |
| 217 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `not result['ok']`：真时执行body，假时进入else/后续。 |
| 218 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print(result['error'])`。 |
| 219 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 221 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `result['content']` 赋给 `content`。 |
| 222 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `1` 赋给 `line_number`。 |
| 223 | 函数体 / with范围 / 循环每次 / 条件为真 | 遍历 `content.splitlines()`，每次绑定 `line`。 |
| 224 | 函数体 / with范围 / 循环每次 / 条件为真 / 循环每次 | 计算表达式/调用产生动作：`print(line_number, ':', line)`。 |
| 225 | 函数体 / with范围 / 循环每次 / 条件为真 / 循环每次 | 更新已有变量：`line_number += 1`。 |
| 226 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 228 | 函数体 / with范围 / 循环每次 | 条件 `user_text.startswith('/attach ')`：真时执行body，假时进入else/后续。 |
| 229 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `path_arguments[0]` 赋给 `path`。 |
| 230 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`attach_files([path], messages)`。 |
| 231 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 233 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/grep' or user_text.startswith('/grep ')`：真时执行body，假时进入else/后续。 |
| 234 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `path_arguments` 赋给 `(path, keyword)`。 |
| 235 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `not keyword`：真时执行body，假时进入else/后续。 |
| 236 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print('用法: /grep <目录> <关键词>，例如 /grep . run_agent')`。 |
| 237 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 238 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `search_project(path, keyword)` 赋给 `result`。 |
| 239 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `not result['ok']`：真时执行body，假时进入else/后续。 |
| 240 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print(result['error'])`。 |
| 241 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 242 | 函数体 / with范围 / 循环每次 / 条件为真 | 遍历 `result['matches']`，每次绑定 `match`。 |
| 243 | 函数体 / with范围 / 循环每次 / 条件为真 / 循环每次 | 计算表达式/调用产生动作：`print(match['path'] + ':' + str(match['line_number']) + ': ' + match['content'])`。 |
| 244 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('扫描文件:', result['files_scanned'], '匹配行:', len(result['matches']))`。 |
| 245 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `result['truncated']`：真时执行body，假时进入else/后续。 |
| 246 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print('搜索结果不完整:', result['limit_reason'])`。 |
| 247 | 函数体 / with范围 / 循环每次 / 条件为真 | 遍历 `result['warnings']`，每次绑定 `warning`。 |
| 248 | 函数体 / with范围 / 循环每次 / 条件为真 / 循环每次 | 计算表达式/调用产生动作：`print('搜索警告:', warning)`。 |
| 249 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('跳过统计:', result['skipped'])`。 |
| 250 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 252 | 函数体 / with范围 / 循环每次 | 条件 `user_text.startswith('/search ')`：真时执行body，假时进入else/后续。 |
| 253 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `path_arguments` 赋给 `(path, keyword)`。 |
| 254 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `not keyword`：真时执行body，假时进入else/后续。 |
| 255 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print('/search + path + keyword')`。 |
| 256 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 257 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `search_file(path, keyword)` 赋给 `result`。 |
| 258 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `not result['ok']`：真时执行body，假时进入else/后续。 |
| 259 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print(result['error'])`。 |
| 260 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 261 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `result['matches'] == []`：真时执行body，假时进入else/后续。 |
| 262 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print('no matches')`。 |
| 263 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 264 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('found matches')`。 |
| 265 | 函数体 / with范围 / 循环每次 / 条件为真 | 遍历 `result['matches']`，每次绑定 `match`。 |
| 266 | 函数体 / with范围 / 循环每次 / 条件为真 / 循环每次 | 计算表达式/调用产生动作：`print(match['line_number'], ':', match['content'])`。 |
| 267 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 271 | 函数体 / with范围 / 循环每次 | 条件 `user_text.startswith('/model ')`：真时执行body，假时进入else/后续。 |
| 272 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `user_text.split(maxsplit=1)` 赋给 `parts`。 |
| 273 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `parts[1]` 赋给 `model_config['model']`。 |
| 274 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('model has switched to ' + model_config['model'])`。 |
| 275 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 277 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/stream'`：真时执行body，假时进入else/后续。 |
| 278 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `model_config['stream']`：真时执行body，假时进入else/后续。 |
| 279 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 将 `'on'` 赋给 `stream_type`。 |
| 281 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif | 将 `'off'` 赋给 `stream_type`。 |
| 282 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('current stream type:' + stream_type)`。 |
| 283 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 285 | 函数体 / with范围 / 循环每次 | 条件 `user_text.startswith('/stream ')`：真时执行body，假时进入else/后续。 |
| 286 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `user_text.split(maxsplit=1)` 赋给 `parts`。 |
| 287 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `parts[1]` 赋给 `mode`。 |
| 288 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `mode == 'on'`：真时执行body，假时进入else/后续。 |
| 289 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 将 `True` 赋给 `model_config['stream']`。 |
| 290 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print('流式输出已开启')`。 |
| 291 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif | 条件 `mode == 'off'`：真时执行body，假时进入else/后续。 |
| 292 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 条件为真 | 将 `False` 赋给 `model_config['stream']`。 |
| 293 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 条件为真 | 计算表达式/调用产生动作：`print('流式输出已关闭')`。 |
| 295 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 条件为假/elif | 计算表达式/调用产生动作：`print('unknown mode')`。 |
| 297 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 299 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/skills'`：真时执行body，假时进入else/后续。 |
| 300 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `list_skills()` 赋给 `result`。 |
| 301 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `not result['ok']`：真时执行body，假时进入else/后续。 |
| 302 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print(result['error'])`。 |
| 303 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif | 条件 `not result['skills']`：真时执行body，假时进入else/后续。 |
| 304 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 条件为真 | 计算表达式/调用产生动作：`print('没有可用 Skill，请放入 skills/<名称>/SKILL.md')`。 |
| 306 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 条件为假/elif | 遍历 `result['skills']`，每次绑定 `skill`。 |
| 307 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 条件为假/elif / 循环每次 | 将 `'已启用' if skill['active'] else '未启用'` 赋给 `status`。 |
| 308 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif / 条件为假/elif / 循环每次 | 计算表达式/调用产生动作：`print(skill['name'] + ' (' + status + ')')`。 |
| 309 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 311 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/skill clear'`：真时执行body，假时进入else/后续。 |
| 312 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`clear_skills()`。 |
| 313 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('已停用所有 Skills')`。 |
| 314 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 316 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/skill generate' or user_text.startswith('/skill generate ')`：真时执行body，假时进入else/后续。 |
| 317 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `user_text.split(maxsplit=3)` 赋给 `parts`。 |
| 318 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `len(parts) != 4`：真时执行body，假时进入else/后续。 |
| 319 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print('用法: /skill generate <名称> <用途>')`。 |
| 320 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 321 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('正在生成 Skill 草稿...')`。 |
| 322 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `generate_skill(parts[2], parts[3])` 赋给 `result`。 |
| 323 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print(result['message'] if result['ok'] else result['error'])`。 |
| 324 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 326 | 函数体 / with范围 / 循环每次 | 条件 `user_text.startswith('/skill ')`：真时执行body，假时进入else/后续。 |
| 327 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `user_text.split(maxsplit=1)[1]` 赋给 `name`。 |
| 328 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `activate_skill(name)` 赋给 `result`。 |
| 329 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `result['ok']`：真时执行body，假时进入else/后续。 |
| 330 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print('已启用 Skill:', name)`。 |
| 332 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为假/elif | 计算表达式/调用产生动作：`print(result['error'])`。 |
| 333 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 335 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/instructions'`：真时执行body，假时进入else/后续。 |
| 336 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print(instruction_state['message'])`。 |
| 337 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `instruction_state['content']`：真时执行body，假时进入else/后续。 |
| 338 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print(instruction_state['content'])`。 |
| 339 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 341 | 函数体 / with范围 / 循环每次 | 条件 `command == '/browser'`：真时执行body，假时进入else/后续。 |
| 342 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `no_mcp`：真时执行body，假时进入else/后续。 |
| 343 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print('本次运行已通过 --no-mcp 禁用浏览器 MCP')`。 |
| 344 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 345 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `argument.partition(' ')` 赋给 `(action, _, rest)`。 |
| 346 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `{'open': 'open_page', 'read': 'read_page', 'click': 'click', 'fill': 'fill', 'wait': 'wait_text', 'screenshot': 'screenshot', 'close': 'close_browser'}` 赋给 `actions`。 |
| 348 | 函数体 / with范围 / 循环每次 / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 349 | 函数体 / with范围 / 循环每次 / 条件为真 / try | 条件 `action not in actions`：真时执行body，假时进入else/后续。 |
| 350 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为真 | 抛出 `ValueError()`。 |
| 351 | 函数体 / with范围 / 循环每次 / 条件为真 / try | 条件 `action == 'open'`：真时执行body，假时进入else/后续。 |
| 352 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为真 | 将 `{'url': rest.strip()}` 赋给 `args`。 |
| 353 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif | 条件 `action == 'click'`：真时执行body，假时进入else/后续。 |
| 354 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为真 | 将 `{'ref': rest.strip()}` 赋给 `args`。 |
| 355 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为假/elif | 条件 `action == 'fill'`：真时执行body，假时进入else/后续。 |
| 356 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为假/elif / 条件为真 | 将 `rest.split(' ', 1)` 赋给 `(ref, value)`。 |
| 357 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为假/elif / 条件为真 | 将 `{'ref': ref, 'value': value}` 赋给 `args`。 |
| 358 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为假/elif / 条件为假/elif | 条件 `action == 'wait'`：真时执行body，假时进入else/后续。 |
| 359 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为假/elif / 条件为假/elif / 条件为真 | 将 `{'text': rest}` 赋给 `args`。 |
| 361 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为假/elif / 条件为假/elif / 条件为假/elif | 条件 `rest.strip()`：真时执行body，假时进入else/后续。 |
| 362 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为假/elif / 条件为假/elif / 条件为假/elif / 条件为真 | 抛出 `ValueError()`。 |
| 363 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为假/elif / 条件为假/elif / 条件为假/elif | 将 `{}` 赋给 `args`。 |
| 364 | 函数体 / with范围 / 循环每次 / 条件为真 / try | 将 `mcp_manager.connect('browser')` 赋给 `connected`。 |
| 365 | 函数体 / with范围 / 循环每次 / 条件为真 / try | 条件 `not connected['ok']`：真时执行body，假时进入else/后续。 |
| 366 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为真 | 计算表达式/调用产生动作：`print(connected['error'])`。 |
| 367 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 368 | 函数体 / with范围 / 循环每次 / 条件为真 / try | 在此处导入依赖：`from tool_runtime import execute_tool`；局部导入可延迟加载或避免循环。 |
| 369 | 函数体 / with范围 / 循环每次 / 条件为真 / try | 将 `execute_tool('mcp__browser__' + actions[action], args, source='user')` 赋给 `result`。 |
| 370 | 函数体 / with范围 / 循环每次 / 条件为真 / try | 计算表达式/调用产生动作：`print(safe_text(json.dumps(result.get('structured_content') or result, ensure_ascii=False, indent=2)))`。 |
| 371 | 函数体 / with范围 / 循环每次 / 条件为真 | except ValueError：只处理匹配类型的异常。 |
| 372 | 函数体 / with范围 / 循环每次 / 条件为真 / except ValueError | 计算表达式/调用产生动作：`print('用法: /browser open <URL> \| read \| click <ref> \| fill <ref> <文字> \| wait <文字> \| screenshot \| close')`。 |
| 373 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 375 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/mcp tools'`：真时执行body，假时进入else/后续。 |
| 376 | 函数体 / with范围 / 循环每次 / 条件为真 | 将 `mcp_manager.tool_names()` 赋给 `names`。 |
| 377 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('可用 MCP 工具:', ', '.join(names) if names else '无')`。 |
| 378 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 380 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/mcp refresh'`：真时执行body，假时进入else/后续。 |
| 381 | 函数体 / with范围 / 循环每次 / 条件为真 | 条件 `no_mcp`：真时执行body，假时进入else/后续。 |
| 382 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print('本次运行已通过 --no-mcp 禁用 MCP')`。 |
| 383 | 函数体 / with范围 / 循环每次 / 条件为真 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 384 | 函数体 / with范围 / 循环每次 / 条件为真 | 遍历 `mcp_config`，每次绑定 `name`。 |
| 385 | 函数体 / with范围 / 循环每次 / 条件为真 / 循环每次 | 将 `mcp_manager.refresh(name)` 赋给 `result`。 |
| 386 | 函数体 / with范围 / 循环每次 / 条件为真 / 循环每次 | 条件 `result['ok']`：真时执行body，假时进入else/后续。 |
| 387 | 函数体 / with范围 / 循环每次 / 条件为真 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('MCP 已刷新:', name)`。 |
| 389 | 函数体 / with范围 / 循环每次 / 条件为真 / 循环每次 / 条件为假/elif | 计算表达式/调用产生动作：`print('MCP 刷新失败:', name, result['error'])`。 |
| 390 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 392 | 函数体 / with范围 / 循环每次 | 条件 `user_text == '/tasks'`：真时执行body，假时进入else/后续。 |
| 393 | 函数体 / with范围 / 循环每次 / 条件为真 | 在此处导入依赖：`from process_tasks import list_tasks`；局部导入可延迟加载或避免循环。 |
| 394 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print(safe_text(json.dumps(list_tasks(), ensure_ascii=False, indent=2)))`。 |
| 395 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 397 | 函数体 / with范围 / 循环每次 | 条件 `command in ('/pty', '/agent', '/task', '/send', '/cancel', '/apply')`：真时执行body，假时进入else/后续。 |
| 398 | 函数体 / with范围 / 循环每次 / 条件为真 | 在此处导入依赖：`from tool_runtime import execute_tool`；局部导入可延迟加载或避免循环。 |
| 399 | 函数体 / with范围 / 循环每次 / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 400 | 函数体 / with范围 / 循环每次 / 条件为真 / try | 条件 `command == '/pty'`：真时执行body，假时进入else/后续。 |
| 401 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为真 | 将 `{'argv': shlex.split(argument)}` 赋给 `arguments`。 |
| 402 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为真 | 将 `'start_pty'` 赋给 `name`。 |
| 403 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif | 条件 `command == '/agent'`：真时执行body，假时进入else/后续。 |
| 404 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为真 | 将 `('spawn_agent', {'task': argument})` 赋给 `(name, arguments)`。 |
| 405 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为假/elif | 条件 `command == '/apply'`：真时执行body，假时进入else/后续。 |
| 406 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为假/elif / 条件为真 | 将 `argument.split()` 赋给 `(identifier, proposal)`。 |
| 407 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为假/elif / 条件为真 | 将 `('apply_agent_proposal', {'task_id': identifier, 'proposal_id': proposal})` 赋给 `(name, arguments)`。 |
| 408 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为假/elif / 条件为假/elif | 条件 `command == '/task'`：真时执行body，假时进入else/后续。 |
| 409 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为假/elif / 条件为假/elif / 条件为真 | 将 `('task_status', {'task_id': argument.strip()})` 赋给 `(name, arguments)`。 |
| 410 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为假/elif / 条件为假/elif / 条件为假/elif | 条件 `command == '/cancel'`：真时执行body，假时进入else/后续。 |
| 411 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为假/elif / 条件为假/elif / 条件为假/elif / 条件为真 | 将 `('task_cancel', {'task_id': argument.strip()})` 赋给 `(name, arguments)`。 |
| 413 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为假/elif / 条件为假/elif / 条件为假/elif / 条件为假/elif | 将 `argument.split(' ', 1)` 赋给 `(identifier, text)`。 |
| 414 | 函数体 / with范围 / 循环每次 / 条件为真 / try / 条件为假/elif / 条件为假/elif / 条件为假/elif / 条件为假/elif / 条件为假/elif | 将 `('task_input', {'task_id': identifier, 'text': text + '\n'})` 赋给 `(name, arguments)`。 |
| 415 | 函数体 / with范围 / 循环每次 / 条件为真 / try | 将 `execute_tool(name, arguments, source='user')` 赋给 `result`。 |
| 416 | 函数体 / with范围 / 循环每次 / 条件为真 / try | 计算表达式/调用产生动作：`print(safe_text(json.dumps(result, ensure_ascii=False, indent=2)))`。 |
| 417 | 函数体 / with范围 / 循环每次 / 条件为真 | except ValueError：只处理匹配类型的异常。 |
| 418 | 函数体 / with范围 / 循环每次 / 条件为真 / except ValueError | 计算表达式/调用产生动作：`print('命令参数错误，请查看 /help')`。 |
| 419 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 421 | 函数体 / with范围 / 循环每次 | 条件 `user_text.startswith('/')`：真时执行body，假时进入else/后续。 |
| 422 | 函数体 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('unknown command: ' + user_text)`。 |
| 423 | 函数体 / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 425 | 函数体 / with范围 / 循环每次 | 将 `{'role': 'user', 'content': user_text}` 赋给 `message`。 |
| 428 | 函数体 / with范围 / 循环每次 | 计算表达式/调用产生动作：`messages.append(message)`。 |
| 429 | 函数体 / with范围 / 循环每次 | 计算表达式/调用产生动作：`append_message(message)`。 |
| 431 | 函数体 / with范围 / 循环每次 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 432 | 函数体 / with范围 / 循环每次 / try | 将 `ConsoleOutput()` 赋给 `output`。 |
| 433 | 函数体 / with范围 / 循环每次 / try | 将 `run_agent(messages, output=output)` 赋给 `reply`。 |
| 434 | 函数体 / with范围 / 循环每次 | except ModelResponseError as error：只处理匹配类型的异常。 |
| 435 | 函数体 / with范围 / 循环每次 / except ModelResponseError as error | 计算表达式/调用产生动作：`print('模型响应错误:', error)`。 |
| 436 | 函数体 / with范围 / 循环每次 / except ModelResponseError as error | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 437 | 函数体 / with范围 / 循环每次 | except urllib.error.HTTPError as error：只处理匹配类型的异常。 |
| 438 | 函数体 / with范围 / 循环每次 / except urllib.error.HTTPError as error | 计算表达式/调用产生动作：`print('service request failed:', error.code)`。 |
| 439 | 函数体 / with范围 / 循环每次 / except urllib.error.HTTPError as error | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 440 | 函数体 / with范围 / 循环每次 | except urllib.error.URLError as error：只处理匹配类型的异常。 |
| 441 | 函数体 / with范围 / 循环每次 / except urllib.error.URLError as error | 计算表达式/调用产生动作：`print('model request failed', error.reason)`。 |
| 442 | 函数体 / with范围 / 循环每次 / except urllib.error.URLError as error | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 443 | 函数体 / with范围 / 循环每次 | except TimeoutError：只处理匹配类型的异常。 |
| 444 | 函数体 / with范围 / 循环每次 / except TimeoutError | 计算表达式/调用产生动作：`print('model timeout 5/5, plz try again later')`。 |
| 445 | 函数体 / with范围 / 循环每次 / except TimeoutError | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 448 | 函数体 / with范围 / 循环每次 | 将 `{'role': 'assistant', 'content': reply}` 赋给 `message`。 |
| 449 | 函数体 / with范围 / 循环每次 | 计算表达式/调用产生动作：`messages.append(message)`。 |
| 450 | 函数体 / with范围 / 循环每次 | 计算表达式/调用产生动作：`append_message(message)`。 |
| 451 | 函数体 / with范围 / 循环每次 | 计算表达式/调用产生动作：`output.final(reply)`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- with/yield：资源/状态生命周期或逐个生成：L49, L76。
- try/except/finally：异常与保证清理：L51, L100, L196, L348, L399, L431, L455。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | import json
0002 | import shlex
0003 | import urllib.error
0004 | from tools import search_file, search_project, get_tool_definitions
0005 | from tools import read_file
0006 | from config import model_config
0007 | from agent import run_agent
0008 | from permissions import resolve_project_path
0009 | from history import clear_history, load_history, append_message
0010 | from mcp_manager import MCPManager
0011 | from config import mcp_config
0012 | from project_instructions import load_project_instructions, instruction_state
0013 | from skills import activate_skill, clear_skills, list_skills
0014 | from skill_generation import generate_skill
0015 | from sessions import SessionManager
0016 | from context_window import ContextBudgetError, prepare_context
0017 | from console_output import ConsoleOutput
0018 | from streaming import ModelResponseError
0019 | from command_help import show_help
0020 | from terminal_input import TerminalInput
0021 | from path_input import parse_path_arguments
0022 | from contextlib import nullcontext
0023 | from attachments import prepare_attachments
0024 | from tool_display import safe_text
0025 | 
0026 | 
0027 | def show_history(messages):
0028 |     if not messages:
0029 |         print("there's no messages")
0030 |     else:
0031 |         for message in messages:
0032 |             print(message['role'] + ": " + message['content'])
0033 | 
0034 | 
0035 | def attach_files(paths, messages):
0036 |     result = prepare_attachments(paths)
0037 |     if not result['ok']:
0038 |         print(safe_text(result['error']))
0039 |         return
0040 |     append_message(result['message'])
0041 |     messages.append(result['message'])
0042 |     print('已添加附件:', safe_text(', '.join(result['paths'])))
0043 | 
0044 | 
0045 | 
0046 | def main(*, initial_session=None, plain=False, no_mcp=False, workspace=None):
0047 |     from workspace import use_workspace
0048 |     context = use_workspace(workspace) if workspace is not None else nullcontext()
0049 |     with context:
0050 |         from process_tasks import close_tasks
0051 |         try:
0052 |             return _main(initial_session=initial_session, plain=plain, no_mcp=no_mcp)
0053 |         finally:
0054 |             close_tasks()
0055 | 
0056 | 
0057 | def _main(*, initial_session=None, plain=False, no_mcp=False):
0058 |     clear_skills()
0059 |     session_manager = SessionManager()
0060 |     initial_messages = None
0061 |     if initial_session:
0062 |         result = session_manager.switch(initial_session)
0063 |         if not result['ok']:
0064 |             raise ValueError(result['error'])
0065 |         initial_messages = result['messages']
0066 |     terminal = TerminalInput(plain=plain)
0067 |     print('Local AI CLI | 直接描述任务，/help 查看命令')
0068 |     from permissions import PROJECT_ROOT
0069 |     print('工作目录:', PROJECT_ROOT)
0070 |     from config import approval_config
0071 |     print('审批模式:', approval_config['mode'])
0072 |     if terminal.session is not None:
0073 |         print('Enter 发送 | Alt+Enter 换行 | Tab 补全')
0074 |     instruction_result = load_project_instructions()
0075 |     print(instruction_result['message'])
0076 |     with terminal.confirmations(), MCPManager() as mcp_manager:
0077 |         for name, result in ({} if no_mcp else mcp_manager.load_configured()).items():
0078 |             if result['ok']:
0079 |                 print('MCP 已加载:', name)
0080 |             else:
0081 |                 print('MCP 加载失败:', name, result['error'])
0082 |         messages = load_history() if initial_messages is None else initial_messages
0083 | 
0084 |         while True:
0085 |             user_text = terminal.read(session_manager.current_name).strip()
0086 | 
0087 |             if user_text in ('/files', '/browse'):
0088 |                 if user_text == '/files':
0089 |                     selected = terminal.pick_files()
0090 |                 else:
0091 |                     path = terminal.pick_file()
0092 |                     selected = [path] if path is not None else None
0093 |                 if selected:
0094 |                     attach_files(selected, messages)
0095 |                 continue
0096 | 
0097 |             path_arguments = None
0098 |             command, separator, argument = user_text.partition(' ')
0099 |             if command in ('/read', '/attach', '/search', '/grep'):
0100 |                 try:
0101 |                     path_arguments = parse_path_arguments(argument)
0102 |                     if command in ('/read', '/attach') and path_arguments[1]:
0103 |                         raise ValueError('路径含空格时请使用引号；此命令只接受一个路径')
0104 |                 except ValueError as error:
0105 |                     print(error)
0106 |                     continue
0107 | 
0108 |             if user_text == "/exit":
0109 |                 break
0110 | 
0111 |             if user_text == "":
0112 |                 continue
0113 | 
0114 |             if user_text == '/help':
0115 |                 show_help()
0116 |                 continue
0117 | 
0118 |             if user_text == '/history':
0119 |                 show_history(messages)
0120 |                 continue
0121 | 
0122 |             if user_text == '/clear':
0123 |                 clear_history()
0124 |                 messages.clear()
0125 |                 print("assistant: messages cleared")
0126 |                 continue
0127 | 
0128 |             if user_text == '/save':
0129 |                 result = session_manager.export(messages)
0130 |                 print('已导出: ' + result['path'] if result['ok'] else result['error'])
0131 |                 continue
0132 | 
0133 |             if user_text == '/sessions':
0134 |                 result = session_manager.list_sessions()
0135 |                 if not result['ok']:
0136 |                     print(result['error'])
0137 |                 else:
0138 |                     for name in result['names']:
0139 |                         marker = ' (当前)' if name == session_manager.current_name else ''
0140 |                         print(name + marker)
0141 |                 continue
0142 | 
0143 |             if user_text == '/session':
0144 |                 print('当前会话:', session_manager.current_name)
0145 |                 print('用法: /session <名称>，不存在时创建')
0146 |                 continue
0147 | 
0148 |             if user_text == '/session rename' or user_text.startswith('/session rename '):
0149 |                 parts = user_text.split(maxsplit=2)
0150 |                 if len(parts) != 3:
0151 |                     print('用法: /session rename <新名称>')
0152 |                     continue
0153 |                 result = session_manager.rename(parts[2])
0154 |                 print(result['message'] if result['ok'] else result['error'])
0155 |                 continue
0156 | 
0157 |             if user_text.startswith('/session '):
0158 |                 name = user_text.split(maxsplit=1)[1]
0159 |                 result = session_manager.switch(name)
0160 |                 if result['ok']:
0161 |                     messages = result['messages']
0162 |                     print('已切换会话:', name, '消息数:', len(messages))
0163 |                 else:
0164 |                     print(result['error'])
0165 |                 continue
0166 | 
0167 |             if command == '/approval':
0168 |                 mode = argument.strip()
0169 |                 if not mode:
0170 |                     print('当前审批模式:', approval_config['mode'])
0171 |                 elif mode in ('auto', 'manual'):
0172 |                     approval_config['mode'] = mode
0173 |                     print('审批模式已切换:', mode)
0174 |                 else:
0175 |                     print('用法: /approval [auto|manual]')
0176 |                 continue
0177 | 
0178 |             if command == '/compact':
0179 |                 from config import context_config
0180 |                 from compaction import compact_messages, context_view
0181 |                 option = argument.strip()
0182 |                 if option in ('auto on', 'auto off'):
0183 |                     context_config['auto_compact'] = option == 'auto on'
0184 |                     print('自动压缩:', 'on' if context_config['auto_compact'] else 'off')
0185 |                 elif option == 'status':
0186 |                     view = context_view(messages)
0187 |                     print('自动压缩:', context_config['auto_compact'], '摘要字符:', len(view['summary']), '已摘要消息:', view['covered'])
0188 |                 elif not option:
0189 |                     result = compact_messages(messages)
0190 |                     print(result['message'] if result['ok'] else result['error'])
0191 |                 else:
0192 |                     print('用法: /compact，/compact status，/compact auto on|off')
0193 |                 continue
0194 | 
0195 |             if user_text == '/context':
0196 |                 try:
0197 |                     context = prepare_context(messages, get_tool_definitions())
0198 |                     print('请求字符预算:', context['chars'], '/', context['budget'])
0199 |                     print('发送用户轮次:', context['sent_turns'], '/', context['total_turns'])
0200 |                     print('省略历史消息:', context['omitted_messages'])
0201 |                     print('已摘要消息:', context['summarized_messages'], '摘要字符:', context['summary_chars'])
0202 |                 except ContextBudgetError as error:
0203 |                     print('上下文超限或无效:', error)
0204 |                 continue
0205 | 
0206 |             if user_text == '':
0207 |                 continue
0208 | 
0209 |             if user_text == '/model':
0210 |                 print('current model:'+ model_config['model'])
0211 |                 continue
0212 | 
0213 |             if user_text.startswith('/read '):
0214 |                 path = path_arguments[0]
0215 |                 result = read_file(path)
0216 | 
0217 |                 if not result['ok']:
0218 |                     print(result['error'])
0219 |                     continue
0220 | 
0221 |                 content = result['content']
0222 |                 line_number =1
0223 |                 for line in content.splitlines():
0224 |                     print(line_number,':', line)
0225 |                     line_number +=1
0226 |                 continue
0227 | 
0228 |             if user_text.startswith('/attach '):
0229 |                 path = path_arguments[0]
0230 |                 attach_files([path], messages)
0231 |                 continue
0232 | 
0233 |             if user_text == '/grep' or user_text.startswith('/grep '):
0234 |                 path, keyword = path_arguments
0235 |                 if not keyword:
0236 |                     print('用法: /grep <目录> <关键词>，例如 /grep . run_agent')
0237 |                     continue
0238 |                 result = search_project(path, keyword)
0239 |                 if not result['ok']:
0240 |                     print(result['error'])
0241 |                     continue
0242 |                 for match in result['matches']:
0243 |                     print(match['path'] + ':' + str(match['line_number']) + ': ' + match['content'])
0244 |                 print('扫描文件:', result['files_scanned'], '匹配行:', len(result['matches']))
0245 |                 if result['truncated']:
0246 |                     print('搜索结果不完整:', result['limit_reason'])
0247 |                 for warning in result['warnings']:
0248 |                     print('搜索警告:', warning)
0249 |                 print('跳过统计:', result['skipped'])
0250 |                 continue
0251 | 
0252 |             if user_text.startswith('/search '):
0253 |                 path, keyword = path_arguments
0254 |                 if not keyword:
0255 |                     print('/search + path + keyword')
0256 |                     continue
0257 |                 result = search_file(path, keyword)
0258 |                 if not result['ok']:
0259 |                     print(result['error'])
0260 |                     continue
0261 |                 if result['matches'] == []:
0262 |                     print('no matches')
0263 |                     continue
0264 |                 print('found matches')
0265 |                 for match in result['matches']:
0266 |                     print(match['line_number'],':', match['content'])
0267 |                 continue
0268 | 
0269 | 
0270 | 
0271 |             if user_text.startswith('/model '):
0272 |                 parts = user_text.split(maxsplit=1)
0273 |                 model_config['model'] = parts[1]
0274 |                 print('model has switched to ' + model_config['model'])
0275 |                 continue
0276 | 
0277 |             if user_text == '/stream':
0278 |                 if model_config['stream']:
0279 |                     stream_type = 'on'
0280 |                 else:
0281 |                     stream_type = 'off'
0282 |                 print('current stream type:'+ stream_type)
0283 |                 continue
0284 | 
0285 |             if user_text.startswith('/stream '):
0286 |                 parts = user_text.split(maxsplit=1)
0287 |                 mode = parts[1]
0288 |                 if mode == 'on':
0289 |                     model_config['stream'] = True
0290 |                     print('流式输出已开启')
0291 |                 elif mode == 'off':
0292 |                     model_config['stream'] = False
0293 |                     print('流式输出已关闭')
0294 |                 else:
0295 |                     print('unknown mode')
0296 | 
0297 |                 continue
0298 | 
0299 |             if user_text == '/skills':
0300 |                 result = list_skills()
0301 |                 if not result['ok']:
0302 |                     print(result['error'])
0303 |                 elif not result['skills']:
0304 |                     print('没有可用 Skill，请放入 skills/<名称>/SKILL.md')
0305 |                 else:
0306 |                     for skill in result['skills']:
0307 |                         status = '已启用' if skill['active'] else '未启用'
0308 |                         print(skill['name'] + ' (' + status + ')')
0309 |                 continue
0310 | 
0311 |             if user_text == '/skill clear':
0312 |                 clear_skills()
0313 |                 print('已停用所有 Skills')
0314 |                 continue
0315 | 
0316 |             if user_text == '/skill generate' or user_text.startswith('/skill generate '):
0317 |                 parts = user_text.split(maxsplit=3)
0318 |                 if len(parts) != 4:
0319 |                     print('用法: /skill generate <名称> <用途>')
0320 |                     continue
0321 |                 print('正在生成 Skill 草稿...')
0322 |                 result = generate_skill(parts[2], parts[3])
0323 |                 print(result['message'] if result['ok'] else result['error'])
0324 |                 continue
0325 | 
0326 |             if user_text.startswith('/skill '):
0327 |                 name = user_text.split(maxsplit=1)[1]
0328 |                 result = activate_skill(name)
0329 |                 if result['ok']:
0330 |                     print('已启用 Skill:', name)
0331 |                 else:
0332 |                     print(result['error'])
0333 |                 continue
0334 | 
0335 |             if user_text == '/instructions':
0336 |                 print(instruction_state['message'])
0337 |                 if instruction_state['content']:
0338 |                     print(instruction_state['content'])
0339 |                 continue
0340 | 
0341 |             if command == '/browser':
0342 |                 if no_mcp:
0343 |                     print('本次运行已通过 --no-mcp 禁用浏览器 MCP')
0344 |                     continue
0345 |                 action, _, rest = argument.partition(' ')
0346 |                 actions = {'open': 'open_page', 'read': 'read_page', 'click': 'click',
0347 |                            'fill': 'fill', 'wait': 'wait_text', 'screenshot': 'screenshot', 'close': 'close_browser'}
0348 |                 try:
0349 |                     if action not in actions:
0350 |                         raise ValueError()
0351 |                     if action == 'open':
0352 |                         args = {'url': rest.strip()}
0353 |                     elif action == 'click':
0354 |                         args = {'ref': rest.strip()}
0355 |                     elif action == 'fill':
0356 |                         ref, value = rest.split(' ', 1)
0357 |                         args = {'ref': ref, 'value': value}
0358 |                     elif action == 'wait':
0359 |                         args = {'text': rest}
0360 |                     else:
0361 |                         if rest.strip():
0362 |                             raise ValueError()
0363 |                         args = {}
0364 |                     connected = mcp_manager.connect('browser')
0365 |                     if not connected['ok']:
0366 |                         print(connected['error'])
0367 |                         continue
0368 |                     from tool_runtime import execute_tool
0369 |                     result = execute_tool('mcp__browser__' + actions[action], args, source='user')
0370 |                     print(safe_text(json.dumps(result.get('structured_content') or result, ensure_ascii=False, indent=2)))
0371 |                 except ValueError:
0372 |                     print('用法: /browser open <URL> | read | click <ref> | fill <ref> <文字> | wait <文字> | screenshot | close')
0373 |                 continue
0374 | 
0375 |             if user_text == '/mcp tools':
0376 |                 names = mcp_manager.tool_names()
0377 |                 print('可用 MCP 工具:', ', '.join(names) if names else '无')
0378 |                 continue
0379 | 
0380 |             if user_text == '/mcp refresh':
0381 |                 if no_mcp:
0382 |                     print('本次运行已通过 --no-mcp 禁用 MCP')
0383 |                     continue
0384 |                 for name in mcp_config:
0385 |                     result = mcp_manager.refresh(name)
0386 |                     if result['ok']:
0387 |                         print('MCP 已刷新:', name)
0388 |                     else:
0389 |                         print('MCP 刷新失败:', name, result['error'])
0390 |                 continue
0391 | 
0392 |             if user_text == '/tasks':
0393 |                 from process_tasks import list_tasks
0394 |                 print(safe_text(json.dumps(list_tasks(), ensure_ascii=False, indent=2)))
0395 |                 continue
0396 | 
0397 |             if command in ('/pty', '/agent', '/task', '/send', '/cancel', '/apply'):
0398 |                 from tool_runtime import execute_tool
0399 |                 try:
0400 |                     if command == '/pty':
0401 |                         arguments = {'argv': shlex.split(argument)}
0402 |                         name = 'start_pty'
0403 |                     elif command == '/agent':
0404 |                         name, arguments = 'spawn_agent', {'task': argument}
0405 |                     elif command == '/apply':
0406 |                         identifier, proposal = argument.split()
0407 |                         name, arguments = 'apply_agent_proposal', {'task_id': identifier, 'proposal_id': proposal}
0408 |                     elif command == '/task':
0409 |                         name, arguments = 'task_status', {'task_id': argument.strip()}
0410 |                     elif command == '/cancel':
0411 |                         name, arguments = 'task_cancel', {'task_id': argument.strip()}
0412 |                     else:
0413 |                         identifier, text = argument.split(' ', 1)
0414 |                         name, arguments = 'task_input', {'task_id': identifier, 'text': text + '\n'}
0415 |                     result = execute_tool(name, arguments, source='user')
0416 |                     print(safe_text(json.dumps(result, ensure_ascii=False, indent=2)))
0417 |                 except ValueError:
0418 |                     print('命令参数错误，请查看 /help')
0419 |                 continue
0420 | 
0421 |             if user_text.startswith('/') :
0422 |                 print('unknown command: ' + user_text)
0423 |                 continue
0424 | 
0425 |             message = {'role': 'user', 'content': user_text}
0426 | 
0427 | 
0428 |             messages.append(message)
0429 |             append_message(message)
0430 | 
0431 |             try:
0432 |                 output = ConsoleOutput()
0433 |                 reply = run_agent(messages, output=output)
0434 |             except ModelResponseError as error:
0435 |                 print('模型响应错误:', error)
0436 |                 continue
0437 |             except urllib.error.HTTPError as error:
0438 |                 print('service request failed:', error.code)
0439 |                 continue
0440 |             except urllib.error.URLError as error:
0441 |                 print('model request failed', error.reason)
0442 |                 continue
0443 |             except TimeoutError:
0444 |                 print('model timeout 5/5, plz try again later')
0445 |                 continue
0446 | 
0447 | 
0448 |             message = {'role': 'assistant', 'content': reply}
0449 |             messages.append(message)
0450 |             append_message(message)
0451 |             output.final(reply)
0452 | 
0453 | 
0454 | if __name__ == '__main__':
0455 |     try:
0456 |         main()
0457 |     except (EOFError, KeyboardInterrupt):
0458 |         print('\nCLI 已退出')
```
