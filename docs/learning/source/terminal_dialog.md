# terminal_dialog.py：源码导读

通用选择面板；选项值与标签分开，权限默认拒绝。

先读专题：[07-terminal.md](../07-terminal.md)。

实际源码：[terminal_dialog.py](../../../terminal_dialog.py)。

快照 SHA256：`d5f4d60e36fc3c32f7f4f76f16180ae0355fb0da8e469962aa9afae451ebea14`；63 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `from tool_display import safe_text` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [choose](#choose) | [5](../../../terminal_dialog.py#L5) | 通用候选面板，默认首项、按键更新、返回选项value或None。 |
| [choose.up](#choose-up) | [20](../../../terminal_dialog.py#L20) | 高亮索引减1并限制下界。 |
| [choose.down](#choose-down) | [25](../../../terminal_dialog.py#L25) | 高亮索引加1并限制上界。 |
| [choose.accept](#choose-accept) | [30](../../../terminal_dialog.py#L30) | 提交所选值或整批路径，结束面板。 |
| [choose.cancel](#choose-cancel) | [36](../../../terminal_dialog.py#L36) | 取消选择/输入并返回None。 |
| [choose.yes](#choose-yes) | [41](../../../terminal_dialog.py#L41) | 快捷键直接选择允许。 |
| [choose.no](#choose-no) | [45](../../../terminal_dialog.py#L45) | 快捷键直接选择拒绝。 |
| [choose.render](#choose-render) | [48](../../../terminal_dialog.py#L48) | 事件驱动的当前显示内容，读取闭包状态。 |

<a id="choose"></a>
## choose

通用候选面板，默认首项、按键更新、返回选项value或None。

```python
def choose(title, choices, *, input=None, output=None, yes_no=False)
```

位置：[5行](../../../terminal_dialog.py#L5) 至快照 63 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `title` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `choices` | `未显式注解` | 选择面板的(value,label)列表。 |
| `input` | `未显式注解` | prompt-toolkit输入接口，测试可注入模拟输入。 |
| `output` | `未显式注解` | ConsoleOutput对象、缓冲或UI输出接口，具体按签名位置。 |
| `yes_no` | `未显式注解` | 是否绑定y/n快速许可选择。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Application`、`Dimension`、`FormattedTextControl`、`HSplit`、`KeyBindings`、`Label`、`Layout`、`Window`、`app.run`、`safe_text`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 16 | `selected` | `0` | 界面高亮索引，某些主循环分支为选择结果；看当前层次。 |
| 17 | `bindings` | `KeyBindings()` | prompt-toolkit按键绑定集合。 |
| 56 | `control` | `FormattedTextControl(render, focusable=True, get_cursor_position=lambda: Point(x=0, y=selected))` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 58 | `body` | `Window(control, height=Dimension(min=1, max=12))` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 59 | `container` | `HSplit([Label(safe_text(title)), body, Label('↑/↓ 选择 · Enter 确认 · Esc 取消' + (' · y/n 快捷确认' if yes_no else ''))])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 61 | `app` | `Application(layout=Layout(container, focused_element=body), key_bindings=bindings, full_screen=False, input=input, output=output)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 6 | 函数体 | 在此处导入依赖：`from prompt_toolkit.application import Application`；局部导入可延迟加载或避免循环。 |
| 7 | 函数体 | 在此处导入依赖：`from prompt_toolkit.key_binding import KeyBindings`；局部导入可延迟加载或避免循环。 |
| 8 | 函数体 | 在此处导入依赖：`from prompt_toolkit.layout import Layout, HSplit, Window`；局部导入可延迟加载或避免循环。 |
| 9 | 函数体 | 在此处导入依赖：`from prompt_toolkit.layout.controls import FormattedTextControl`；局部导入可延迟加载或避免循环。 |
| 10 | 函数体 | 在此处导入依赖：`from prompt_toolkit.layout.dimension import Dimension`；局部导入可延迟加载或避免循环。 |
| 11 | 函数体 | 在此处导入依赖：`from prompt_toolkit.data_structures import Point`；局部导入可延迟加载或避免循环。 |
| 12 | 函数体 | 在此处导入依赖：`from prompt_toolkit.widgets import Label`；局部导入可延迟加载或避免循环。 |
| 14 | 函数体 | 条件 `not choices`：真时执行body，假时进入else/后续。 |
| 15 | 函数体 / 条件为真 | 返回 `None`，结束当前函数；具体分支见完整源码。 |
| 16 | 函数体 | 将 `0` 赋给 `selected`。 |
| 17 | 函数体 | 将 `KeyBindings()` 赋给 `bindings`。 |
| 20 | 函数体 | 定义嵌套函数 `up`；定义本身不执行函数体。 |
| 25 | 函数体 | 定义嵌套函数 `down`；定义本身不执行函数体。 |
| 30 | 函数体 | 定义嵌套函数 `accept`；定义本身不执行函数体。 |
| 36 | 函数体 | 定义嵌套函数 `cancel`；定义本身不执行函数体。 |
| 39 | 函数体 | 条件 `yes_no`：真时执行body，假时进入else/后续。 |
| 41 | 函数体 / 条件为真 | 定义嵌套函数 `yes`；定义本身不执行函数体。 |
| 45 | 函数体 / 条件为真 | 定义嵌套函数 `no`；定义本身不执行函数体。 |
| 48 | 函数体 | 定义嵌套函数 `render`；定义本身不执行函数体。 |
| 56 | 函数体 | 将 `FormattedTextControl(render, focusable=True, get_cursor_position=lambda: Point(x=0, y=selected))` 赋给 `control`。 |
| 58 | 函数体 | 将 `Window(control, height=Dimension(min=1, max=12))` 赋给 `body`。 |
| 59 | 函数体 | 将 `HSplit([Label(safe_text(title)), body, Label('↑/↓ 选择 · Enter 确认 · Esc 取消' + (' · y/n 快捷确认' if yes_no else ''))])` 赋给 `container`。 |
| 61 | 函数体 | 将 `Application(layout=Layout(container, focused_element=body), key_bindings=bindings, full_screen=False, input=input, output=output)` 赋给 `app`。 |
| 63 | 函数体 | 返回 `app.run()`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L15：`None`。
- L63：`app.run()`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="choose-up"></a>
## choose.up

高亮索引减1并限制下界。

```python
def up(event)
```

位置：[20行](../../../terminal_dialog.py#L20) 至快照 22 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `event` | `未显式注解` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |

**调用表达式（静态提取，不含内层独立函数体）**：`bindings.add`、`max`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 22 | `selected` | `max(0, selected - 1)` | 界面高亮索引，某些主循环分支为选择结果；看当前层次。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 21 | 函数体 | nonlocal使用并可重新赋值外层函数变量：`selected`。 |
| 22 | 函数体 | 将 `max(0, selected - 1)` 赋给 `selected`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="choose-down"></a>
## choose.down

高亮索引加1并限制上界。

```python
def down(event)
```

位置：[25行](../../../terminal_dialog.py#L25) 至快照 27 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `event` | `未显式注解` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |

**调用表达式（静态提取，不含内层独立函数体）**：`bindings.add`、`len`、`min`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 27 | `selected` | `min(len(choices) - 1, selected + 1)` | 界面高亮索引，某些主循环分支为选择结果；看当前层次。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 26 | 函数体 | nonlocal使用并可重新赋值外层函数变量：`selected`。 |
| 27 | 函数体 | 将 `min(len(choices) - 1, selected + 1)` 赋给 `selected`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="choose-accept"></a>
## choose.accept

提交所选值或整批路径，结束面板。

```python
def accept(event)
```

位置：[30行](../../../terminal_dialog.py#L30) 至快照 31 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `event` | `未显式注解` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |

**调用表达式（静态提取，不含内层独立函数体）**：`bindings.add`、`event.app.exit`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 31 | 函数体 | 计算表达式/调用产生动作：`event.app.exit(result=choices[selected][0])`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="choose-cancel"></a>
## choose.cancel

取消选择/输入并返回None。

```python
def cancel(event)
```

位置：[36行](../../../terminal_dialog.py#L36) 至快照 37 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `event` | `未显式注解` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |

**调用表达式（静态提取，不含内层独立函数体）**：`bindings.add`、`event.app.exit`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 37 | 函数体 | 计算表达式/调用产生动作：`event.app.exit(result=None)`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="choose-yes"></a>
## choose.yes

快捷键直接选择允许。

```python
def yes(event)
```

位置：[41行](../../../terminal_dialog.py#L41) 至快照 42 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `event` | `未显式注解` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |

**调用表达式（静态提取，不含内层独立函数体）**：`bindings.add`、`event.app.exit`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 42 | 函数体 | 计算表达式/调用产生动作：`event.app.exit(result=True)`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="choose-no"></a>
## choose.no

快捷键直接选择拒绝。

```python
def no(event)
```

位置：[45行](../../../terminal_dialog.py#L45) 至快照 46 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `event` | `未显式注解` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |

**调用表达式（静态提取，不含内层独立函数体）**：`bindings.add`、`event.app.exit`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 46 | 函数体 | 计算表达式/调用产生动作：`event.app.exit(result=False)`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="choose-render"></a>
## choose.render

事件驱动的当前显示内容，读取闭包状态。

```python
def render()
```

位置：[48行](../../../terminal_dialog.py#L48) 至快照 54 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`enumerate`、`rows.append`、`safe_text`、`safe_text(label).replace`、`safe_text(label).replace('\n', '\\n').replace`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 49 | `rows` | `[]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 51 | `style` | `'reverse' if index == selected else ''` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 52 | `display` | `safe_text(label).replace('\n', '\\n').replace('\t', '\\t')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 49 | 函数体 | 将 `[]` 赋给 `rows`。 |
| 50 | 函数体 | 遍历 `enumerate(choices)`，每次绑定 `(index, (_, label))`。 |
| 51 | 函数体 / 循环每次 | 将 `'reverse' if index == selected else ''` 赋给 `style`。 |
| 52 | 函数体 / 循环每次 | 将 `safe_text(label).replace('\n', '\\n').replace('\t', '\\t')` 赋给 `display`。 |
| 53 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`rows.append((style, ('› ' if index == selected else '  ') + display + '\n'))`。 |
| 54 | 函数体 | 返回 `rows`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L54：`rows`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- nonlocal：回调改外层变量：L21, L26。
- lambda：小回调函数：L57。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """轻量选择面板：上下移动，Enter 确认，Esc 取消。"""
0002 | from tool_display import safe_text
0003 | 
0004 | 
0005 | def choose(title, choices, *, input=None, output=None, yes_no=False):
0006 |     from prompt_toolkit.application import Application
0007 |     from prompt_toolkit.key_binding import KeyBindings
0008 |     from prompt_toolkit.layout import Layout, HSplit, Window
0009 |     from prompt_toolkit.layout.controls import FormattedTextControl
0010 |     from prompt_toolkit.layout.dimension import Dimension
0011 |     from prompt_toolkit.data_structures import Point
0012 |     from prompt_toolkit.widgets import Label
0013 | 
0014 |     if not choices:
0015 |         return None
0016 |     selected = 0  # 当前高亮的候选位置；初始为第一项。
0017 |     bindings = KeyBindings()
0018 | 
0019 |     @bindings.add('up')
0020 |     def up(event):
0021 |         nonlocal selected
0022 |         selected = max(0, selected - 1)
0023 | 
0024 |     @bindings.add('down')
0025 |     def down(event):
0026 |         nonlocal selected
0027 |         selected = min(len(choices) - 1, selected + 1)
0028 | 
0029 |     @bindings.add('enter')
0030 |     def accept(event):
0031 |         event.app.exit(result=choices[selected][0])
0032 | 
0033 |     @bindings.add('escape', eager=True)
0034 |     @bindings.add('c-c')
0035 |     @bindings.add('c-d')
0036 |     def cancel(event):
0037 |         event.app.exit(result=None)
0038 | 
0039 |     if yes_no:
0040 |         @bindings.add('y')
0041 |         def yes(event):
0042 |             event.app.exit(result=True)
0043 | 
0044 |         @bindings.add('n')
0045 |         def no(event):
0046 |             event.app.exit(result=False)
0047 | 
0048 |     def render():
0049 |         rows = []
0050 |         for index, (_, label) in enumerate(choices):
0051 |             style = 'reverse' if index == selected else ''
0052 |             display = safe_text(label).replace('\n', '\\n').replace('\t', '\\t')
0053 |             rows.append((style, ('› ' if index == selected else '  ') + display + '\n'))
0054 |         return rows
0055 | 
0056 |     control = FormattedTextControl(render, focusable=True,
0057 |                                    get_cursor_position=lambda: Point(x=0, y=selected))
0058 |     body = Window(control, height=Dimension(min=1, max=12))
0059 |     container = HSplit([Label(safe_text(title)), body,
0060 |                         Label('↑/↓ 选择 · Enter 确认 · Esc 取消' + (' · y/n 快捷确认' if yes_no else ''))])
0061 |     app = Application(layout=Layout(container, focused_element=body),
0062 |                       key_bindings=bindings, full_screen=False, input=input, output=output)
0063 |     return app.run()
```
