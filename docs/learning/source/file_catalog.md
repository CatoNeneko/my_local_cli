# file_catalog.py：源码导读

有限目录索引和文件名模糊排序；不读取正文、不调用模型。

先读专题：[07-terminal.md](../07-terminal.md)。

实际源码：[file_catalog.py](../../../file_catalog.py)。

快照 SHA256：`f2f9fbdae75cb4cb10e16f97c2aac20754e2672a94e1f7eff88e21ecfcb9182b`；79 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import os` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import time` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `import permissions` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `from config import search_config` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 9 | `MAX_FILES = 5000` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 10 | `MAX_ENTRIES = 20000` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 11 | `SCAN_SECONDS = 2` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [scan_files](#scan-files) | [14](../../../file_catalog.py#L14) | 有限stack/scandir目录索引，跳私有/链接/依赖。 |
| [fuzzy_score](#fuzzy-score) | [55](../../../file_catalog.py#L55) | 按顺序匹配query字符，计算空隙与文件名优先排名。 |
| [matching_files](#matching-files) | [73](../../../file_catalog.py#L73) | 计算有效候选score并排序输出路径。 |

<a id="scan-files"></a>
## scan_files

有限stack/scandir目录索引，跳私有/链接/依赖。

```python
def scan_files()
```

位置：[14行](../../../file_catalog.py#L14) 至快照 52 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`Path(checked['path']).relative_to`、`bool`、`entry.is_dir`、`entry.is_file`、`entry.is_symlink`、`files.append`、`len`、`os.scandir`、`permissions.resolve_project_path`、`sorted`、`stack.append`、`stack.pop`、`str`、`time.monotonic`、`warnings.append`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 15 | `files` | `[]` | 目录项文件名集合或索引，非文件正文。 |
| 16 | `stack` | `[permissions.PROJECT_ROOT]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 17 | `visited` | `0` | 已检查目录项计数，用于扫描限额。 |
| 18 | `deadline` | `time.monotonic() + SCAN_SECONDS` | monotonic算出的结束时刻，不受墙上时钟调整影响。 |
| 19 | `reason` | `''` | 明确终止/审批/截断原因，不根据正文措辞推断。 |
| 20 | `warnings` | `[]` | 有限警告集合；部分结果仍可能ok=True。 |
| 23 | `reason` | `'扫描时间上限'` | 明确终止/审批/截断原因，不根据正文措辞推断。 |
| 25 | `directory` | `stack.pop()` | 当前目录路径，遍历/候选/会话使用。 |
| 31 | `reason` | `'目录项数量上限'` | 明确终止/审批/截断原因，不根据正文措辞推断。 |
| 34 | `reason` | `'扫描时间上限'` | 明确终止/审批/截断原因，不根据正文措辞推断。 |
| 38 | `checked` | `permissions.resolve_project_path(entry.path)` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 47 | `reason` | `'文件数量上限'` | 明确终止/审批/截断原因，不根据正文措辞推断。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 15 | 函数体 | 将 `[]` 赋给 `files`。 |
| 16 | 函数体 | 将 `[permissions.PROJECT_ROOT]` 赋给 `stack`。 |
| 17 | 函数体 | 将 `0` 赋给 `visited`。 |
| 18 | 函数体 | 将 `time.monotonic() + SCAN_SECONDS` 赋给 `deadline`。 |
| 19 | 函数体 | 将 `''` 赋给 `reason`。 |
| 20 | 函数体 | 将 `[]` 赋给 `warnings`。 |
| 21 | 函数体 | 循环检查 `stack and (not reason)`，break/return/异常可结束。 |
| 22 | 函数体 / 循环每次 | 条件 `time.monotonic() >= deadline`：真时执行body，假时进入else/后续。 |
| 23 | 函数体 / 循环每次 / 条件为真 | 将 `'扫描时间上限'` 赋给 `reason`。 |
| 24 | 函数体 / 循环每次 / 条件为真 | break结束最近一层循环。 |
| 25 | 函数体 / 循环每次 | 将 `stack.pop()` 赋给 `directory`。 |
| 26 | 函数体 / 循环每次 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 27 | 函数体 / 循环每次 / try | 进入资源/状态范围：`os.scandir(directory)` 绑定 `entries`；退出执行清理。 |
| 28 | 函数体 / 循环每次 / try / with范围 | 遍历 `entries`，每次绑定 `entry`。 |
| 29 | 函数体 / 循环每次 / try / with范围 / 循环每次 | 更新已有变量：`visited += 1`。 |
| 30 | 函数体 / 循环每次 / try / with范围 / 循环每次 | 条件 `visited > MAX_ENTRIES`：真时执行body，假时进入else/后续。 |
| 31 | 函数体 / 循环每次 / try / with范围 / 循环每次 / 条件为真 | 将 `'目录项数量上限'` 赋给 `reason`。 |
| 32 | 函数体 / 循环每次 / try / with范围 / 循环每次 / 条件为真 | break结束最近一层循环。 |
| 33 | 函数体 / 循环每次 / try / with范围 / 循环每次 | 条件 `time.monotonic() >= deadline`：真时执行body，假时进入else/后续。 |
| 34 | 函数体 / 循环每次 / try / with范围 / 循环每次 / 条件为真 | 将 `'扫描时间上限'` 赋给 `reason`。 |
| 35 | 函数体 / 循环每次 / try / with范围 / 循环每次 / 条件为真 | break结束最近一层循环。 |
| 36 | 函数体 / 循环每次 / try / with范围 / 循环每次 | 条件 `entry.is_symlink()`：真时执行body，假时进入else/后续。 |
| 37 | 函数体 / 循环每次 / try / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 38 | 函数体 / 循环每次 / try / with范围 / 循环每次 | 将 `permissions.resolve_project_path(entry.path)` 赋给 `checked`。 |
| 39 | 函数体 / 循环每次 / try / with范围 / 循环每次 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 40 | 函数体 / 循环每次 / try / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 41 | 函数体 / 循环每次 / try / with范围 / 循环每次 | 条件 `entry.is_dir(follow_symlinks=False)`：真时执行body，假时进入else/后续。 |
| 42 | 函数体 / 循环每次 / try / with范围 / 循环每次 / 条件为真 | 条件 `entry.name not in search_config['ignored_directories']`：真时执行body，假时进入else/后续。 |
| 43 | 函数体 / 循环每次 / try / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`stack.append(Path(entry.path))`。 |
| 44 | 函数体 / 循环每次 / try / with范围 / 循环每次 / 条件为假/elif | 条件 `entry.is_file(follow_symlinks=False)`：真时执行body，假时进入else/后续。 |
| 45 | 函数体 / 循环每次 / try / with范围 / 循环每次 / 条件为假/elif / 条件为真 | 计算表达式/调用产生动作：`files.append(str(Path(checked['path']).relative_to(permissions.PROJECT_ROOT)))`。 |
| 46 | 函数体 / 循环每次 / try / with范围 / 循环每次 / 条件为假/elif / 条件为真 | 条件 `len(files) >= MAX_FILES`：真时执行body，假时进入else/后续。 |
| 47 | 函数体 / 循环每次 / try / with范围 / 循环每次 / 条件为假/elif / 条件为真 / 条件为真 | 将 `'文件数量上限'` 赋给 `reason`。 |
| 48 | 函数体 / 循环每次 / try / with范围 / 循环每次 / 条件为假/elif / 条件为真 / 条件为真 | break结束最近一层循环。 |
| 49 | 函数体 / 循环每次 | except OSError as error：只处理匹配类型的异常。 |
| 50 | 函数体 / 循环每次 / except OSError as error | 条件 `len(warnings) < 5`：真时执行body，假时进入else/后续。 |
| 51 | 函数体 / 循环每次 / except OSError as error / 条件为真 | 计算表达式/调用产生动作：`warnings.append('跳过无法读取的目录: ' + str(error))`。 |
| 52 | 函数体 | 返回 `{'files': sorted(files), 'truncated': bool(reason), 'reason': reason, 'warnings': warnings}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L52：`{'files': sorted(files), 'truncated': bool(reason), 'reason': reason, 'warnings': warnings}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="fuzzy-score"></a>
## fuzzy_score

按顺序匹配query字符，计算空隙与文件名优先排名。

```python
def fuzzy_score(query, path)
```

位置：[55行](../../../file_catalog.py#L55) 至快照 70 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `query` | `未显式注解` | 筛选文字或Buffer对象，回调读取其text。 |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`Path(path).name.casefold`、`len`、`path.casefold`、`positions.append`、`query.casefold`、`query.casefold().split`、`text.find`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 56 | `text` | `path.casefold()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 57 | `tokens` | `query.casefold().split()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 58 | `gap` | `0` | 模糊文件名匹配中字符间额外空隙，总间隙越小越优先。 |
| 60 | `cursor` | `0` | 分页/模糊查找位置，具体按调用来源判断。 |
| 61 | `positions` | `[]` | 候选字符位置列表，或用户轮次在历史中的位置。 |
| 63 | `position` | `text.find(char, cursor)` | 关键词/字符在字符串中的索引，找不到常为-1。 |
| 67 | `cursor` | `position + 1` | 分页/模糊查找位置，具体按调用来源判断。 |
| 69 | `basename` | `Path(path).name.casefold()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 56 | 函数体 | 将 `path.casefold()` 赋给 `text`。 |
| 57 | 函数体 | 将 `query.casefold().split()` 赋给 `tokens`。 |
| 58 | 函数体 | 将 `0` 赋给 `gap`。 |
| 59 | 函数体 | 遍历 `tokens`，每次绑定 `token`。 |
| 60 | 函数体 / 循环每次 | 将 `0` 赋给 `cursor`。 |
| 61 | 函数体 / 循环每次 | 将 `[]` 赋给 `positions`。 |
| 62 | 函数体 / 循环每次 | 遍历 `token`，每次绑定 `char`。 |
| 63 | 函数体 / 循环每次 / 循环每次 | 将 `text.find(char, cursor)` 赋给 `position`。 |
| 64 | 函数体 / 循环每次 / 循环每次 | 条件 `position < 0`：真时执行body，假时进入else/后续。 |
| 65 | 函数体 / 循环每次 / 循环每次 / 条件为真 | 返回 `None`，结束当前函数；具体分支见完整源码。 |
| 66 | 函数体 / 循环每次 / 循环每次 | 计算表达式/调用产生动作：`positions.append(position)`。 |
| 67 | 函数体 / 循环每次 / 循环每次 | 将 `position + 1` 赋给 `cursor`。 |
| 68 | 函数体 / 循环每次 | 更新已有变量：`gap += positions[-1] - positions[0] + 1 - len(token)`。 |
| 69 | 函数体 | 将 `Path(path).name.casefold()` 赋给 `basename`。 |
| 70 | 函数体 | 返回 `(0 if query.casefold() in basename else 1, gap, len(path), path)`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L65：`None`。
- L70：`(0 if query.casefold() in basename else 1, gap, len(path), path)`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="matching-files"></a>
## matching_files

计算有效候选score并排序输出路径。

```python
def matching_files(paths, query)
```

位置：[73行](../../../file_catalog.py#L73) 至快照 79 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `paths` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `query` | `未显式注解` | 筛选文字或Buffer对象，回调读取其text。 |

**调用表达式（静态提取，不含内层独立函数体）**：`fuzzy_score`、`ranked.append`、`sorted`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 74 | `ranked` | `[]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 76 | `score` | `fuzzy_score(query, path)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 74 | 函数体 | 将 `[]` 赋给 `ranked`。 |
| 75 | 函数体 | 遍历 `paths`，每次绑定 `path`。 |
| 76 | 函数体 / 循环每次 | 将 `fuzzy_score(query, path)` 赋给 `score`。 |
| 77 | 函数体 / 循环每次 | 条件 `score is not None`：真时执行body，假时进入else/后续。 |
| 78 | 函数体 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`ranked.append((score, path))`。 |
| 79 | 函数体 | 返回 `[path for _, path in sorted(ranked)]`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L79：`[path for _, path in sorted(ranked)]`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L26。
- 推导式/生成器表达式：循环建容器或逐个产生：L79。
- with/yield：资源/状态生命周期或逐个生成：L27。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """有限扫描的项目文件索引与文件名模糊匹配，不读取文件正文。"""
0002 | import os
0003 | import time
0004 | from pathlib import Path
0005 | 
0006 | import permissions
0007 | from config import search_config
0008 | 
0009 | MAX_FILES = 5000
0010 | MAX_ENTRIES = 20000
0011 | SCAN_SECONDS = 2
0012 | 
0013 | 
0014 | def scan_files():
0015 |     files = []
0016 |     stack = [permissions.PROJECT_ROOT]
0017 |     visited = 0
0018 |     deadline = time.monotonic() + SCAN_SECONDS
0019 |     reason = ''
0020 |     warnings = []
0021 |     while stack and not reason:
0022 |         if time.monotonic() >= deadline:
0023 |             reason = '扫描时间上限'
0024 |             break
0025 |         directory = stack.pop()
0026 |         try:
0027 |             with os.scandir(directory) as entries:
0028 |                 for entry in entries:
0029 |                     visited += 1
0030 |                     if visited > MAX_ENTRIES:
0031 |                         reason = '目录项数量上限'
0032 |                         break
0033 |                     if time.monotonic() >= deadline:
0034 |                         reason = '扫描时间上限'
0035 |                         break
0036 |                     if entry.is_symlink():
0037 |                         continue
0038 |                     checked = permissions.resolve_project_path(entry.path)
0039 |                     if not checked['ok']:
0040 |                         continue
0041 |                     if entry.is_dir(follow_symlinks=False):
0042 |                         if entry.name not in search_config['ignored_directories']:
0043 |                             stack.append(Path(entry.path))
0044 |                     elif entry.is_file(follow_symlinks=False):
0045 |                         files.append(str(Path(checked['path']).relative_to(permissions.PROJECT_ROOT)))
0046 |                         if len(files) >= MAX_FILES:
0047 |                             reason = '文件数量上限'
0048 |                             break
0049 |         except OSError as error:
0050 |             if len(warnings) < 5:
0051 |                 warnings.append('跳过无法读取的目录: ' + str(error))
0052 |     return {'files': sorted(files), 'truncated': bool(reason), 'reason': reason, 'warnings': warnings}
0053 | 
0054 | 
0055 | def fuzzy_score(query, path):
0056 |     text = path.casefold()
0057 |     tokens = query.casefold().split()
0058 |     gap = 0
0059 |     for token in tokens:
0060 |         cursor = 0
0061 |         positions = []
0062 |         for char in token:
0063 |             position = text.find(char, cursor)
0064 |             if position < 0:
0065 |                 return None
0066 |             positions.append(position)
0067 |             cursor = position + 1
0068 |         gap += positions[-1] - positions[0] + 1 - len(token)
0069 |     basename = Path(path).name.casefold()
0070 |     return (0 if query.casefold() in basename else 1, gap, len(path), path)
0071 | 
0072 | 
0073 | def matching_files(paths, query):
0074 |     ranked = []
0075 |     for path in paths:
0076 |         score = fuzzy_score(query, path)
0077 |         if score is not None:
0078 |             ranked.append((score, path))
0079 |     return [path for _, path in sorted(ranked)]
```
