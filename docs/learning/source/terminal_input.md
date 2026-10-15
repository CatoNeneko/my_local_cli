# terminal_input.py：源码导读

增强/普通输入适配、命令路径补全、按键、附件选择和确认上下文。

先读专题：[07-terminal.md](../07-terminal.md)。

实际源码：[terminal_input.py](../../../terminal_input.py)。

快照 SHA256：`0225174047c7cfbb438690a8e1659cf3a42ebd18e7dd0e18e2ad2365be2fd6a8`；173 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import sys` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `from contextlib import contextmanager` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `from contextvars import ContextVar` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `from command_help import COMMANDS` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `from config import model_config` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 9 | `from path_input import PATH_COMMANDS, path_candidates` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 10 | `from tool_display import safe_text` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 12 | `enhanced_confirmation = ContextVar('enhanced_confirmation', default=False)` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [request_confirmation](#request-confirmation) | [15](../../../terminal_input.py#L15) | 选当前增强面板或普通y/N输入，返回布尔。 |
| [create_completer](#create-completer) | [22](../../../terminal_input.py#L22) | 定义并创建项目命令/路径补全对象。 |
| [create_completer.ProjectCompleter.get_completions](#create-completer-projectcompleter-get-completions) | [26](../../../terminal_input.py#L26) | 命令补全或合法路径候选，yield Completion对象。 |
| [create_key_bindings](#create-key-bindings) | [53](../../../terminal_input.py#L53) | 定义Enter接受候选/提交与Alt+Enter换行回调。 |
| [create_key_bindings.submit](#create-key-bindings-submit) | [58](../../../terminal_input.py#L58) | Enter有候选先接受，否则提交当前buffer。 |
| [create_key_bindings.newline](#create-key-bindings-newline) | [67](../../../terminal_input.py#L67) | 向当前输入buffer插入换行。 |
| [TerminalInput.__init__](#terminalinput---init--) | [74](../../../terminal_input.py#L74) | 构造对象的初始状态；调用类创建对象时自动执行。 |
| [TerminalInput.confirmations](#terminalinput-confirmations) | [86](../../../terminal_input.py#L86) | 设置确认界面ContextVar并在退出恢复。 |
| [TerminalInput.pick_file](#terminalinput-pick-file) | [93](../../../terminal_input.py#L93) | 逐层选目录/单文件，返回项目路径。 |
| [TerminalInput.pick_files](#terminalinput-pick-files) | [136](../../../terminal_input.py#L136) | 面板实时模糊多选或普通编号选择。 |
| [TerminalInput.read](#terminalinput-read) | [166](../../../terminal_input.py#L166) | 普通input或PromptSession.prompt读取，动态toolbar显示当前配置。 |
| [TerminalInput.read.toolbar](#terminalinput-read-toolbar) | [170](../../../terminal_input.py#L170) | 动态显示当前会话、模型与流式配置。 |

<a id="request-confirmation"></a>
## request_confirmation

选当前增强面板或普通y/N输入，返回布尔。

```python
def request_confirmation(prompt)
```

位置：[15行](../../../terminal_input.py#L15) 至快照 19 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `prompt` | `未显式注解` | 发给用户或模型的说明文字；看请求接口区分。 |

**调用表达式（静态提取，不含内层独立函数体）**：`choose`、`enhanced_confirmation.get`、`input`、`input(safe_text(prompt) + '\n允许吗？[y/N] ').strip`、`input(safe_text(prompt) + '\n允许吗？[y/N] ').strip().lower`、`safe_text`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 16 | 函数体 | 条件 `enhanced_confirmation.get()`：真时执行body，假时进入else/后续。 |
| 17 | 函数体 / 条件为真 | 在此处导入依赖：`from terminal_dialog import choose`；局部导入可延迟加载或避免循环。 |
| 18 | 函数体 / 条件为真 | 返回 `choose(prompt, [(False, '拒绝（默认）'), (True, '允许本次操作')], yes_no=True) is True`，结束当前函数；具体分支见完整源码。 |
| 19 | 函数体 | 返回 `input(safe_text(prompt) + '\n允许吗？[y/N] ').strip().lower() == 'y'`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L18：`choose(prompt, [(False, '拒绝（默认）'), (True, '允许本次操作')], yes_no=True) is True`。
- L19：`input(safe_text(prompt) + '\n允许吗？[y/N] ').strip().lower() == 'y'`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="create-completer"></a>
## create_completer

定义并创建项目命令/路径补全对象。

```python
def create_completer()
```

位置：[22行](../../../terminal_input.py#L22) 至快照 50 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`ProjectCompleter`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 23 | 函数体 | 在此处导入依赖：`from prompt_toolkit.completion import Completer, Completion, WordCompleter`；局部导入可延迟加载或避免循环。 |
| 25 | 函数体 | 定义类 `ProjectCompleter`，保存方法与对象状态。 |
| 50 | 函数体 | 返回 `ProjectCompleter()`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L50：`ProjectCompleter()`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="create-completer-projectcompleter-get-completions"></a>
## create_completer.ProjectCompleter.get_completions

命令补全或合法路径候选，yield Completion对象。

```python
def get_completions(self, document, complete_event)
```

位置：[26行](../../../terminal_input.py#L26) 至快照 48 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `document` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `complete_event` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Completion`、`WordCompleter`、`WordCompleter(list(COMMANDS), sentence=True).get_completions`、`any`、`char.isspace`、`len`、`list`、`ord`、`path_candidates`、`safe_text`、`text.partition`、`typed.rpartition`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 27 | `text` | `document.text_before_cursor` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 28 | `(command, separator, argument)` | `text.partition(' ')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 33 | `quote` | `argument[:1] if argument[:1] in ('"', "'") else ''` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 34 | `typed` | `argument[1:] if quote else argument` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 37 | `(parent, _, prefix)` | `typed.rpartition('/')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 38 | `directory` | `parent + '/' if '/' in typed else '.'` | 当前目录路径，遍历/候选/会话使用。 |
| 39 | `(candidates, _)` | `path_candidates(directory, prefix, directories_only=command == '/grep')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 41 | `candidate` | `relative + ('/' if is_directory else '')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 43 | `delimiter` | `quote or ('"' if any((char.isspace() for char in candidate)) else '')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 46 | `replacement` | `delimiter + candidate + (delimiter if delimiter and (not is_directory) else '')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 27 | 函数体 | 将 `document.text_before_cursor` 赋给 `text`。 |
| 28 | 函数体 | 将 `text.partition(' ')` 赋给 `(command, separator, argument)`。 |
| 29 | 函数体 | 条件 `command not in PATH_COMMANDS or not separator`：真时执行body，假时进入else/后续。 |
| 30 | 函数体 / 条件为真 | yield让出值/控制权；上下文管理器中表示进入with内部代码。 |
| 31 | 函数体 / 条件为真 | 返回 `None`，结束当前函数；具体分支见完整源码。 |
| 33 | 函数体 | 将 `argument[:1] if argument[:1] in ('"', "'") else ''` 赋给 `quote`。 |
| 34 | 函数体 | 将 `argument[1:] if quote else argument` 赋给 `typed`。 |
| 35 | 函数体 | 条件 `quote and quote in typed or (not quote and any((char.isspace() for char in typed)))`：真时执行body，假时进入else/后续。 |
| 36 | 函数体 / 条件为真 | 返回 `None`，结束当前函数；具体分支见完整源码。 |
| 37 | 函数体 | 将 `typed.rpartition('/')` 赋给 `(parent, _, prefix)`。 |
| 38 | 函数体 | 将 `parent + '/' if '/' in typed else '.'` 赋给 `directory`。 |
| 39 | 函数体 | 将 `path_candidates(directory, prefix, directories_only=command == '/grep')` 赋给 `(candidates, _)`。 |
| 40 | 函数体 | 遍历 `candidates`，每次绑定 `(relative, is_directory)`。 |
| 41 | 函数体 / 循环每次 | 将 `relative + ('/' if is_directory else '')` 赋给 `candidate`。 |
| 43 | 函数体 / 循环每次 | 将 `quote or ('"' if any((char.isspace() for char in candidate)) else '')` 赋给 `delimiter`。 |
| 44 | 函数体 / 循环每次 | 条件 `'"' in candidate or "'" in candidate or any((ord(char) < 32 for char in candidate))`：真时执行body，假时进入else/后续。 |
| 45 | 函数体 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 46 | 函数体 / 循环每次 | 将 `delimiter + candidate + (delimiter if delimiter and (not is_directory) else '')` 赋给 `replacement`。 |
| 47 | 函数体 / 循环每次 | yield让出值/控制权；上下文管理器中表示进入with内部代码。 |

