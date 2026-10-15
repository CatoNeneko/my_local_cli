# patches.py：源码导读

全文件内容比较成diff，获准后检查冲突并原子替换。

先读专题：[03-tools.md](../03-tools.md)。

实际源码：[patches.py](../../../patches.py)。

快照 SHA256：`f3678bd97cfe4e7e49ef4bdbbd3d5916ab7f11fd9bc896934cf9eedec0ce9022`；105 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 1 | `import difflib` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 2 | `import os` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import tempfile` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `from permissions import resolve_project_path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [build_diff](#build-diff) | [9](../../../patches.py#L9) | 用unified_diff比较完整旧新内容并处理无末尾换行。 |
| [prepare_edit](#prepare-edit) | [25](../../../patches.py#L25) | 读取原字节，编码新字节，生成待审diff。 |
| [preview_edit](#preview-edit) | [53](../../../patches.py#L53) | 只返回准备得到的diff与changed，不发布。 |
| [apply_prepared_edit](#apply-prepared-edit) | [60](../../../patches.py#L60) | 复查路径与原字节，临时文件写好后os.replace发布。 |
| [edit_file](#edit-file) | [102](../../../patches.py#L102) | 兼容包装，重新进入统一执行器。 |

<a id="build-diff"></a>
## build_diff

用unified_diff比较完整旧新内容并处理无末尾换行。

```python
def build_diff(path, old_content, new_content)
```

位置：[9行](../../../patches.py#L9) 至快照 22 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| `old_content` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `new_content` | `未显式注解` | 拟写入的完整文字内容，不是模型提供的patch格式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`''.join`、`difflib.unified_diff`、`line.endswith`、`new_content.splitlines`、`old_content.splitlines`、`rendered.append`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 10 | `diff_lines` | `difflib.unified_diff(old_content.splitlines(keepends=True), new_content.splitlines(keepends=True), fromfile='before/' + path, tofi…（见完整源码）` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 16 | `rendered` | `[]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 10 | 函数体 | 将 `difflib.unified_diff(old_content.splitlines(keepends=True), new_content.splitlines(keepends=True), fromfile='before/' + path, tofile='after/' + path)` 赋给 `diff_lines`。 |
| 16 | 函数体 | 将 `[]` 赋给 `rendered`。 |
| 17 | 函数体 | 遍历 `diff_lines`，每次绑定 `line`。 |
| 18 | 函数体 / 循环每次 | 条件 `line.endswith('\n')`：真时执行body，假时进入else/后续。 |
| 19 | 函数体 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`rendered.append(line)`。 |
| 21 | 函数体 / 循环每次 / 条件为假/elif | 计算表达式/调用产生动作：`rendered.append(line + '\n\\ No newline at end of file\n')`。 |
| 22 | 函数体 | 返回 `''.join(rendered)`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L22：`''.join(rendered)`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="prepare-edit"></a>
## prepare_edit

读取原字节，编码新字节，生成待审diff。

```python
def prepare_edit(path, new_content)
```

位置：[25行](../../../patches.py#L25) 至快照 50 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| `new_content` | `未显式注解` | 拟写入的完整文字内容，不是模型提供的patch格式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`build_diff`、`isinstance`、`new_content.encode`、`original_bytes.decode`、`resolve_project_path`、`str`、`target.read_bytes`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 29 | `path_result` | `resolve_project_path(path)` | 路径解析检查结果；成功携带真实绝对路径。 |
| 33 | `target` | `Path(path_result['path'])` | 已选定的文件/目录或操作目标，提交前可能需要再次验证。 |
| 35 | `original_bytes` | `target.read_bytes()` | 审批前旧文件字节，用于写前冲突检查。 |
| 36 | `old_content` | `original_bytes.decode('utf-8')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 37 | `new_bytes` | `new_content.encode('utf-8')` | 拟发布的UTF-8字节，不在prepare阶段直接写目标。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 26 | 函数体 | 条件 `not isinstance(path, str) or not isinstance(new_content, str)`：真时执行body，假时进入else/后续。 |
| 27 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '路径和新内容必须是字符串'}`，结束当前函数；具体分支见完整源码。 |
| 29 | 函数体 | 将 `resolve_project_path(path)` 赋给 `path_result`。 |
| 30 | 函数体 | 条件 `not path_result['ok']`：真时执行body，假时进入else/后续。 |
| 31 | 函数体 / 条件为真 | 返回 `path_result`，结束当前函数；具体分支见完整源码。 |
| 33 | 函数体 | 将 `Path(path_result['path'])` 赋给 `target`。 |
| 34 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 35 | 函数体 / try | 将 `target.read_bytes()` 赋给 `original_bytes`。 |
| 36 | 函数体 / try | 将 `original_bytes.decode('utf-8')` 赋给 `old_content`。 |
| 37 | 函数体 / try | 将 `new_content.encode('utf-8')` 赋给 `new_bytes`。 |
| 38 | 函数体 | except UnicodeError：只处理匹配类型的异常。 |
| 39 | 函数体 / except UnicodeError | 返回 `{'ok': False, 'error': '文件或新内容不是有效的 UTF-8 文本'}`，结束当前函数；具体分支见完整源码。 |
| 40 | 函数体 | except OSError as error：只处理匹配类型的异常。 |
| 41 | 函数体 / except OSError as error | 返回 `{'ok': False, 'error': '读取失败: ' + str(error)}`，结束当前函数；具体分支见完整源码。 |
| 43 | 函数体 | 返回 `{'ok': True, 'path': str(target), 'original_bytes': original_bytes, 'new_bytes': new_bytes, 'changed': original_bytes != new_bytes, 'diff': build_diff(path, old_content, …（见完整源码）`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L27：`{'ok': False, 'error': '路径和新内容必须是字符串'}`。
- L31：`path_result`。
- L39：`{'ok': False, 'error': '文件或新内容不是有效的 UTF-8 文本'}`。
- L41：`{'ok': False, 'error': '读取失败: ' + str(error)}`。
- L43：`{'ok': True, 'path': str(target), 'original_bytes': original_bytes, 'new_bytes': new_bytes, 'changed': original_bytes != new_bytes, 'diff': build_diff(path, old_content, new_content)}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="preview-edit"></a>
## preview_edit

只返回准备得到的diff与changed，不发布。

```python
def preview_edit(path, new_content)
```

位置：[53行](../../../patches.py#L53) 至快照 57 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| `new_content` | `未显式注解` | 拟写入的完整文字内容，不是模型提供的patch格式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`prepare_edit`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 54 | `prepared` | `prepare_edit(path, new_content)` | prepare形成的待审快照：diff/字节或沙箱命令参数。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 54 | 函数体 | 将 `prepare_edit(path, new_content)` 赋给 `prepared`。 |
| 55 | 函数体 | 条件 `not prepared['ok']`：真时执行body，假时进入else/后续。 |
| 56 | 函数体 / 条件为真 | 返回 `prepared`，结束当前函数；具体分支见完整源码。 |
| 57 | 函数体 | 返回 `{'ok': True, 'changed': prepared['changed'], 'diff': prepared['diff']}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L56：`prepared`。
- L57：`{'ok': True, 'changed': prepared['changed'], 'diff': prepared['diff']}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="apply-prepared-edit"></a>
## apply_prepared_edit

复查路径与原字节，临时文件写好后os.replace发布。

```python
def apply_prepared_edit(prepared)
```

位置：[60行](../../../patches.py#L60) 至快照 99 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `prepared` | `未显式注解` | prepare形成的待审快照：diff/字节或沙箱命令参数。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`file.fileno`、`file.flush`、`file.write`、`os.chmod`、`os.fsync`、`os.replace`、`print`、`resolve_project_path`、`str`、`target.read_bytes`、`target.stat`、`tempfile.NamedTemporaryFile`、`temporary_path.unlink`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 64 | `target` | `Path(prepared['path'])` | 已选定的文件/目录或操作目标，提交前可能需要再次验证。 |
| 65 | `temporary_path` | `None` | 尚未发布的同目录临时文件路径，finally清理。 |
| 67 | `checked` | `resolve_project_path(prepared['path'])` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 75 | `original_mode` | `target.stat().st_mode` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 77 | `temporary_path` | `Path(file.name)` | 尚未发布的同目录临时文件路径，finally清理。 |
| 83 | `checked` | `resolve_project_path(prepared['path'])` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 90 | `temporary_path` | `None` | 尚未发布的同目录临时文件路径，finally清理。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 61 | 函数体 | 文档字符串：说明职责，不作为普通语句动作执行。 |
| 62 | 函数体 | 条件 `not prepared['changed']`：真时执行body，假时进入else/后续。 |
| 63 | 函数体 / 条件为真 | 返回 `{'ok': True, 'changed': False, 'message': '文件内容没有变化'}`，结束当前函数；具体分支见完整源码。 |
| 64 | 函数体 | 将 `Path(prepared['path'])` 赋给 `target`。 |
| 65 | 函数体 | 将 `None` 赋给 `temporary_path`。 |
| 66 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 67 | 函数体 / try | 将 `resolve_project_path(prepared['path'])` 赋给 `checked`。 |
| 68 | 函数体 / try | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 69 | 函数体 / try / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 70 | 函数体 / try | 条件 `checked['path'] != str(target)`：真时执行body，假时进入else/后续。 |
| 71 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': '路径目标已变化，请重新审查'}`，结束当前函数；具体分支见完整源码。 |
| 72 | 函数体 / try | 条件 `target.read_bytes() != prepared['original_bytes']`：真时执行body，假时进入else/后续。 |
| 73 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': '文件在审查期间已变化，请重新生成修改'}`，结束当前函数；具体分支见完整源码。 |
| 75 | 函数体 / try | 将 `target.stat().st_mode` 赋给 `original_mode`。 |
| 76 | 函数体 / try | 进入资源/状态范围：`tempfile.NamedTemporaryFile(dir=target.parent, prefix='.cli-edit-', delete=False)` 绑定 `file`；退出执行清理。 |
| 77 | 函数体 / try / with范围 | 将 `Path(file.name)` 赋给 `temporary_path`。 |
| 78 | 函数体 / try / with范围 | 计算表达式/调用产生动作：`file.write(prepared['new_bytes'])`。 |
| 79 | 函数体 / try / with范围 | 计算表达式/调用产生动作：`file.flush()`。 |
| 80 | 函数体 / try / with范围 | 计算表达式/调用产生动作：`os.fsync(file.fileno())`。 |
| 81 | 函数体 / try | 计算表达式/调用产生动作：`os.chmod(temporary_path, original_mode)`。 |
| 83 | 函数体 / try | 将 `resolve_project_path(prepared['path'])` 赋给 `checked`。 |
| 84 | 函数体 / try | 条件 `not checked['ok'] or checked['path'] != str(target)`：真时执行body，假时进入else/后续。 |
| 85 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': '路径目标已变化，请重新审查'}`，结束当前函数；具体分支见完整源码。 |
| 86 | 函数体 / try | 条件 `target.read_bytes() != prepared['original_bytes']`：真时执行body，假时进入else/后续。 |
| 87 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': '文件在写入前已变化，修改已取消'}`，结束当前函数；具体分支见完整源码。 |
| 89 | 函数体 / try | 计算表达式/调用产生动作：`os.replace(temporary_path, target)`。 |
| 90 | 函数体 / try | 将 `None` 赋给 `temporary_path`。 |
| 91 | 函数体 / try | 返回 `{'ok': True, 'changed': True, 'path': str(target), 'message': '修改已写入'}`，结束当前函数；具体分支见完整源码。 |
| 92 | 函数体 | except OSError as error：只处理匹配类型的异常。 |
| 93 | 函数体 / except OSError as error | 返回 `{'ok': False, 'error': '写入失败: ' + str(error)}`，结束当前函数；具体分支见完整源码。 |
| 95 | 函数体 / finally保证清理 | 条件 `temporary_path is not None`：真时执行body，假时进入else/后续。 |
| 96 | 函数体 / finally保证清理 / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 97 | 函数体 / finally保证清理 / 条件为真 / try | 计算表达式/调用产生动作：`temporary_path.unlink()`。 |
| 98 | 函数体 / finally保证清理 / 条件为真 | except OSError as error：只处理匹配类型的异常。 |
| 99 | 函数体 / finally保证清理 / 条件为真 / except OSError as error | 计算表达式/调用产生动作：`print('清理临时文件失败:', error)`。 |

**实际返回分支**：

- L63：`{'ok': True, 'changed': False, 'message': '文件内容没有变化'}`。
- L69：`checked`。
- L71：`{'ok': False, 'error': '路径目标已变化，请重新审查'}`。
- L73：`{'ok': False, 'error': '文件在审查期间已变化，请重新生成修改'}`。
- L85：`{'ok': False, 'error': '路径目标已变化，请重新审查'}`。
- L87：`{'ok': False, 'error': '文件在写入前已变化，修改已取消'}`。
- L91：`{'ok': True, 'changed': True, 'path': str(target), 'message': '修改已写入'}`。
- L93：`{'ok': False, 'error': '写入失败: ' + str(error)}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="edit-file"></a>
## edit_file

兼容包装，重新进入统一执行器。

```python
def edit_file(path, new_content)
```

位置：[102行](../../../patches.py#L102) 至快照 105 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| `new_content` | `未显式注解` | 拟写入的完整文字内容，不是模型提供的patch格式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`execute_tool`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 104 | 函数体 | 在此处导入依赖：`from tool_runtime import execute_tool`；局部导入可延迟加载或避免循环。 |
| 105 | 函数体 | 返回 `execute_tool('edit_file', {'path': path, 'new_content': new_content})`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L105：`execute_tool('edit_file', {'path': path, 'new_content': new_content})`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L34, L66, L96。
- with/yield：资源/状态生命周期或逐个生成：L76。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | import difflib
0002 | import os
0003 | import tempfile
0004 | from pathlib import Path
0005 | 
0006 | from permissions import resolve_project_path
0007 | 
0008 | 
0009 | def build_diff(path, old_content, new_content):
0010 |     diff_lines = difflib.unified_diff(
0011 |         old_content.splitlines(keepends=True),
0012 |         new_content.splitlines(keepends=True),
0013 |         fromfile="before/" + path,
0014 |         tofile="after/" + path
0015 |     )
0016 |     rendered = []
0017 |     for line in diff_lines:
0018 |         if line.endswith("\n"):
0019 |             rendered.append(line)
0020 |         else:
0021 |             rendered.append(line + "\n\\ No newline at end of file\n")
0022 |     return "".join(rendered)
0023 | 
0024 | 
0025 | def prepare_edit(path, new_content):
0026 |     if not isinstance(path, str) or not isinstance(new_content, str):
0027 |         return {"ok": False, "error": "路径和新内容必须是字符串"}
0028 | 
0029 |     path_result = resolve_project_path(path)
0030 |     if not path_result["ok"]:
0031 |         return path_result
0032 | 
0033 |     target = Path(path_result["path"])
0034 |     try:
0035 |         original_bytes = target.read_bytes()
0036 |         old_content = original_bytes.decode("utf-8")
0037 |         new_bytes = new_content.encode("utf-8")
0038 |     except UnicodeError:
0039 |         return {"ok": False, "error": "文件或新内容不是有效的 UTF-8 文本"}
0040 |     except OSError as error:
0041 |         return {"ok": False, "error": "读取失败: " + str(error)}
0042 | 
0043 |     return {
0044 |         "ok": True,
0045 |         "path": str(target),
0046 |         "original_bytes": original_bytes,
0047 |         "new_bytes": new_bytes,
0048 |         "changed": original_bytes != new_bytes,
0049 |         "diff": build_diff(path, old_content, new_content)
0050 |     }
0051 | 
0052 | 
0053 | def preview_edit(path, new_content):
0054 |     prepared = prepare_edit(path, new_content)
0055 |     if not prepared["ok"]:
0056 |         return prepared
0057 |     return {"ok": True, "changed": prepared["changed"], "diff": prepared["diff"]}
0058 | 
0059 | 
0060 | def apply_prepared_edit(prepared):
0061 |     """内部写入实现，只由已授权的执行入口调用。"""
0062 |     if not prepared["changed"]:
0063 |         return {"ok": True, "changed": False, "message": "文件内容没有变化"}
0064 |     target = Path(prepared["path"])
0065 |     temporary_path = None
0066 |     try:
0067 |         checked = resolve_project_path(prepared["path"])
0068 |         if not checked["ok"]:
0069 |             return checked
0070 |         if checked["path"] != str(target):
0071 |             return {"ok": False, "error": "路径目标已变化，请重新审查"}
0072 |         if target.read_bytes() != prepared["original_bytes"]:
0073 |             return {"ok": False, "error": "文件在审查期间已变化，请重新生成修改"}
0074 | 
0075 |         original_mode = target.stat().st_mode
0076 |         with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".cli-edit-", delete=False) as file:
0077 |             temporary_path = Path(file.name)
0078 |             file.write(prepared["new_bytes"])
0079 |             file.flush()
0080 |             os.fsync(file.fileno())
0081 |         os.chmod(temporary_path, original_mode)
0082 | 
0083 |         checked = resolve_project_path(prepared["path"])
0084 |         if not checked["ok"] or checked["path"] != str(target):
0085 |             return {"ok": False, "error": "路径目标已变化，请重新审查"}
0086 |         if target.read_bytes() != prepared["original_bytes"]:
0087 |             return {"ok": False, "error": "文件在写入前已变化，修改已取消"}
0088 | 
0089 |         os.replace(temporary_path, target)
0090 |         temporary_path = None
0091 |         return {"ok": True, "changed": True, "path": str(target), "message": "修改已写入"}
0092 |     except OSError as error:
0093 |         return {"ok": False, "error": "写入失败: " + str(error)}
0094 |     finally:
0095 |         if temporary_path is not None:
0096 |             try:
0097 |                 temporary_path.unlink()
0098 |             except OSError as error:
0099 |                 print("清理临时文件失败:", error)
0100 | 
0101 | 
0102 | def edit_file(path, new_content):
0103 |     # 保留旧接口，但也必须经过统一执行入口。
0104 |     from tool_runtime import execute_tool
0105 |     return execute_tool("edit_file", {"path": path, "new_content": new_content})
```
