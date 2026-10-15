# path_input.py：源码导读

解析带引号路径和剩余关键词，以及受边界限制的目录候选。

先读专题：[07-terminal.md](../07-terminal.md)。

实际源码：[path_input.py](../../../path_input.py)。

快照 SHA256：`33a61cccb52a3b743c3e453c21e9144c90114c1509f5de9c5e2b9755ad8f323d`；56 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import os` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import io` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `import shlex` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `import permissions` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `from config import search_config` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 10 | `PATH_COMMANDS = {'/read', '/attach', '/search', '/grep'}` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [parse_path_arguments](#parse-path-arguments) | [13](../../../path_input.py#L13) | shlex只解析首路径token，保留剩余关键词。 |
| [path_candidates](#path-candidates) | [28](../../../path_input.py#L28) | 有界目录候选并区分目录，跳私有与链接。 |

<a id="parse-path-arguments"></a>
## parse_path_arguments

shlex只解析首路径token，保留剩余关键词。

```python
def parse_path_arguments(text)
```

位置：[13行](../../../path_input.py#L13) 至快照 25 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `text` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ValueError`、`io.StringIO`、`lexer.get_token`、`shlex.shlex`、`stream.read`、`stream.read().lstrip`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 15 | `stream` | `io.StringIO(text)` | 本次请求是否分块返回；不自动等于所有接口都流式。 |
| 16 | `lexer` | `shlex.shlex(stream, posix=True)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 17 | `lexer.whitespace_split` | `True` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 18 | `lexer.commenters` | `''` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 20 | `path` | `lexer.get_token()` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 15 | 函数体 | 将 `io.StringIO(text)` 赋给 `stream`。 |
| 16 | 函数体 | 将 `shlex.shlex(stream, posix=True)` 赋给 `lexer`。 |
| 17 | 函数体 | 将 `True` 赋给 `lexer.whitespace_split`。 |
| 18 | 函数体 | 将 `''` 赋给 `lexer.commenters`。 |
| 19 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 20 | 函数体 / try | 将 `lexer.get_token()` 赋给 `path`。 |
| 21 | 函数体 | except ValueError as error：只处理匹配类型的异常。 |
| 22 | 函数体 / except ValueError as error | 抛出 `ValueError('路径格式无效；带空格的路径请使用成对引号')`，异常链关联 `error`。 |
| 23 | 函数体 | 条件 `not path`：真时执行body，假时进入else/后续。 |
| 24 | 函数体 / 条件为真 | 抛出 `ValueError('路径不能为空')`。 |
| 25 | 函数体 | 返回 `(path, stream.read().lstrip())`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L25：`(path, stream.read().lstrip())`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="path-candidates"></a>
## path_candidates

有界目录候选并区分目录，跳私有与链接。

```python
def path_candidates(directory, prefix='', directories_only=False)
```

位置：[28行](../../../path_input.py#L28) 至快照 56 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `directory` | `未显式注解` | 当前目录路径，遍历/候选/会话使用。 |
| `prefix` | `未显式注解` | 系统规则/摘要前缀；模糊/路径函数中则是待补全名字前缀。 |
| `directories_only` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`Path(allowed['path']).relative_to`、`candidates.append`、`entry.is_dir`、`entry.is_file`、`entry.is_symlink`、`entry.name.startswith`、`enumerate`、`len`、`os.scandir`、`permissions.resolve_project_path`、`sorted`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 29 | `checked` | `permissions.resolve_project_path(directory)` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 32 | `candidates` | `[]` | 候选路径/目录项列表，数量有限。 |
| 33 | `truncated` | `False` | 结果受限是否不完整，需与ok分别判断。 |
| 38 | `truncated` | `True` | 结果受限是否不完整，需与ok分别判断。 |
| 42 | `allowed` | `permissions.resolve_project_path(entry.path)` | 通过边界校验的子目录集合，或是否许可的布尔值。 |
| 45 | `is_directory` | `entry.is_dir(follow_symlinks=False)` | 候选是否为目录，用于导航和显示。 |
| 52 | `relative` | `str(Path(allowed['path']).relative_to(permissions.PROJECT_ROOT))` | 相对项目路径，供显示或范围检查。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 29 | 函数体 | 将 `permissions.resolve_project_path(directory)` 赋给 `checked`。 |
| 30 | 函数体 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 31 | 函数体 / 条件为真 | 返回 `([], False)`，结束当前函数；具体分支见完整源码。 |
| 32 | 函数体 | 将 `[]` 赋给 `candidates`。 |
| 33 | 函数体 | 将 `False` 赋给 `truncated`。 |
| 34 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 35 | 函数体 / try | 进入资源/状态范围：`os.scandir(checked['path'])` 绑定 `entries`；退出执行清理。 |
| 36 | 函数体 / try / with范围 | 遍历 `enumerate(entries)`，每次绑定 `(index, entry)`。 |
| 37 | 函数体 / try / with范围 / 循环每次 | 条件 `index >= 1000 or len(candidates) >= 200`：真时执行body，假时进入else/后续。 |
| 38 | 函数体 / try / with范围 / 循环每次 / 条件为真 | 将 `True` 赋给 `truncated`。 |
| 39 | 函数体 / try / with范围 / 循环每次 / 条件为真 | break结束最近一层循环。 |
| 40 | 函数体 / try / with范围 / 循环每次 | 条件 `not entry.name.startswith(prefix) or entry.is_symlink()`：真时执行body，假时进入else/后续。 |
| 41 | 函数体 / try / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 42 | 函数体 / try / with范围 / 循环每次 | 将 `permissions.resolve_project_path(entry.path)` 赋给 `allowed`。 |
| 43 | 函数体 / try / with范围 / 循环每次 | 条件 `not allowed['ok']`：真时执行body，假时进入else/后续。 |
| 44 | 函数体 / try / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 45 | 函数体 / try / with范围 / 循环每次 | 将 `entry.is_dir(follow_symlinks=False)` 赋给 `is_directory`。 |
| 46 | 函数体 / try / with范围 / 循环每次 | 条件 `is_directory and entry.name in search_config['ignored_directories']`：真时执行body，假时进入else/后续。 |
| 47 | 函数体 / try / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 48 | 函数体 / try / with范围 / 循环每次 | 条件 `directories_only and (not is_directory)`：真时执行body，假时进入else/后续。 |
| 49 | 函数体 / try / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 50 | 函数体 / try / with范围 / 循环每次 | 条件 `not is_directory and (not entry.is_file(follow_symlinks=False))`：真时执行body，假时进入else/后续。 |
| 51 | 函数体 / try / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 52 | 函数体 / try / with范围 / 循环每次 | 将 `str(Path(allowed['path']).relative_to(permissions.PROJECT_ROOT))` 赋给 `relative`。 |
| 53 | 函数体 / try / with范围 / 循环每次 | 计算表达式/调用产生动作：`candidates.append((relative, is_directory))`。 |
| 54 | 函数体 | except OSError：只处理匹配类型的异常。 |
| 55 | 函数体 / except OSError | 返回 `([], False)`，结束当前函数；具体分支见完整源码。 |
| 56 | 函数体 | 返回 `(sorted(candidates, key=lambda item: (not item[1], item[0])), truncated)`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L31：`([], False)`。
- L55：`([], False)`。
- L56：`(sorted(candidates, key=lambda item: (not item[1], item[0])), truncated)`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L19, L34。
- with/yield：资源/状态生命周期或逐个生成：L35。
- lambda：小回调函数：L56。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """路径命令解析和受项目边界约束的文件候选。"""
0002 | import os
0003 | import io
0004 | import shlex
0005 | from pathlib import Path
0006 | 
0007 | import permissions
0008 | from config import search_config
0009 | 
0010 | PATH_COMMANDS = {'/read', '/attach', '/search', '/grep'}
0011 | 
0012 | 
0013 | def parse_path_arguments(text):
0014 |     # 只解析第一个路径；关键词中的空格保持原样。
0015 |     stream = io.StringIO(text)
0016 |     lexer = shlex.shlex(stream, posix=True)
0017 |     lexer.whitespace_split = True
0018 |     lexer.commenters = ''
0019 |     try:
0020 |         path = lexer.get_token()
0021 |     except ValueError as error:
0022 |         raise ValueError('路径格式无效；带空格的路径请使用成对引号') from error
0023 |     if not path:
0024 |         raise ValueError('路径不能为空')
0025 |     return path, stream.read().lstrip()
0026 | 
0027 | 
0028 | def path_candidates(directory, prefix='', directories_only=False):
0029 |     checked = permissions.resolve_project_path(directory)
0030 |     if not checked['ok']:
0031 |         return [], False
0032 |     candidates = []
0033 |     truncated = False
0034 |     try:
0035 |         with os.scandir(checked['path']) as entries:
0036 |             for index, entry in enumerate(entries):
0037 |                 if index >= 1000 or len(candidates) >= 200:
0038 |                     truncated = True
0039 |                     break
0040 |                 if not entry.name.startswith(prefix) or entry.is_symlink():
0041 |                     continue
0042 |                 allowed = permissions.resolve_project_path(entry.path)
0043 |                 if not allowed['ok']:
0044 |                     continue
0045 |                 is_directory = entry.is_dir(follow_symlinks=False)
0046 |                 if is_directory and entry.name in search_config['ignored_directories']:
0047 |                     continue
0048 |                 if directories_only and not is_directory:
0049 |                     continue
0050 |                 if not is_directory and not entry.is_file(follow_symlinks=False):
0051 |                     continue
0052 |                 relative = str(Path(allowed['path']).relative_to(permissions.PROJECT_ROOT))
0053 |                 candidates.append((relative, is_directory))
0054 |     except OSError:
0055 |         return [], False
0056 |     return sorted(candidates, key=lambda item: (not item[1], item[0])), truncated
```