**实际返回分支**：

- L31：`None`。
- L36：`None`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="create-key-bindings"></a>
## create_key_bindings

定义Enter接受候选/提交与Alt+Enter换行回调。

```python
def create_key_bindings()
```

位置：[53行](../../../terminal_input.py#L53) 至快照 70 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`KeyBindings`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 55 | `bindings` | `KeyBindings()` | prompt-toolkit按键绑定集合。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 54 | 函数体 | 在此处导入依赖：`from prompt_toolkit.key_binding import KeyBindings`；局部导入可延迟加载或避免循环。 |
| 55 | 函数体 | 将 `KeyBindings()` 赋给 `bindings`。 |
| 58 | 函数体 | 定义嵌套函数 `submit`；定义本身不执行函数体。 |
| 67 | 函数体 | 定义嵌套函数 `newline`；定义本身不执行函数体。 |
| 70 | 函数体 | 返回 `bindings`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L70：`bindings`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="create-key-bindings-submit"></a>
## create_key_bindings.submit

Enter有候选先接受，否则提交当前buffer。

```python
def submit(event)
```

位置：[58行](../../../terminal_input.py#L58) 至快照 64 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `event` | `未显式注解` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |

**调用表达式（静态提取，不含内层独立函数体）**：`bindings.add`、`event.current_buffer.go_to_completion`、`event.current_buffer.validate_and_handle`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 62 | `event.current_buffer.complete_state` | `None` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 59 | 函数体 | 条件 `event.current_buffer.complete_state is not None`：真时执行body，假时进入else/后续。 |
| 60 | 函数体 / 条件为真 | 条件 `event.current_buffer.complete_state.current_completion is None`：真时执行body，假时进入else/后续。 |
| 61 | 函数体 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`event.current_buffer.go_to_completion(0)`。 |
| 62 | 函数体 / 条件为真 | 将 `None` 赋给 `event.current_buffer.complete_state`。 |
| 63 | 函数体 / 条件为真 | 返回 `None`，结束当前函数；具体分支见完整源码。 |
| 64 | 函数体 | 计算表达式/调用产生动作：`event.current_buffer.validate_and_handle()`。 |

**实际返回分支**：

- L63：`None`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="create-key-bindings-newline"></a>
## create_key_bindings.newline

向当前输入buffer插入换行。

```python
def newline(event)
```

位置：[67行](../../../terminal_input.py#L67) 至快照 68 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `event` | `未显式注解` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |

**调用表达式（静态提取，不含内层独立函数体）**：`bindings.add`、`event.current_buffer.insert_text`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 68 | 函数体 | 计算表达式/调用产生动作：`event.current_buffer.insert_text('\n')`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="terminalinput---init--"></a>
## TerminalInput.__init__

构造对象的初始状态；self上的字段会在后续方法中继续使用。

```python
def __init__(self, plain=False)
```

位置：[74行](../../../terminal_input.py#L74) 至快照 83 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `plain` | `未显式注解` | 强制普通input而非增强TTY。 |

**调用表达式（静态提取，不含内层独立函数体）**：`InMemoryHistory`、`PromptSession`、`create_completer`、`create_key_bindings`、`sys.stdin.isatty`、`sys.stdout.isatty`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 75 | `self.session` | `None` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 79 | `self.session` | `PromptSession(multiline=True, key_bindings=create_key_bindings(), completer=create_completer(), complete_while_typing=True, histor…（见完整源码）` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 75 | 函数体 | 将 `None` 赋给 `self.session`。 |
| 76 | 函数体 | 条件 `not plain and sys.stdin.isatty() and sys.stdout.isatty()`：真时执行body，假时进入else/后续。 |
| 77 | 函数体 / 条件为真 | 在此处导入依赖：`from prompt_toolkit import PromptSession`；局部导入可延迟加载或避免循环。 |
| 78 | 函数体 / 条件为真 | 在此处导入依赖：`from prompt_toolkit.history import InMemoryHistory`；局部导入可延迟加载或避免循环。 |
| 79 | 函数体 / 条件为真 | 将 `PromptSession(multiline=True, key_bindings=create_key_bindings(), completer=create_completer(), complete_while_typing=True, history=InMemoryHistory())` 赋给 `self.session`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="terminalinput-confirmations"></a>
## TerminalInput.confirmations

设置确认界面ContextVar并在退出恢复。

```python
def confirmations(self)
```

位置：[86行](../../../terminal_input.py#L86) 至快照 91 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：`enhanced_confirmation.reset`、`enhanced_confirmation.set`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 87 | `token` | `enhanced_confirmation.set(self.session is not None)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 87 | 函数体 | 将 `enhanced_confirmation.set(self.session is not None)` 赋给 `token`。 |
| 88 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 89 | 函数体 / try | yield让出值/控制权；上下文管理器中表示进入with内部代码。 |
| 91 | 函数体 / finally保证清理 | 计算表达式/调用产生动作：`enhanced_confirmation.reset(token)`。 |

**实际返回分支**：

- 这是生成器/上下文管理器式控制，含yield；不按普通return结果理解。

<a id="terminalinput-pick-file"></a>
## TerminalInput.pick_file

逐层选目录/单文件，返回项目路径。

```python
def pick_file(self)
```

位置：[93行](../../../terminal_input.py#L93) 至快照 134 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`answer.isdigit`、`choices.append`、`choices.extend`、`choose`、`enumerate`、`input`、`input('输入编号，留空取消: ').strip`、`int`、`len`、`path_candidates`、`permissions.resolve_project_path`、`print`、`safe_text`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 96 | `directory` | `'.'` | 当前目录路径，遍历/候选/会话使用。 |
| 98 | `(candidates, truncated)` | `path_candidates(directory)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 99 | `choices` | `[]` | 选择面板的(value,label)列表。 |
| 101 | `parent` | `str(Path(directory).parent)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 105 | `title` | `'选择附件 · ' + directory` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 112 | `selected` | `choose(title, choices)` | 界面高亮索引，某些主循环分支为选择结果；看当前层次。 |
| 117 | `answer` | `input('输入编号，留空取消: ').strip()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 123 | `selected` | `choices[int(answer) - 1][0]` | 界面高亮索引，某些主循环分支为选择结果；看当前层次。 |
| 126 | `(path, is_directory)` | `selected` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 127 | `checked` | `permissions.resolve_project_path(path)` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 132 | `directory` | `path` | 当前目录路径，遍历/候选/会话使用。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 94 | 函数体 | 在此处导入依赖：`import permissions`；局部导入可延迟加载或避免循环。 |
| 95 | 函数体 | 在此处导入依赖：`from terminal_dialog import choose`；局部导入可延迟加载或避免循环。 |
| 96 | 函数体 | 将 `'.'` 赋给 `directory`。 |
| 97 | 函数体 | 循环检查 `True`，break/return/异常可结束。 |
| 98 | 函数体 / 循环每次 | 将 `path_candidates(directory)` 赋给 `(candidates, truncated)`。 |
| 99 | 函数体 / 循环每次 | 将 `[]` 赋给 `choices`。 |
| 100 | 函数体 / 循环每次 | 条件 `directory != '.'`：真时执行body，假时进入else/后续。 |
| 101 | 函数体 / 循环每次 / 条件为真 | 将 `str(Path(directory).parent)` 赋给 `parent`。 |
| 102 | 函数体 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`choices.append(((parent, True), '../ 返回上一级'))`。 |
| 103 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`choices.extend((((path, is_directory), ('📁 ' if is_directory else '   ') + Path(path).name) for path, is_directory in candidates))`。 |
| 105 | 函数体 / 循环每次 | 将 `'选择附件 · ' + directory` 赋给 `title`。 |
| 106 | 函数体 / 循环每次 | 条件 `truncated`：真时执行body，假时进入else/后续。 |
| 107 | 函数体 / 循环每次 / 条件为真 | 更新已有变量：`title += '（候选已限制，请用路径补全定位其他文件）'`。 |
| 108 | 函数体 / 循环每次 | 条件 `not choices`：真时执行body，假时进入else/后续。 |
| 109 | 函数体 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('没有可选择的文件')`。 |
| 110 | 函数体 / 循环每次 / 条件为真 | 返回 `None`，结束当前函数；具体分支见完整源码。 |
| 111 | 函数体 / 循环每次 | 条件 `self.session is not None`：真时执行body，假时进入else/后续。 |
| 112 | 函数体 / 循环每次 / 条件为真 | 将 `choose(title, choices)` 赋给 `selected`。 |
| 114 | 函数体 / 循环每次 / 条件为假/elif | 计算表达式/调用产生动作：`print(title)`。 |
| 115 | 函数体 / 循环每次 / 条件为假/elif | 遍历 `enumerate(choices, 1)`，每次绑定 `(index, (_, label))`。 |
| 116 | 函数体 / 循环每次 / 条件为假/elif / 循环每次 | 计算表达式/调用产生动作：`print(str(index) + '. ' + safe_text(label))`。 |
| 117 | 函数体 / 循环每次 / 条件为假/elif | 将 `input('输入编号，留空取消: ').strip()` 赋给 `answer`。 |
| 118 | 函数体 / 循环每次 / 条件为假/elif | 条件 `not answer`：真时执行body，假时进入else/后续。 |
| 119 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 | 返回 `None`，结束当前函数；具体分支见完整源码。 |
| 120 | 函数体 / 循环每次 / 条件为假/elif | 条件 `not answer.isdigit() or not 1 <= int(answer) <= len(choices)`：真时执行body，假时进入else/后续。 |
| 121 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 | 计算表达式/调用产生动作：`print('无效编号')`。 |
| 122 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 123 | 函数体 / 循环每次 / 条件为假/elif | 将 `choices[int(answer) - 1][0]` 赋给 `selected`。 |
| 124 | 函数体 / 循环每次 | 条件 `selected is None`：真时执行body，假时进入else/后续。 |
| 125 | 函数体 / 循环每次 / 条件为真 | 返回 `None`，结束当前函数；具体分支见完整源码。 |
| 126 | 函数体 / 循环每次 | 将 `selected` 赋给 `(path, is_directory)`。 |
| 127 | 函数体 / 循环每次 | 将 `permissions.resolve_project_path(path)` 赋给 `checked`。 |
| 128 | 函数体 / 循环每次 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 129 | 函数体 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print(checked['error'])`。 |
| 130 | 函数体 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 131 | 函数体 / 循环每次 | 条件 `is_directory`：真时执行body，假时进入else/后续。 |
| 132 | 函数体 / 循环每次 / 条件为真 | 将 `path` 赋给 `directory`。 |
| 134 | 函数体 / 循环每次 / 条件为假/elif | 返回 `path`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L110：`None`。
- L119：`None`。
- L125：`None`。
- L134：`path`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="terminalinput-pick-files"></a>
## TerminalInput.pick_files

面板实时模糊多选或普通编号选择。

```python
def pick_files(self)
```

位置：[136行](../../../terminal_input.py#L136) 至快照 164 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：`all`、`answer.split`、`answer.startswith`、`dict.fromkeys`、`enumerate`、`input`、`input('编号可用逗号分隔；/关键词 筛选；留空取消: ').strip`、`int`、`len`、`list`、`matching_files`、`min`、`pick_files`、`print`、`safe_text`、`scan_files`、`str`、`value.strip`、`value.strip().isdigit`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 139 | `catalog` | `scan_files()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 142 | `notice` | `'（索引不完整: ' + catalog['reason'] + '）' if catalog['truncated'] else ''` | 目录索引不完整等提示文字。 |
| 148 | `filtered` | `catalog['files']` | 当前筛选后候选路径列表。 |
| 154 | `answer` | `input('编号可用逗号分隔；/关键词 筛选；留空取消: ').strip()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 158 | `filtered` | `matching_files(catalog['files'], answer[1:])` | 当前筛选后候选路径列表。 |
| 160 | `numbers` | `answer.split(',')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 137 | 函数体 | 在此处导入依赖：`from file_catalog import scan_files, matching_files`；局部导入可延迟加载或避免循环。 |
| 138 | 函数体 | 在此处导入依赖：`from file_picker import MAX_SELECTION, pick_files`；局部导入可延迟加载或避免循环。 |
| 139 | 函数体 | 将 `scan_files()` 赋给 `catalog`。 |
| 140 | 函数体 | 遍历 `catalog['warnings']`，每次绑定 `warning`。 |
| 141 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`print(safe_text(warning))`。 |
| 142 | 函数体 | 将 `'（索引不完整: ' + catalog['reason'] + '）' if catalog['truncated'] else ''` 赋给 `notice`。 |
| 143 | 函数体 | 条件 `not catalog['files']`：真时执行body，假时进入else/后续。 |
| 144 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`print('没有可选择的文件' + notice)`。 |
| 145 | 函数体 / 条件为真 | 返回 `None`，结束当前函数；具体分支见完整源码。 |
| 146 | 函数体 | 条件 `self.session is not None`：真时执行body，假时进入else/后续。 |
| 147 | 函数体 / 条件为真 | 返回 `pick_files(catalog['files'], notice=notice)`，结束当前函数；具体分支见完整源码。 |
| 148 | 函数体 | 将 `catalog['files']` 赋给 `filtered`。 |
| 149 | 函数体 | 循环检查 `True`，break/return/异常可结束。 |
| 150 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`print('选择附件' + notice)`。 |
| 151 | 函数体 / 循环每次 | 遍历 `enumerate(filtered[:200], 1)`，每次绑定 `(index, path)`。 |
| 152 | 函数体 / 循环每次 / 循环每次 | 计算表达式/调用产生动作：`print(str(index) + '. ' + safe_text(path))`。 |
| 153 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`print('匹配数量:', len(filtered), '（最多显示 200 项）')`。 |
| 154 | 函数体 / 循环每次 | 将 `input('编号可用逗号分隔；/关键词 筛选；留空取消: ').strip()` 赋给 `answer`。 |
| 155 | 函数体 / 循环每次 | 条件 `not answer`：真时执行body，假时进入else/后续。 |
| 156 | 函数体 / 循环每次 / 条件为真 | 返回 `None`，结束当前函数；具体分支见完整源码。 |
| 157 | 函数体 / 循环每次 | 条件 `answer.startswith('/')`：真时执行body，假时进入else/后续。 |
| 158 | 函数体 / 循环每次 / 条件为真 | 将 `matching_files(catalog['files'], answer[1:])` 赋给 `filtered`。 |
| 159 | 函数体 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 160 | 函数体 / 循环每次 | 将 `answer.split(',')` 赋给 `numbers`。 |
| 161 | 函数体 / 循环每次 | 条件 `len(numbers) <= MAX_SELECTION and all((value.strip().isdigit() and 1 <= int(value.strip()) <= min(len(filtered), 200) for value in numbers))`：真时执行body，假时进入else/后续。 |
| 163 | 函数体 / 循环每次 / 条件为真 | 返回 `list(dict.fromkeys((filtered[int(value.strip()) - 1] for value in numbers)))`，结束当前函数；具体分支见完整源码。 |
| 164 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`print('无效编号；最多选择 10 个文件')`。 |

**实际返回分支**：

- L145：`None`。
- L147：`pick_files(catalog['files'], notice=notice)`。
- L156：`None`。
- L163：`list(dict.fromkeys((filtered[int(value.strip()) - 1] for value in numbers)))`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="terminalinput-read"></a>
## TerminalInput.read

普通input或PromptSession.prompt读取，动态toolbar显示当前配置。

```python
def read(self, session_name)
```

位置：[166行](../../../terminal_input.py#L166) 至快照 173 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `session_name` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`input`、`self.session.prompt`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 167 | `label` | `'你[' + session_name + ']: '` | 候选显示标签/提示前缀，与真正返回value分开。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 167 | 函数体 | 将 `'你[' + session_name + ']: '` 赋给 `label`。 |
| 168 | 函数体 | 条件 `self.session is None`：真时执行body，假时进入else/后续。 |
| 169 | 函数体 / 条件为真 | 返回 `input(label)`，结束当前函数；具体分支见完整源码。 |
| 170 | 函数体 | 定义嵌套函数 `toolbar`；定义本身不执行函数体。 |
| 173 | 函数体 | 返回 `self.session.prompt(label, bottom_toolbar=toolbar)`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L169：`input(label)`。
- L173：`self.session.prompt(label, bottom_toolbar=toolbar)`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="terminalinput-read-toolbar"></a>
## TerminalInput.read.toolbar

动态显示当前会话、模型与流式配置。

```python
def toolbar()
```

位置：[170行](../../../terminal_input.py#L170) 至快照 172 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：无直接调用。

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 171 | `mode` | `'开' if model_config['stream'] else '关'` | 流式/审批等当前模式字符串。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 171 | 函数体 | 将 `'开' if model_config['stream'] else '关'` 赋给 `mode`。 |
| 172 | 函数体 | 返回 `'会话 ' + session_name + ' \| 模型 ' + model_config['model'] + ' \| 流式 ' + mode + ' \| /help 查看帮助'`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L172：`'会话 ' + session_name + ' | 模型 ' + model_config['model'] + ' | 流式 ' + mode + ' | /help 查看帮助'`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- class：对象状态与方法/继承：L25, L73。
- try/except/finally：异常与保证清理：L88。
- with/yield：资源/状态生命周期或逐个生成：L30, L47, L89。
- 推导式/生成器表达式：循环建容器或逐个产生：L35, L43, L44, L103, L161, L163。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """终端输入适配：TTY 使用补全和多行编辑，管道或 --plain 使用 input。"""
0002 | import sys
0003 | from contextlib import contextmanager
0004 | from contextvars import ContextVar
0005 | from pathlib import Path
0006 | 
0007 | from command_help import COMMANDS
0008 | from config import model_config
0009 | from path_input import PATH_COMMANDS, path_candidates
0010 | from tool_display import safe_text
0011 | 
0012 | enhanced_confirmation = ContextVar('enhanced_confirmation', default=False)
0013 | 
0014 | 
0015 | def request_confirmation(prompt):
0016 |     if enhanced_confirmation.get():
0017 |         from terminal_dialog import choose
0018 |         return choose(prompt, [(False, '拒绝（默认）'), (True, '允许本次操作')], yes_no=True) is True
0019 |     return input(safe_text(prompt) + '\n允许吗？[y/N] ').strip().lower() == 'y'
0020 | 
0021 | 
0022 | def create_completer():
0023 |     from prompt_toolkit.completion import Completer, Completion, WordCompleter
0024 | 
0025 |     class ProjectCompleter(Completer):
0026 |         def get_completions(self, document, complete_event):
0027 |             text = document.text_before_cursor
0028 |             command, separator, argument = text.partition(' ')
0029 |             if command not in PATH_COMMANDS or not separator:
0030 |                 yield from WordCompleter(list(COMMANDS), sentence=True).get_completions(document, complete_event)
0031 |                 return
0032 |             # 路径是第一个参数；完整闭合引号后不再补全关键词。
0033 |             quote = argument[:1] if argument[:1] in ('"', "'") else ''
0034 |             typed = argument[1:] if quote else argument
0035 |             if (quote and quote in typed) or (not quote and any(char.isspace() for char in typed)):
0036 |                 return
0037 |             parent, _, prefix = typed.rpartition('/')
0038 |             directory = parent + '/' if '/' in typed else '.'
0039 |             candidates, _ = path_candidates(directory, prefix, directories_only=command == '/grep')
0040 |             for relative, is_directory in candidates:
0041 |                 candidate = relative + ('/' if is_directory else '')
0042 |                 # 含空格的文件用引号包裹；目录末尾保留开引号以便继续补全。
0043 |                 delimiter = quote or ('"' if any(char.isspace() for char in candidate) else '')
0044 |                 if '"' in candidate or "'" in candidate or any(ord(char) < 32 for char in candidate):
0045 |                     continue
0046 |                 replacement = delimiter + candidate + (delimiter if delimiter and not is_directory else '')
0047 |                 yield Completion(replacement, start_position=-len(argument),
0048 |                                  display=safe_text(candidate), display_meta='目录' if is_directory else '文件')
0049 | 
0050 |     return ProjectCompleter()
0051 | 
0052 | 
0053 | def create_key_bindings():
0054 |     from prompt_toolkit.key_binding import KeyBindings
0055 |     bindings = KeyBindings()
0056 | 
0057 |     @bindings.add("enter")
0058 |     def submit(event):
0059 |         if event.current_buffer.complete_state is not None:
0060 |             if event.current_buffer.complete_state.current_completion is None:
0061 |                 event.current_buffer.go_to_completion(0)
0062 |             event.current_buffer.complete_state = None
0063 |             return
0064 |         event.current_buffer.validate_and_handle()
0065 | 
0066 |     @bindings.add("escape", "enter")
0067 |     def newline(event):
0068 |         event.current_buffer.insert_text("\n")
0069 | 
0070 |     return bindings
0071 | 
0072 | 
0073 | class TerminalInput:
0074 |     def __init__(self, plain=False):
0075 |         self.session = None
0076 |         if not plain and sys.stdin.isatty() and sys.stdout.isatty():
0077 |             from prompt_toolkit import PromptSession
0078 |             from prompt_toolkit.history import InMemoryHistory
0079 |             self.session = PromptSession(
0080 |                 multiline=True, key_bindings=create_key_bindings(),
0081 |                 completer=create_completer(),
0082 |                 complete_while_typing=True, history=InMemoryHistory()
0083 |             )
0084 | 
0085 |     @contextmanager
0086 |     def confirmations(self):
0087 |         token = enhanced_confirmation.set(self.session is not None)
0088 |         try:
0089 |             yield
0090 |         finally:
0091 |             enhanced_confirmation.reset(token)
0092 | 
0093 |     def pick_file(self):
0094 |         import permissions
0095 |         from terminal_dialog import choose
0096 |         directory = '.'
0097 |         while True:
0098 |             candidates, truncated = path_candidates(directory)
0099 |             choices = []
0100 |             if directory != '.':
0101 |                 parent = str(Path(directory).parent)
0102 |                 choices.append(((parent, True), '../ 返回上一级'))
0103 |             choices.extend(((path, is_directory), ('📁 ' if is_directory else '   ') + Path(path).name)
0104 |                            for path, is_directory in candidates)
0105 |             title = '选择附件 · ' + directory
0106 |             if truncated:
0107 |                 title += '（候选已限制，请用路径补全定位其他文件）'
0108 |             if not choices:
0109 |                 print('没有可选择的文件')
0110 |                 return None
0111 |             if self.session is not None:
0112 |                 selected = choose(title, choices)
0113 |             else:
0114 |                 print(title)
0115 |                 for index, (_, label) in enumerate(choices, 1):
0116 |                     print(str(index) + '. ' + safe_text(label))
0117 |                 answer = input('输入编号，留空取消: ').strip()
0118 |                 if not answer:
0119 |                     return None
0120 |                 if not answer.isdigit() or not 1 <= int(answer) <= len(choices):
0121 |                     print('无效编号')
0122 |                     continue
0123 |                 selected = choices[int(answer) - 1][0]
0124 |             if selected is None:
0125 |                 return None
0126 |             path, is_directory = selected
0127 |             checked = permissions.resolve_project_path(path)
0128 |             if not checked['ok']:
0129 |                 print(checked['error'])
0130 |                 continue
0131 |             if is_directory:
0132 |                 directory = path
0133 |             else:
0134 |                 return path
0135 | 
0136 |     def pick_files(self):
0137 |         from file_catalog import scan_files, matching_files
0138 |         from file_picker import MAX_SELECTION, pick_files
0139 |         catalog = scan_files()
0140 |         for warning in catalog['warnings']:
0141 |             print(safe_text(warning))
0142 |         notice = '（索引不完整: ' + catalog['reason'] + '）' if catalog['truncated'] else ''
0143 |         if not catalog['files']:
0144 |             print('没有可选择的文件' + notice)
0145 |             return None
0146 |         if self.session is not None:
0147 |             return pick_files(catalog['files'], notice=notice)
0148 |         filtered = catalog['files']
0149 |         while True:
0150 |             print('选择附件' + notice)
0151 |             for index, path in enumerate(filtered[:200], 1):
0152 |                 print(str(index) + '. ' + safe_text(path))
0153 |             print('匹配数量:', len(filtered), '（最多显示 200 项）')
0154 |             answer = input('编号可用逗号分隔；/关键词 筛选；留空取消: ').strip()
0155 |             if not answer:
0156 |                 return None
0157 |             if answer.startswith('/'):
0158 |                 filtered = matching_files(catalog['files'], answer[1:])
0159 |                 continue
0160 |             numbers = answer.split(',')
0161 |             if (len(numbers) <= MAX_SELECTION and all(value.strip().isdigit()
0162 |                     and 1 <= int(value.strip()) <= min(len(filtered), 200) for value in numbers)):
0163 |                 return list(dict.fromkeys(filtered[int(value.strip()) - 1] for value in numbers))
0164 |             print('无效编号；最多选择 10 个文件')
0165 | 
0166 |     def read(self, session_name):
0167 |         label = "你[" + session_name + "]: "
0168 |         if self.session is None:
0169 |             return input(label)
0170 |         def toolbar():
0171 |             mode = "开" if model_config["stream"] else "关"
0172 |             return "会话 " + session_name + " | 模型 " + model_config["model"] + " | 流式 " + mode + " | /help 查看帮助"
0173 |         return self.session.prompt(label, bottom_toolbar=toolbar)
```
