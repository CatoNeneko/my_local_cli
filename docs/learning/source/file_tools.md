# file_tools.py：源码导读

列目录、有限UTF-8读取、单文件字面搜索。

先读专题：[03-tools.md](../03-tools.md)。

实际源码：[file_tools.py](../../../file_tools.py)。

快照 SHA256：`32e3ba1d0756c8dda059ace65b14fc560b345d17aa0814733076fbb5fba419e9`；76 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 1 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 2 | `from permissions import resolve_project_path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `MAX_READ_BYTES = 1048576` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [list_files](#list-files) | [7](../../../file_tools.py#L7) | 底层列目录并隐藏不合法项；tools同名函数是source=user的统一执行包装。 |
| [read_file](#read-file) | [39](../../../file_tools.py#L39) | 底层有限二进制读取再UTF-8解码；tools同名函数是统一执行包装。 |
| [search_file](#search-file) | [63](../../../file_tools.py#L63) | 底层读文件后逐行字面匹配；tools同名函数是统一执行包装。 |

<a id="list-files"></a>
## list_files

底层列目录并隐藏不合法项；tools同名函数是source=user的统一执行包装。

```python
def list_files(path)
```

位置：[7行](../../../file_tools.py#L7) 至快照 37 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`directory.iterdir`、`entries.append`、`entry.is_dir`、`resolve_project_path`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 8 | `path_result` | `resolve_project_path(path)` | 路径解析检查结果；成功携带真实绝对路径。 |
| 12 | `directory` | `Path(path_result['path'])` | 当前目录路径，遍历/候选/会话使用。 |
| 13 | `entries` | `[]` | 目录项结果列表/扫描迭代器，类型由当前表达式决定。 |
| 17 | `checked` | `resolve_project_path(str(entry))` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 21 | `kind` | `'directory'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 23 | `kind` | `'file'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 8 | 函数体 | 将 `resolve_project_path(path)` 赋给 `path_result`。 |
| 9 | 函数体 | 条件 `not path_result['ok']`：真时执行body，假时进入else/后续。 |
| 10 | 函数体 / 条件为真 | 返回 `path_result`，结束当前函数；具体分支见完整源码。 |
| 12 | 函数体 | 将 `Path(path_result['path'])` 赋给 `directory`。 |
| 13 | 函数体 | 将 `[]` 赋给 `entries`。 |
| 15 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 16 | 函数体 / try | 遍历 `directory.iterdir()`，每次绑定 `entry`。 |
| 17 | 函数体 / try / 循环每次 | 将 `resolve_project_path(str(entry))` 赋给 `checked`。 |
| 18 | 函数体 / try / 循环每次 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 19 | 函数体 / try / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 20 | 函数体 / try / 循环每次 | 条件 `entry.is_dir()`：真时执行body，假时进入else/后续。 |
| 21 | 函数体 / try / 循环每次 / 条件为真 | 将 `'directory'` 赋给 `kind`。 |
| 23 | 函数体 / try / 循环每次 / 条件为假/elif | 将 `'file'` 赋给 `kind`。 |
| 25 | 函数体 / try / 循环每次 | 计算表达式/调用产生动作：`entries.append({'name': entry.name, 'type': kind})`。 |
| 30 | 函数体 / try | 返回 `{'ok': True, 'entries': entries}`，结束当前函数；具体分支见完整源码。 |
| 32 | 函数体 | except FileNotFoundError：只处理匹配类型的异常。 |
| 33 | 函数体 / except FileNotFoundError | 返回 `{'ok': False, 'error': '目录不存在'}`，结束当前函数；具体分支见完整源码。 |
| 34 | 函数体 | except NotADirectoryError：只处理匹配类型的异常。 |
| 35 | 函数体 / except NotADirectoryError | 返回 `{'ok': False, 'error': '路径不是目录'}`，结束当前函数；具体分支见完整源码。 |
| 36 | 函数体 | except PermissionError：只处理匹配类型的异常。 |
| 37 | 函数体 / except PermissionError | 返回 `{'ok': False, 'error': '没有访问目录的权限'}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L10：`path_result`。
- L30：`{'ok': True, 'entries': entries}`。
- L33：`{'ok': False, 'error': '目录不存在'}`。
- L35：`{'ok': False, 'error': '路径不是目录'}`。
- L37：`{'ok': False, 'error': '没有访问目录的权限'}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="read-file"></a>
## read_file

底层有限二进制读取再UTF-8解码；tools同名函数是统一执行包装。

```python
def read_file(path)
```

位置：[39行](../../../file_tools.py#L39) 至快照 61 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |

**调用表达式（静态提取，不含内层独立函数体）**：`content.decode`、`file.read`、`len`、`open`、`resolve_project_path`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 41 | `path_result` | `resolve_project_path(path)` | 路径解析检查结果；成功携带真实绝对路径。 |
| 46 | `path` | `path_result['path']` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| 50 | `content` | `file.read(MAX_READ_BYTES + 1)` | 文件正文、消息文字或累计响应；看role与来源。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 41 | 函数体 | 将 `resolve_project_path(path)` 赋给 `path_result`。 |
| 43 | 函数体 | 条件 `not path_result['ok']`：真时执行body，假时进入else/后续。 |
| 44 | 函数体 / 条件为真 | 返回 `path_result`，结束当前函数；具体分支见完整源码。 |
| 46 | 函数体 | 将 `path_result['path']` 赋给 `path`。 |
| 48 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 49 | 函数体 / try | 进入资源/状态范围：`open(path, 'rb')` 绑定 `file`；退出执行清理。 |
| 50 | 函数体 / try / with范围 | 将 `file.read(MAX_READ_BYTES + 1)` 赋给 `content`。 |
| 51 | 函数体 / try | 条件 `len(content) > MAX_READ_BYTES`：真时执行body，假时进入else/后续。 |
| 52 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': '读取文件超过 1 MiB 上限，请用项目搜索定位内容'}`，结束当前函数；具体分支见完整源码。 |
| 53 | 函数体 / try | 返回 `{'ok': True, 'content': content.decode('utf-8')}`，结束当前函数；具体分支见完整源码。 |
| 54 | 函数体 | except FileNotFoundError：只处理匹配类型的异常。 |
| 55 | 函数体 / except FileNotFoundError | 返回 `{'ok': False, 'error': 'file not found'}`，结束当前函数；具体分支见完整源码。 |
| 56 | 函数体 | except IsADirectoryError：只处理匹配类型的异常。 |
| 57 | 函数体 / except IsADirectoryError | 返回 `{'ok': False, 'error': 'this is a folder'}`，结束当前函数；具体分支见完整源码。 |
| 58 | 函数体 | except PermissionError：只处理匹配类型的异常。 |
| 59 | 函数体 / except PermissionError | 返回 `{'ok': False, 'error': 'permission denied'}`，结束当前函数；具体分支见完整源码。 |
| 60 | 函数体 | except UnicodeDecodeError：只处理匹配类型的异常。 |
| 61 | 函数体 / except UnicodeDecodeError | 返回 `{'ok': False, 'error': 'this is not utf-8'}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L44：`path_result`。
- L52：`{'ok': False, 'error': '读取文件超过 1 MiB 上限，请用项目搜索定位内容'}`。
- L53：`{'ok': True, 'content': content.decode('utf-8')}`。
- L55：`{'ok': False, 'error': 'file not found'}`。
- L57：`{'ok': False, 'error': 'this is a folder'}`。
- L59：`{'ok': False, 'error': 'permission denied'}`。
- L61：`{'ok': False, 'error': 'this is not utf-8'}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="search-file"></a>
## search_file

