# file_picker.py：源码导读

prompt-toolkit实时筛选与多选面板；返回路径，实际读文件由附件模块完成。

先读专题：[07-terminal.md](../07-terminal.md)。

实际源码：[file_picker.py](../../../file_picker.py)。

快照 SHA256：`f4005f44714d1f1cb2ea9a52a068c08f9e1baa3e79a53a63a43a108ea1030adc`；95 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `from file_catalog import matching_files` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `from tool_display import safe_text` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `MAX_SELECTION = 10` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [pick_files](#pick-files) | [8](../../../file_picker.py#L8) | 面板实时模糊多选或普通编号选择。 |
| [pick_files.refresh](#pick-files-refresh) | [24](../../../file_picker.py#L24) | 查询文本变化时重算filtered并归零高亮，保留marked集合。 |
| [pick_files.up](#pick-files-up) | [33](../../../file_picker.py#L33) | 高亮索引减1并限制下界。 |
| [pick_files.down](#pick-files-down) | [38](../../../file_picker.py#L38) | 高亮索引加1并限制上界。 |
| [pick_files.page_up](#pick-files-page-up) | [43](../../../file_picker.py#L43) | 高亮向上10项并限制下界。 |
| [pick_files.page_down](#pick-files-page-down) | [48](../../../file_picker.py#L48) | 高亮向下10项并限制上界。 |
| [pick_files.toggle](#pick-files-toggle) | [53](../../../file_picker.py#L53) | 当前候选勾选/取消，数量上限检查。 |
| [pick_files.accept](#pick-files-accept) | [65](../../../file_picker.py#L65) | 提交所选值或整批路径，结束面板。 |
| [pick_files.cancel](#pick-files-cancel) | [73](../../../file_picker.py#L73) | 取消选择/输入并返回None。 |
| [pick_files.render](#pick-files-render) | [76](../../../file_picker.py#L76) | 事件驱动的当前显示内容，读取闭包状态。 |

<a id="pick-files"></a>
## pick_files

面板实时模糊多选或普通编号选择。

```python
def pick_files(paths, *, notice='', input=None, output=None)
```

位置：[8行](../../../file_picker.py#L8) 至快照 95 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `paths` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `notice` | `未显式注解` | 目录索引不完整等提示文字。 |
| `input` | `未显式注解` | prompt-toolkit输入接口，测试可注入模拟输入。 |
| `output` | `未显式注解` | ConsoleOutput对象、缓冲或UI输出接口，具体按签名位置。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Application`、`Buffer`、`BufferControl`、`Dimension`、`FormattedTextControl`、`HSplit`、`KeyBindings`、`Label`、`Layout`、`VSplit`、`Window`、`app.run`、`matching_files`、`set`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 18 | `selected` | `0` | 界面高亮索引，某些主循环分支为选择结果；看当前层次。 |
| 19 | `marked` | `set()` | 多选勾选集合，筛选变化时仍保留。 |
| 20 | `filtered` | `matching_files(paths, '')` | 当前筛选后候选路径列表。 |
| 21 | `status` | `''` | UI提示或项目规则状态，非自动代表成功。 |
| 22 | `bindings` | `KeyBindings()` | prompt-toolkit按键绑定集合。 |
| 30 | `query` | `Buffer(on_text_changed=refresh)` | 筛选文字或Buffer对象，回调读取其text。 |
| 86 | `body` | `Window(FormattedTextControl(render, get_cursor_position=lambda: Point(x=0, y=selected)), height=Dimension(min=1, max=12))` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 88 | `search` | `Window(BufferControl(buffer=query), height=1)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 89 | `footer` | `Label(lambda: '匹配 ' + str(len(filtered)) + ' / 已选 ' + str(len(marked)) + ' · ↑/↓ 移动 · Tab 勾选 · Enter 添加 · Esc 取消\n' + status)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 91 | `layout` | `HSplit([Label('选择附件 · 输入文件名或路径片段（支持不连续字符）' + notice), VSplit([Label('筛选: ', width=6), search]), body, footer])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 93 | `app` | `Application(layout=Layout(layout, focused_element=search), key_bindings=bindings, full_screen=False, input=input, output=output)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 9 | 函数体 | 在此处导入依赖：`from prompt_toolkit.application import Application`；局部导入可延迟加载或避免循环。 |
| 10 | 函数体 | 在此处导入依赖：`from prompt_toolkit.buffer import Buffer`；局部导入可延迟加载或避免循环。 |
| 11 | 函数体 | 在此处导入依赖：`from prompt_toolkit.data_structures import Point`；局部导入可延迟加载或避免循环。 |
| 12 | 函数体 | 在此处导入依赖：`from prompt_toolkit.key_binding import KeyBindings`；局部导入可延迟加载或避免循环。 |
| 13 | 函数体 | 在此处导入依赖：`from prompt_toolkit.layout import Layout, HSplit, VSplit, Window`；局部导入可延迟加载或避免循环。 |
| 14 | 函数体 | 在此处导入依赖：`from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl`；局部导入可延迟加载或避免循环。 |
| 15 | 函数体 | 在此处导入依赖：`from prompt_toolkit.layout.dimension import Dimension`；局部导入可延迟加载或避免循环。 |
| 16 | 函数体 | 在此处导入依赖：`from prompt_toolkit.widgets import Label`；局部导入可延迟加载或避免循环。 |
| 18 | 函数体 | 将 `0` 赋给 `selected`。 |
| 19 | 函数体 | 将 `set()` 赋给 `marked`。 |
| 20 | 函数体 | 将 `matching_files(paths, '')` 赋给 `filtered`。 |
| 21 | 函数体 | 将 `''` 赋给 `status`。 |
| 22 | 函数体 | 将 `KeyBindings()` 赋给 `bindings`。 |
| 24 | 函数体 | 定义嵌套函数 `refresh`；定义本身不执行函数体。 |
| 30 | 函数体 | 将 `Buffer(on_text_changed=refresh)` 赋给 `query`。 |
| 33 | 函数体 | 定义嵌套函数 `up`；定义本身不执行函数体。 |
| 38 | 函数体 | 定义嵌套函数 `down`；定义本身不执行函数体。 |
| 43 | 函数体 | 定义嵌套函数 `page_up`；定义本身不执行函数体。 |
| 48 | 函数体 | 定义嵌套函数 `page_down`；定义本身不执行函数体。 |
| 53 | 函数体 | 定义嵌套函数 `toggle`；定义本身不执行函数体。 |
| 65 | 函数体 | 定义嵌套函数 `accept`；定义本身不执行函数体。 |
| 73 | 函数体 | 定义嵌套函数 `cancel`；定义本身不执行函数体。 |
| 76 | 函数体 | 定义嵌套函数 `render`；定义本身不执行函数体。 |
| 86 | 函数体 | 将 `Window(FormattedTextControl(render, get_cursor_position=lambda: Point(x=0, y=selected)), height=Dimension(min=1, max=12))` 赋给 `body`。 |
| 88 | 函数体 | 将 `Window(BufferControl(buffer=query), height=1)` 赋给 `search`。 |
| 89 | 函数体 | 将 `Label(lambda: '匹配 ' + str(len(filtered)) + ' / 已选 ' + str(len(marked)) + ' · ↑/↓ 移动 · Tab 勾选 · Enter 添加 · Esc 取消\n' + status)` 赋给 `footer`。 |
| 91 | 函数体 | 将 `HSplit([Label('选择附件 · 输入文件名或路径片段（支持不连续字符）' + notice), VSplit([Label('筛选: ', width=6), search]), body, footer])` 赋给 `layout`。 |
| 93 | 函数体 | 将 `Application(layout=Layout(layout, focused_element=search), key_bindings=bindings, full_screen=False, input=input, output=output)` 赋给 `app`。 |
| 95 | 函数体 | 返回 `app.run()`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L95：`app.run()`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="pick-files-refresh"></a>
## pick_files.refresh

查询文本变化时重算filtered并归零高亮，保留marked集合。

```python
def refresh(buffer)
```

位置：[24行](../../../file_picker.py#L24) 至快照 28 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `buffer` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`matching_files`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 26 | `filtered` | `matching_files(paths, buffer.text)` | 当前筛选后候选路径列表。 |
| 27 | `selected` | `0` | 界面高亮索引，某些主循环分支为选择结果；看当前层次。 |
| 28 | `status` | `''` | UI提示或项目规则状态，非自动代表成功。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 25 | 函数体 | nonlocal使用并可重新赋值外层函数变量：`filtered, selected, status`。 |
| 26 | 函数体 | 将 `matching_files(paths, buffer.text)` 赋给 `filtered`。 |
| 27 | 函数体 | 将 `0` 赋给 `selected`。 |
| 28 | 函数体 | 将 `''` 赋给 `status`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="pick-files-up"></a>
## pick_files.up

高亮索引减1并限制下界。

```python
def up(event)
```

位置：[33行](../../../file_picker.py#L33) 至快照 35 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `event` | `未显式注解` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |

**调用表达式（静态提取，不含内层独立函数体）**：`bindings.add`、`max`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 35 | `selected` | `max(0, selected - 1)` | 界面高亮索引，某些主循环分支为选择结果；看当前层次。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 34 | 函数体 | nonlocal使用并可重新赋值外层函数变量：`selected`。 |
| 35 | 函数体 | 将 `max(0, selected - 1)` 赋给 `selected`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="pick-files-down"></a>
## pick_files.down

高亮索引加1并限制上界。

```python
def down(event)
```

位置：[38行](../../../file_picker.py#L38) 至快照 40 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `event` | `未显式注解` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |

**调用表达式（静态提取，不含内层独立函数体）**：`bindings.add`、`len`、`max`、`min`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 40 | `selected` | `min(max(0, len(filtered) - 1), selected + 1)` | 界面高亮索引，某些主循环分支为选择结果；看当前层次。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 39 | 函数体 | nonlocal使用并可重新赋值外层函数变量：`selected`。 |
| 40 | 函数体 | 将 `min(max(0, len(filtered) - 1), selected + 1)` 赋给 `selected`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="pick-files-page-up"></a>
## pick_files.page_up

高亮向上10项并限制下界。

```python
def page_up(event)
```

位置：[43行](../../../file_picker.py#L43) 至快照 45 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `event` | `未显式注解` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |

**调用表达式（静态提取，不含内层独立函数体）**：`bindings.add`、`max`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 45 | `selected` | `max(0, selected - 10)` | 界面高亮索引，某些主循环分支为选择结果；看当前层次。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 44 | 函数体 | nonlocal使用并可重新赋值外层函数变量：`selected`。 |
| 45 | 函数体 | 将 `max(0, selected - 10)` 赋给 `selected`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="pick-files-page-down"></a>
## pick_files.page_down

高亮向下10项并限制上界。

```python
def page_down(event)
```

位置：[48行](../../../file_picker.py#L48) 至快照 50 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `event` | `未显式注解` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |

**调用表达式（静态提取，不含内层独立函数体）**：`bindings.add`、`len`、`max`、`min`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 50 | `selected` | `min(max(0, len(filtered) - 1), selected + 10)` | 界面高亮索引，某些主循环分支为选择结果；看当前层次。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 49 | 函数体 | nonlocal使用并可重新赋值外层函数变量：`selected`。 |
| 50 | 函数体 | 将 `min(max(0, len(filtered) - 1), selected + 10)` 赋给 `selected`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="pick-files-toggle"></a>
## pick_files.toggle

当前候选勾选/取消，数量上限检查。

```python
def toggle(event)
```

位置：[53行](../../../file_picker.py#L53) 至快照 62 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `event` | `未显式注解` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |

**调用表达式（静态提取，不含内层独立函数体）**：`bindings.add`、`len`、`marked.add`、`marked.remove`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 56 | `path` | `filtered[selected]` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| 62 | `status` | `'最多选择 10 个文件'` | UI提示或项目规则状态，非自动代表成功。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 54 | 函数体 | nonlocal使用并可重新赋值外层函数变量：`status`。 |
| 55 | 函数体 | 条件 `filtered`：真时执行body，假时进入else/后续。 |
| 56 | 函数体 / 条件为真 | 将 `filtered[selected]` 赋给 `path`。 |
| 57 | 函数体 / 条件为真 | 条件 `path in marked`：真时执行body，假时进入else/后续。 |
| 58 | 函数体 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`marked.remove(path)`。 |
| 59 | 函数体 / 条件为真 / 条件为假/elif | 条件 `len(marked) < MAX_SELECTION`：真时执行body，假时进入else/后续。 |
| 60 | 函数体 / 条件为真 / 条件为假/elif / 条件为真 | 计算表达式/调用产生动作：`marked.add(path)`。 |
| 62 | 函数体 / 条件为真 / 条件为假/elif / 条件为假/elif | 将 `'最多选择 10 个文件'` 赋给 `status`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="pick-files-accept"></a>
## pick_files.accept

提交所选值或整批路径，结束面板。

```python
def accept(event)
```

位置：[65行](../../../file_picker.py#L65) 至快照 68 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `event` | `未显式注解` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |

**调用表达式（静态提取，不含内层独立函数体）**：`bindings.add`、`event.app.exit`、`sorted`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 67 | `result` | `sorted(marked) if marked else [filtered[selected]] if filtered else []` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 67 | 函数体 | 将 `sorted(marked) if marked else [filtered[selected]] if filtered else []` 赋给 `result`。 |
| 68 | 函数体 | 计算表达式/调用产生动作：`event.app.exit(result=result)`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="pick-files-cancel"></a>
## pick_files.cancel

取消选择/输入并返回None。

```python
def cancel(event)
```

位置：[73行](../../../file_picker.py#L73) 至快照 74 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `event` | `未显式注解` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |

**调用表达式（静态提取，不含内层独立函数体）**：`bindings.add`、`event.app.exit`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 74 | 函数体 | 计算表达式/调用产生动作：`event.app.exit(result=None)`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="pick-files-render"></a>
## pick_files.render

事件驱动的当前显示内容，读取闭包状态。

```python
def render()
```

位置：[76行](../../../file_picker.py#L76) 至快照 84 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`enumerate`、`safe_text`、`safe_text(path).replace`、`safe_text(path).replace('\n', '\\n').replace`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 77 | 函数体 | 条件 `not filtered`：真时执行body，假时进入else/后续。 |
| 78 | 函数体 / 条件为真 | 返回 `[('ansiyellow', '没有匹配文件；修改关键词或 Esc 取消')]`，结束当前函数；具体分支见完整源码。 |
| 79 | 函数体 | 返回 `[('reverse' if index == selected else '', ('› ' if index == selected else '  ') + ('[x] ' if path in marked else '[ ] ') + safe_text(path).replace('\n', '\\n').replace('\…（见完整源码）`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L78：`[('ansiyellow', '没有匹配文件；修改关键词或 Esc 取消')]`。
- L79：`[('reverse' if index == selected else '', ('› ' if index == selected else '  ') + ('[x] ' if path in marked else '[ ] ') + safe_text(path).replace('\n', '\\n').replace('\t', '\\t') + '\n') for index, path in en…（见完整源码）`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- nonlocal：回调改外层变量：L25, L34, L39, L44, L49, L54。
- 推导式/生成器表达式：循环建容器或逐个产生：L79。
- lambda：小回调函数：L86, L89。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """可筛选、多选的附件面板；选中状态跨筛选保留。"""
0002 | from file_catalog import matching_files
0003 | from tool_display import safe_text
0004 | 
0005 | MAX_SELECTION = 10
0006 | 
0007 | 
0008 | def pick_files(paths, *, notice='', input=None, output=None):
0009 |     from prompt_toolkit.application import Application
0010 |     from prompt_toolkit.buffer import Buffer
0011 |     from prompt_toolkit.data_structures import Point
0012 |     from prompt_toolkit.key_binding import KeyBindings
0013 |     from prompt_toolkit.layout import Layout, HSplit, VSplit, Window
0014 |     from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
0015 |     from prompt_toolkit.layout.dimension import Dimension
0016 |     from prompt_toolkit.widgets import Label
0017 | 
0018 |     selected = 0
0019 |     marked = set()
0020 |     filtered = matching_files(paths, '')
0021 |     status = ''
0022 |     bindings = KeyBindings()
0023 | 
0024 |     def refresh(buffer):
0025 |         nonlocal filtered, selected, status
0026 |         filtered = matching_files(paths, buffer.text)
0027 |         selected = 0
0028 |         status = ''
0029 | 
0030 |     query = Buffer(on_text_changed=refresh)
0031 | 
0032 |     @bindings.add('up')
0033 |     def up(event):
0034 |         nonlocal selected
0035 |         selected = max(0, selected - 1)
0036 | 
0037 |     @bindings.add('down')
0038 |     def down(event):
0039 |         nonlocal selected
0040 |         selected = min(max(0, len(filtered) - 1), selected + 1)
0041 | 
0042 |     @bindings.add('pageup')
0043 |     def page_up(event):
0044 |         nonlocal selected
0045 |         selected = max(0, selected - 10)
0046 | 
0047 |     @bindings.add('pagedown')
0048 |     def page_down(event):
0049 |         nonlocal selected
0050 |         selected = min(max(0, len(filtered) - 1), selected + 10)
0051 | 
0052 |     @bindings.add('tab')
0053 |     def toggle(event):
0054 |         nonlocal status
0055 |         if filtered:
0056 |             path = filtered[selected]
0057 |             if path in marked:
0058 |                 marked.remove(path)
0059 |             elif len(marked) < MAX_SELECTION:
0060 |                 marked.add(path)
0061 |             else:
0062 |                 status = '最多选择 10 个文件'
0063 | 
0064 |     @bindings.add('enter')
0065 |     def accept(event):
0066 |         # 已勾选时提交整个集合；否则添加当前高亮项。
0067 |         result = sorted(marked) if marked else [filtered[selected]] if filtered else []
0068 |         event.app.exit(result=result)
0069 | 
0070 |     @bindings.add('escape', eager=True)
0071 |     @bindings.add('c-c')
0072 |     @bindings.add('c-d')
0073 |     def cancel(event):
0074 |         event.app.exit(result=None)
0075 | 
0076 |     def render():
0077 |         if not filtered:
0078 |             return [('ansiyellow', '没有匹配文件；修改关键词或 Esc 取消')]
0079 |         return [
0080 |             ('reverse' if index == selected else '',
0081 |              ('› ' if index == selected else '  ') + ('[x] ' if path in marked else '[ ] ')
0082 |              + safe_text(path).replace('\n', '\\n').replace('\t', '\\t') + '\n')
0083 |             for index, path in enumerate(filtered)
0084 |         ]
0085 | 
0086 |     body = Window(FormattedTextControl(render, get_cursor_position=lambda: Point(x=0, y=selected)),
0087 |                   height=Dimension(min=1, max=12))
0088 |     search = Window(BufferControl(buffer=query), height=1)
0089 |     footer = Label(lambda: '匹配 ' + str(len(filtered)) + ' / 已选 ' + str(len(marked))
0090 |                    + ' · ↑/↓ 移动 · Tab 勾选 · Enter 添加 · Esc 取消\n' + status)
0091 |     layout = HSplit([Label('选择附件 · 输入文件名或路径片段（支持不连续字符）' + notice),
0092 |                      VSplit([Label('筛选: ', width=6), search]), body, footer])
0093 |     app = Application(layout=Layout(layout, focused_element=search), key_bindings=bindings,
0094 |                       full_screen=False, input=input, output=output)
0095 |     return app.run()
```
