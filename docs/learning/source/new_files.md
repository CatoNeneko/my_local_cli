# new_files.py：源码导读

新文件准备与独占发布，拒绝覆盖已有目标。

先读专题：[03-tools.md](../03-tools.md)。

实际源码：[new_files.py](../../../new_files.py)。

快照 SHA256：`7a46952e09e5eec690084c2b5ac52790d86406b2f8b8213321ec83266553a38b`；78 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import os` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import tempfile` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `import permissions` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `from patches import build_diff` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 9 | `MAX_NEW_FILE_BYTES = 1048576` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [check_new_target](#check-new-target) | [12](../../../new_files.py#L12) | 新目标不能存在，原路径各层不能是符号链接或非法父路径。 |
| [prepare_create_file](#prepare-create-file) | [31](../../../new_files.py#L31) | 验证新文件内容与大小，生成空文件到新内容的diff。 |
| [apply_prepared_file](#apply-prepared-file) | [49](../../../new_files.py#L49) | 复查目标，临时写后os.link独占发布，finally清理临时名。 |

<a id="check-new-target"></a>
## check_new_target

新目标不能存在，原路径各层不能是符号链接或非法父路径。

```python
def check_new_target(path)
```

位置：[12行](../../../new_files.py#L12) 至快照 28 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`item.exists`、`item.is_dir`、`item.is_symlink`、`original.is_absolute`、`permissions.resolve_project_path`、`target.exists`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 13 | `checked` | `permissions.resolve_project_path(path)` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 16 | `target` | `Path(checked['path'])` | 已选定的文件/目录或操作目标，提交前可能需要再次验证。 |
| 18 | `original` | `Path(path)` | 旧文件字节/原始路径对象等，具体以当前赋值为准。 |
| 20 | `original` | `permissions.PROJECT_ROOT / original` | 旧文件字节/原始路径对象等，具体以当前赋值为准。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 13 | 函数体 | 将 `permissions.resolve_project_path(path)` 赋给 `checked`。 |
| 14 | 函数体 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 15 | 函数体 / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 16 | 函数体 | 将 `Path(checked['path'])` 赋给 `target`。 |
| 18 | 函数体 | 将 `Path(path)` 赋给 `original`。 |
| 19 | 函数体 | 条件 `not original.is_absolute()`：真时执行body，假时进入else/后续。 |
| 20 | 函数体 / 条件为真 | 将 `permissions.PROJECT_ROOT / original` 赋给 `original`。 |
| 21 | 函数体 | 遍历 `[original, *original.parents]`，每次绑定 `item`。 |
| 22 | 函数体 / 循环每次 | 条件 `item.is_symlink()`：真时执行body，假时进入else/后续。 |
| 23 | 函数体 / 循环每次 / 条件为真 | 返回 `{'ok': False, 'error': '新建文件的路径不能包含符号链接'}`，结束当前函数；具体分支见完整源码。 |
| 24 | 函数体 / 循环每次 | 条件 `item.exists() and item != original and (not item.is_dir())`：真时执行body，假时进入else/后续。 |
| 25 | 函数体 / 循环每次 / 条件为真 | 返回 `{'ok': False, 'error': '父路径不是目录'}`，结束当前函数；具体分支见完整源码。 |
| 26 | 函数体 | 条件 `target.exists()`：真时执行body，假时进入else/后续。 |
| 27 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '目标已存在；请先读取并使用 edit_file，不能覆盖'}`，结束当前函数；具体分支见完整源码。 |
| 28 | 函数体 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L15：`checked`。
- L23：`{'ok': False, 'error': '新建文件的路径不能包含符号链接'}`。
- L25：`{'ok': False, 'error': '父路径不是目录'}`。
- L27：`{'ok': False, 'error': '目标已存在；请先读取并使用 edit_file，不能覆盖'}`。
- L28：`checked`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="prepare-create-file"></a>
## prepare_create_file

验证新文件内容与大小，生成空文件到新内容的diff。

```python
def prepare_create_file(path, new_content)
```

位置：[31行](../../../new_files.py#L31) 至快照 46 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| `new_content` | `未显式注解` | 拟写入的完整文字内容，不是模型提供的patch格式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`Path(checked['path']).relative_to`、`build_diff`、`check_new_target`、`isinstance`、`len`、`new_content.encode`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 32 | `checked` | `check_new_target(path)` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 38 | `raw` | `new_content.encode('utf-8')` | 未解码字节/完整输出快照，按编码与限额再处理。 |
| 43 | `relative` | `str(Path(checked['path']).relative_to(permissions.PROJECT_ROOT))` | 相对项目路径，供显示或范围检查。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 32 | 函数体 | 将 `check_new_target(path)` 赋给 `checked`。 |
| 33 | 函数体 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 34 | 函数体 / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 35 | 函数体 | 条件 `not isinstance(new_content, str) or '\x00' in new_content`：真时执行body，假时进入else/后续。 |
| 36 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '新文件内容必须是文字，不能包含空字符'}`，结束当前函数；具体分支见完整源码。 |
| 37 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 38 | 函数体 / try | 将 `new_content.encode('utf-8')` 赋给 `raw`。 |
| 39 | 函数体 | except UnicodeError：只处理匹配类型的异常。 |
| 40 | 函数体 / except UnicodeError | 返回 `{'ok': False, 'error': '新文件内容不是有效 UTF-8'}`，结束当前函数；具体分支见完整源码。 |
| 41 | 函数体 | 条件 `len(raw) > MAX_NEW_FILE_BYTES`：真时执行body，假时进入else/后续。 |
| 42 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '新文件内容超过 1 MiB 上限'}`，结束当前函数；具体分支见完整源码。 |
| 43 | 函数体 | 将 `str(Path(checked['path']).relative_to(permissions.PROJECT_ROOT))` 赋给 `relative`。 |
| 44 | 函数体 | 返回 `{'ok': True, 'path': checked['path'], 'original_path': path, 'new_bytes': raw, 'diff': build_diff(relative, '', new_content), 'details': '新建 UTF-8 文件；必要时创建父目录；拒绝覆盖已有文件'}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L34：`checked`。
- L36：`{'ok': False, 'error': '新文件内容必须是文字，不能包含空字符'}`。
- L40：`{'ok': False, 'error': '新文件内容不是有效 UTF-8'}`。
- L42：`{'ok': False, 'error': '新文件内容超过 1 MiB 上限'}`。
- L44：`{'ok': True, 'path': checked['path'], 'original_path': path, 'new_bytes': raw, 'diff': build_diff(relative, '', new_content), 'details': '新建 UTF-8 文件；必要时创建父目录；拒绝覆盖已有文件'}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="apply-prepared-file"></a>
## apply_prepared_file

复查目标，临时写后os.link独占发布，finally清理临时名。

```python
def apply_prepared_file(prepared)
```

位置：[49行](../../../new_files.py#L49) 至快照 78 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `prepared` | `未显式注解` | prepare形成的待审快照：diff/字节或沙箱命令参数。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`check_new_target`、`emit`、`file.fileno`、`file.flush`、`file.write`、`os.fsync`、`os.link`、`short_text`、`str`、`target.parent.mkdir`、`tempfile.NamedTemporaryFile`、`temporary.unlink`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 50 | `temporary` | `None` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 52 | `checked` | `check_new_target(prepared['original_path'])` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 57 | `target` | `Path(checked['path'])` | 已选定的文件/目录或操作目标，提交前可能需要再次验证。 |
| 61 | `temporary` | `Path(file.name)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 65 | `checked` | `check_new_target(prepared['original_path'])` | 路径/准备检查的返回结果，用ok决定能否继续。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 50 | 函数体 | 将 `None` 赋给 `temporary`。 |
| 51 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 52 | 函数体 / try | 将 `check_new_target(prepared['original_path'])` 赋给 `checked`。 |
| 53 | 函数体 / try | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 54 | 函数体 / try / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 55 | 函数体 / try | 条件 `checked['path'] != prepared['path']`：真时执行body，假时进入else/后续。 |
| 56 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': '目标已变化，请重新审查'}`，结束当前函数；具体分支见完整源码。 |
| 57 | 函数体 / try | 将 `Path(checked['path'])` 赋给 `target`。 |
| 58 | 函数体 / try | 计算表达式/调用产生动作：`target.parent.mkdir(parents=True, exist_ok=True)`。 |
| 60 | 函数体 / try | 进入资源/状态范围：`tempfile.NamedTemporaryFile(dir=target.parent, prefix='.cli-new-', delete=False)` 绑定 `file`；退出执行清理。 |
| 61 | 函数体 / try / with范围 | 将 `Path(file.name)` 赋给 `temporary`。 |
| 62 | 函数体 / try / with范围 | 计算表达式/调用产生动作：`file.write(prepared['new_bytes'])`。 |
| 63 | 函数体 / try / with范围 | 计算表达式/调用产生动作：`file.flush()`。 |
| 64 | 函数体 / try / with范围 | 计算表达式/调用产生动作：`os.fsync(file.fileno())`。 |
| 65 | 函数体 / try | 将 `check_new_target(prepared['original_path'])` 赋给 `checked`。 |
| 66 | 函数体 / try | 条件 `not checked['ok'] or checked['path'] != str(target)`：真时执行body，假时进入else/后续。 |
| 67 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': '目标在写入前已变化或已存在，创建取消'}`，结束当前函数；具体分支见完整源码。 |
| 68 | 函数体 / try | 计算表达式/调用产生动作：`os.link(temporary, target)`。 |
| 69 | 函数体 / try | 返回 `{'ok': True, 'changed': True, 'path': str(target), 'message': '新文件已创建'}`，结束当前函数；具体分支见完整源码。 |
| 70 | 函数体 | except OSError as error：只处理匹配类型的异常。 |
| 71 | 函数体 / except OSError as error | 返回 `{'ok': False, 'error': '新建失败: ' + str(error)}`，结束当前函数；具体分支见完整源码。 |
| 73 | 函数体 / finally保证清理 | 条件 `temporary is not None`：真时执行body，假时进入else/后续。 |
| 74 | 函数体 / finally保证清理 / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 75 | 函数体 / finally保证清理 / 条件为真 / try | 计算表达式/调用产生动作：`temporary.unlink(missing_ok=True)`。 |
| 76 | 函数体 / finally保证清理 / 条件为真 | except OSError as error：只处理匹配类型的异常。 |
| 77 | 函数体 / finally保证清理 / 条件为真 / except OSError as error | 在此处导入依赖：`from tool_display import emit, short_text`；局部导入可延迟加载或避免循环。 |
| 78 | 函数体 / finally保证清理 / 条件为真 / except OSError as error | 计算表达式/调用产生动作：`emit('新文件临时文件清理失败: ' + short_text(error), 'ansiyellow')`。 |

**实际返回分支**：

- L54：`checked`。
- L56：`{'ok': False, 'error': '目标已变化，请重新审查'}`。
- L67：`{'ok': False, 'error': '目标在写入前已变化或已存在，创建取消'}`。
- L69：`{'ok': True, 'changed': True, 'path': str(target), 'message': '新文件已创建'}`。
- L71：`{'ok': False, 'error': '新建失败: ' + str(error)}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L37, L51, L74。
- with/yield：资源/状态生命周期或逐个生成：L60。
- 星号展开：展开已有容器：L21。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """普通 UTF-8 文件的新建：审查后创建，已有目标一律拒绝覆盖。"""
0002 | import os
0003 | import tempfile
0004 | from pathlib import Path
0005 | 
0006 | import permissions
0007 | from patches import build_diff
0008 | 
0009 | MAX_NEW_FILE_BYTES = 1048576
0010 | 
0011 | 
0012 | def check_new_target(path):
0013 |     checked = permissions.resolve_project_path(path)
0014 |     if not checked['ok']:
0015 |         return checked
0016 |     target = Path(checked['path'])
0017 |     # 检查原始路径的每一层，拒绝通过符号链接新建文件。
0018 |     original = Path(path)
0019 |     if not original.is_absolute():
0020 |         original = permissions.PROJECT_ROOT / original
0021 |     for item in [original, *original.parents]:
0022 |         if item.is_symlink():
0023 |             return {'ok': False, 'error': '新建文件的路径不能包含符号链接'}
0024 |         if item.exists() and item != original and not item.is_dir():
0025 |             return {'ok': False, 'error': '父路径不是目录'}
0026 |     if target.exists():
0027 |         return {'ok': False, 'error': '目标已存在；请先读取并使用 edit_file，不能覆盖'}
0028 |     return checked
0029 | 
0030 | 
0031 | def prepare_create_file(path, new_content):
0032 |     checked = check_new_target(path)
0033 |     if not checked['ok']:
0034 |         return checked
0035 |     if not isinstance(new_content, str) or '\x00' in new_content:
0036 |         return {'ok': False, 'error': '新文件内容必须是文字，不能包含空字符'}
0037 |     try:
0038 |         raw = new_content.encode('utf-8')
0039 |     except UnicodeError:
0040 |         return {'ok': False, 'error': '新文件内容不是有效 UTF-8'}
0041 |     if len(raw) > MAX_NEW_FILE_BYTES:
0042 |         return {'ok': False, 'error': '新文件内容超过 1 MiB 上限'}
0043 |     relative = str(Path(checked['path']).relative_to(permissions.PROJECT_ROOT))
0044 |     return {'ok': True, 'path': checked['path'], 'original_path': path,
0045 |             'new_bytes': raw, 'diff': build_diff(relative, '', new_content),
0046 |             'details': '新建 UTF-8 文件；必要时创建父目录；拒绝覆盖已有文件'}
0047 | 
0048 | 
0049 | def apply_prepared_file(prepared):
0050 |     temporary = None
0051 |     try:
0052 |         checked = check_new_target(prepared['original_path'])
0053 |         if not checked['ok']:
0054 |             return checked
0055 |         if checked['path'] != prepared['path']:
0056 |             return {'ok': False, 'error': '目标已变化，请重新审查'}
0057 |         target = Path(checked['path'])
0058 |         target.parent.mkdir(parents=True, exist_ok=True)
0059 |         # 临时文件写完之后，link 独占发布；并发创建也不会覆盖。
0060 |         with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.cli-new-', delete=False) as file:
0061 |             temporary = Path(file.name)
0062 |             file.write(prepared['new_bytes'])
0063 |             file.flush()
0064 |             os.fsync(file.fileno())
0065 |         checked = check_new_target(prepared['original_path'])
0066 |         if not checked['ok'] or checked['path'] != str(target):
0067 |             return {'ok': False, 'error': '目标在写入前已变化或已存在，创建取消'}
0068 |         os.link(temporary, target)
0069 |         return {'ok': True, 'changed': True, 'path': str(target), 'message': '新文件已创建'}
0070 |     except OSError as error:
0071 |         return {'ok': False, 'error': '新建失败: ' + str(error)}
0072 |     finally:
0073 |         if temporary is not None:
0074 |             try:
0075 |                 temporary.unlink(missing_ok=True)
0076 |             except OSError as error:
0077 |                 from tool_display import emit, short_text
0078 |                 emit('新文件临时文件清理失败: ' + short_text(error), 'ansiyellow')
```