底层读文件后逐行字面匹配；tools同名函数是统一执行包装。

```python
def search_file(path, keyword)
```

位置：[63行](../../../file_tools.py#L63) 至快照 76 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| `keyword` | `未显式注解` | 字面查找的非空文字，非正则表达式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`matches.append`、`read_file`、`result['content'].splitlines`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 65 | `result` | `read_file(path)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 69 | `matches` | `[]` | 文字搜索实际匹配记录列表；空列表表示无匹配。 |
| 70 | `line_number` | `1` | 人可读1起始行号，不是字符/字节偏移。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 65 | 函数体 | 将 `read_file(path)` 赋给 `result`。 |
| 66 | 函数体 | 条件 `not result['ok']`：真时执行body，假时进入else/后续。 |
| 67 | 函数体 / 条件为真 | 返回 `result`，结束当前函数；具体分支见完整源码。 |
| 69 | 函数体 | 将 `[]` 赋给 `matches`。 |
| 70 | 函数体 | 将 `1` 赋给 `line_number`。 |
| 72 | 函数体 | 遍历 `result['content'].splitlines()`，每次绑定 `line`。 |
| 73 | 函数体 / 循环每次 | 条件 `keyword in line`：真时执行body，假时进入else/后续。 |
| 74 | 函数体 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`matches.append({'line_number': line_number, 'content': line})`。 |
| 75 | 函数体 / 循环每次 | 更新已有变量：`line_number += 1`。 |
| 76 | 函数体 | 返回 `{'ok': True, 'matches': matches}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L67：`result`。
- L76：`{'ok': True, 'matches': matches}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L15, L48。
- with/yield：资源/状态生命周期或逐个生成：L49。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | from pathlib import Path
0002 | from permissions import resolve_project_path
0003 | 
0004 | MAX_READ_BYTES = 1048576
0005 | 
0006 | 
0007 | def list_files(path):
0008 |     path_result = resolve_project_path(path)
0009 |     if not path_result["ok"]:
0010 |         return path_result
0011 | 
0012 |     directory = Path(path_result["path"])
0013 |     entries = []
0014 | 
0015 |     try:
0016 |         for entry in directory.iterdir():
0017 |             checked = resolve_project_path(str(entry))
0018 |             if not checked["ok"]:
0019 |                 continue
0020 |             if entry.is_dir():
0021 |                 kind = "directory"
0022 |             else:
0023 |                 kind = "file"
0024 | 
0025 |             entries.append({
0026 |                 "name": entry.name,
0027 |                 "type": kind
0028 |             })
0029 | 
0030 |         return {"ok": True, "entries": entries}
0031 | 
0032 |     except FileNotFoundError:
0033 |         return {"ok": False, "error": "目录不存在"}
0034 |     except NotADirectoryError:
0035 |         return {"ok": False, "error": "路径不是目录"}
0036 |     except PermissionError:
0037 |         return {"ok": False, "error": "没有访问目录的权限"}
0038 | 
0039 | def read_file(path):
0040 | 
0041 |     path_result = resolve_project_path(path)
0042 | 
0043 |     if not path_result["ok"]:
0044 |         return path_result
0045 | 
0046 |     path = path_result["path"]
0047 | 
0048 |     try:
0049 |         with open(path, 'rb') as file:
0050 |             content = file.read(MAX_READ_BYTES + 1)
0051 |         if len(content) > MAX_READ_BYTES:
0052 |             return {'ok': False, 'error': '读取文件超过 1 MiB 上限，请用项目搜索定位内容'}
0053 |         return {'ok': True, 'content': content.decode('utf-8')}
0054 |     except FileNotFoundError:
0055 |         return {'ok': False, 'error': 'file not found'}
0056 |     except IsADirectoryError:
0057 |         return {'ok': False, 'error': 'this is a folder'}
0058 |     except PermissionError:
0059 |         return {'ok': False, 'error': 'permission denied'}
0060 |     except UnicodeDecodeError:
0061 |         return {'ok': False, 'error': 'this is not utf-8'}
0062 | 
0063 | def search_file(path, keyword):
0064 | 
0065 |     result = read_file(path)
0066 |     if not result['ok']:
0067 |         return result
0068 | 
0069 |     matches = []
0070 |     line_number = 1
0071 | 
0072 |     for line in result['content'].splitlines():
0073 |         if keyword in line:
0074 |             matches.append({'line_number': line_number, 'content': line})
0075 |         line_number += 1
0076 |     return {'ok': True, 'matches': matches}
```
