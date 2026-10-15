# project_search.py：源码导读

限时间、文件/字节/结果规模的递归正文搜索，返回部分结果状态。

先读专题：[03-tools.md](../03-tools.md)。

实际源码：[project_search.py](../../../project_search.py)。

快照 SHA256：`d02aca8a46ef83a9cf0a34376bcaedb0ee7c202349ae934f1488360e8e11f9f2`；116 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import fnmatch` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `import os` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `import time` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `import permissions` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 9 | `from config import search_config` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [search_project](#search-project) | [12](../../../project_search.py#L12) | 有界递归正文搜索；tools同名函数提供path/glob默认值并转统一执行。 |
| [search_project.result](#search-project-result) | [33](../../../project_search.py#L33) | 将本次搜索matches/统计/warnings及可选截断原因组装成成功返回。 |
| [search_project.walk_error](#search-project-walk-error) | [38](../../../project_search.py#L38) | 目录遍历失败时计unreadable并加入有限警告，不假装全部扫描。 |

<a id="search-project"></a>
## search_project

有界递归正文搜索；tools同名函数提供path/glob默认值并转统一执行。

```python
def search_project(path, keyword, glob='*')
```

位置：[12行](../../../project_search.py#L12) 至快照 116 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| `keyword` | `未显式注解` | 字面查找的非空文字，非正则表达式。 |
| `glob` | `未显式注解` | 文件名/相对路径匹配模式，例如*.py。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`allowed.append`、`any`、`enumerate`、`file.read`、`fnmatch.fnmatchcase`、`isinstance`、`item.is_file`、`item.is_symlink`、`item.relative_to`、`item.stat`、`json.dumps`、`len`、`line.find`、`matches.append`、`max`、`min`、`open`、`os.walk`、`permissions.resolve_project_path`、`raw.decode`、`result`、`root.is_dir`、`search_config.get`、`set`、`sorted`、`str`、`text.splitlines`、`time.monotonic`、`type`、`warnings.append`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 13 | `checked` | `permissions.resolve_project_path(path)` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 18 | `root` | `Path(checked['path'])` | 本次目录扫描/工作项目根。 |
| 21 | `numeric_keys` | `['max_files', 'max_file_bytes', 'max_total_bytes', 'max_matches', 'max_output_chars', 'timeout_seconds']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 24 | `matches` | `[]` | 文字搜索实际匹配记录列表；空列表表示无匹配。 |
| 25 | `warnings` | `[]` | 有限警告集合；部分结果仍可能ok=True。 |
| 26 | `skipped` | `{'protected_or_link': 0, 'large': 0, 'non_text': 0, 'unreadable': 0}` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 27 | `scanned` | `0` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 28 | `total_bytes` | `0` | 本次搜索/读取累计字节，用于总额限制。 |
| 29 | `output_chars` | `0` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 30 | `deadline` | `time.monotonic() + search_config['timeout_seconds']` | monotonic算出的结束时刻，不受墙上时钟调整影响。 |
| 31 | `ignored` | `set(search_config['ignored_directories'])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 46 | `allowed` | `[]` | 通过边界校验的子目录集合，或是否许可的布尔值。 |
| 50 | `item` | `Path(directory) / name` | 遍历中的一项：字段、文件、消息或工具定义，类型取决于iter。 |
| 55 | `directories[:]` | `allowed` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 59 | `item` | `Path(directory) / name` | 遍历中的一项：字段、文件、消息或工具定义，类型取决于iter。 |
| 60 | `checked` | `permissions.resolve_project_path(str(item))` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 64 | `relative` | `str(item.relative_to(permissions.PROJECT_ROOT))` | 相对项目路径，供显示或范围检查。 |
| 76 | `remaining` | `search_config['max_total_bytes'] - total_bytes` | 还可读取/保存的字节配额。 |
| 80 | `raw` | `file.read(min(search_config['max_file_bytes'], remaining) + 1)` | 未解码字节/完整输出快照，按编码与限额再处理。 |
| 90 | `text` | `raw.decode('utf-8-sig')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 102 | `position` | `line.find(keyword)` | 关键词/字符在字符串中的索引，找不到常为-1。 |
| 105 | `start` | `max(0, position - 100) if len(line) > 500 else 0` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 106 | `snippet` | `line[start:start + 500]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 107 | `entry` | `{'path': relative, 'line_number': number, 'content': snippet, 'content_truncated': start > 0 or start + len(snippet) < len(line)}` | 一条目录项或匹配结果字典。 |
| 109 | `size` | `len(json.dumps(entry, ensure_ascii=False))` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 13 | 函数体 | 将 `permissions.resolve_project_path(path)` 赋给 `checked`。 |
| 14 | 函数体 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 15 | 函数体 / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 16 | 函数体 | 条件 `not isinstance(keyword, str) or not keyword or (not isinstance(glob, str)) or (not glob)`：真时执行body，假时进入else/后续。 |
| 17 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '关键词和文件匹配模式不能为空'}`，结束当前函数；具体分支见完整源码。 |
| 18 | 函数体 | 将 `Path(checked['path'])` 赋给 `root`。 |
| 19 | 函数体 | 条件 `not root.is_dir()`：真时执行body，假时进入else/后续。 |
| 20 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '项目搜索目标必须是存在的目录'}`，结束当前函数；具体分支见完整源码。 |
| 21 | 函数体 | 将 `['max_files', 'max_file_bytes', 'max_total_bytes', 'max_matches', 'max_output_chars', 'timeout_seconds']` 赋给 `numeric_keys`。 |
| 22 | 函数体 | 条件 `any((type(search_config.get(key)) is not int or search_config[key] <= 0 for key in numeric_keys))`：真时执行body，假时进入else/后续。 |
| 23 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '搜索限制必须是正整数'}`，结束当前函数；具体分支见完整源码。 |
| 24 | 函数体 | 将 `[]` 赋给 `matches`。 |
| 25 | 函数体 | 将 `[]` 赋给 `warnings`。 |
| 26 | 函数体 | 将 `{'protected_or_link': 0, 'large': 0, 'non_text': 0, 'unreadable': 0}` 赋给 `skipped`。 |
| 27 | 函数体 | 将 `0` 赋给 `scanned`。 |
| 28 | 函数体 | 将 `0` 赋给 `total_bytes`。 |
| 29 | 函数体 | 将 `0` 赋给 `output_chars`。 |
| 30 | 函数体 | 将 `time.monotonic() + search_config['timeout_seconds']` 赋给 `deadline`。 |
| 31 | 函数体 | 将 `set(search_config['ignored_directories'])` 赋给 `ignored`。 |
| 33 | 函数体 | 定义嵌套函数 `result`；定义本身不执行函数体。 |
| 38 | 函数体 | 定义嵌套函数 `walk_error`；定义本身不执行函数体。 |
| 43 | 函数体 | 遍历 `os.walk(root, followlinks=False, onerror=walk_error)`，每次绑定 `(directory, directories, files)`。 |
| 44 | 函数体 / 循环每次 | 条件 `time.monotonic() >= deadline`：真时执行body，假时进入else/后续。 |
| 45 | 函数体 / 循环每次 / 条件为真 | 返回 `result('搜索时间上限')`，结束当前函数；具体分支见完整源码。 |
| 46 | 函数体 / 循环每次 | 将 `[]` 赋给 `allowed`。 |
| 47 | 函数体 / 循环每次 | 遍历 `sorted(directories)`，每次绑定 `name`。 |
| 48 | 函数体 / 循环每次 / 循环每次 | 条件 `time.monotonic() >= deadline`：真时执行body，假时进入else/后续。 |
| 49 | 函数体 / 循环每次 / 循环每次 / 条件为真 | 返回 `result('搜索时间上限')`，结束当前函数；具体分支见完整源码。 |
| 50 | 函数体 / 循环每次 / 循环每次 | 将 `Path(directory) / name` 赋给 `item`。 |
| 51 | 函数体 / 循环每次 / 循环每次 | 条件 `name in ignored or item.is_symlink() or (not permissions.resolve_project_path(str(item))['ok'])`：真时执行body，假时进入else/后续。 |
| 52 | 函数体 / 循环每次 / 循环每次 / 条件为真 | 更新已有变量：`skipped['protected_or_link'] += 1`。 |
| 54 | 函数体 / 循环每次 / 循环每次 / 条件为假/elif | 计算表达式/调用产生动作：`allowed.append(name)`。 |
| 55 | 函数体 / 循环每次 | 将 `allowed` 赋给 `directories[:]`。 |
| 56 | 函数体 / 循环每次 | 遍历 `sorted(files)`，每次绑定 `name`。 |
| 57 | 函数体 / 循环每次 / 循环每次 | 条件 `time.monotonic() >= deadline`：真时执行body，假时进入else/后续。 |
| 58 | 函数体 / 循环每次 / 循环每次 / 条件为真 | 返回 `result('搜索时间上限')`，结束当前函数；具体分支见完整源码。 |
| 59 | 函数体 / 循环每次 / 循环每次 | 将 `Path(directory) / name` 赋给 `item`。 |
| 60 | 函数体 / 循环每次 / 循环每次 | 将 `permissions.resolve_project_path(str(item))` 赋给 `checked`。 |
| 61 | 函数体 / 循环每次 / 循环每次 | 条件 `item.is_symlink() or not checked['ok']`：真时执行body，假时进入else/后续。 |
| 62 | 函数体 / 循环每次 / 循环每次 / 条件为真 | 更新已有变量：`skipped['protected_or_link'] += 1`。 |
| 63 | 函数体 / 循环每次 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 64 | 函数体 / 循环每次 / 循环每次 | 将 `str(item.relative_to(permissions.PROJECT_ROOT))` 赋给 `relative`。 |
| 65 | 函数体 / 循环每次 / 循环每次 | 条件 `not fnmatch.fnmatchcase(relative, glob) and (not fnmatch.fnmatchcase(name, glob))`：真时执行body，假时进入else/后续。 |
| 66 | 函数体 / 循环每次 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 67 | 函数体 / 循环每次 / 循环每次 | 条件 `scanned >= search_config['max_files']`：真时执行body，假时进入else/后续。 |
| 68 | 函数体 / 循环每次 / 循环每次 / 条件为真 | 返回 `result('扫描文件数量上限')`，结束当前函数；具体分支见完整源码。 |
| 69 | 函数体 / 循环每次 / 循环每次 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 70 | 函数体 / 循环每次 / 循环每次 / try | 条件 `not item.is_file()`：真时执行body，假时进入else/后续。 |
| 71 | 函数体 / 循环每次 / 循环每次 / try / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 72 | 函数体 / 循环每次 / 循环每次 / try | 更新已有变量：`scanned += 1`。 |
| 73 | 函数体 / 循环每次 / 循环每次 / try | 条件 `item.stat().st_size > search_config['max_file_bytes']`：真时执行body，假时进入else/后续。 |
| 74 | 函数体 / 循环每次 / 循环每次 / try / 条件为真 | 更新已有变量：`skipped['large'] += 1`。 |
| 75 | 函数体 / 循环每次 / 循环每次 / try / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 76 | 函数体 / 循环每次 / 循环每次 / try | 将 `search_config['max_total_bytes'] - total_bytes` 赋给 `remaining`。 |
| 77 | 函数体 / 循环每次 / 循环每次 / try | 条件 `remaining <= 0`：真时执行body，假时进入else/后续。 |
| 78 | 函数体 / 循环每次 / 循环每次 / try / 条件为真 | 返回 `result('总读取字节上限')`，结束当前函数；具体分支见完整源码。 |
| 79 | 函数体 / 循环每次 / 循环每次 / try | 进入资源/状态范围：`open(checked['path'], 'rb')` 绑定 `file`；退出执行清理。 |
| 80 | 函数体 / 循环每次 / 循环每次 / try / with范围 | 将 `file.read(min(search_config['max_file_bytes'], remaining) + 1)` 赋给 `raw`。 |
| 81 | 函数体 / 循环每次 / 循环每次 / try | 更新已有变量：`total_bytes += len(raw)`。 |
| 82 | 函数体 / 循环每次 / 循环每次 / try | 条件 `len(raw) > remaining`：真时执行body，假时进入else/后续。 |
| 83 | 函数体 / 循环每次 / 循环每次 / try / 条件为真 | 返回 `result('总读取字节上限')`，结束当前函数；具体分支见完整源码。 |
| 84 | 函数体 / 循环每次 / 循环每次 / try | 条件 `len(raw) > search_config['max_file_bytes']`：真时执行body，假时进入else/后续。 |
| 85 | 函数体 / 循环每次 / 循环每次 / try / 条件为真 | 更新已有变量：`skipped['large'] += 1`。 |
| 86 | 函数体 / 循环每次 / 循环每次 / try / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 87 | 函数体 / 循环每次 / 循环每次 / try | 条件 `b'\x00' in raw`：真时执行body，假时进入else/后续。 |
| 88 | 函数体 / 循环每次 / 循环每次 / try / 条件为真 | 更新已有变量：`skipped['non_text'] += 1`。 |
| 89 | 函数体 / 循环每次 / 循环每次 / try / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 90 | 函数体 / 循环每次 / 循环每次 / try | 将 `raw.decode('utf-8-sig')` 赋给 `text`。 |
| 91 | 函数体 / 循环每次 / 循环每次 | except UnicodeError：只处理匹配类型的异常。 |
| 92 | 函数体 / 循环每次 / 循环每次 / except UnicodeError | 更新已有变量：`skipped['non_text'] += 1`。 |
| 93 | 函数体 / 循环每次 / 循环每次 / except UnicodeError | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 94 | 函数体 / 循环每次 / 循环每次 | except OSError as error：只处理匹配类型的异常。 |
| 95 | 函数体 / 循环每次 / 循环每次 / except OSError as error | 更新已有变量：`skipped['unreadable'] += 1`。 |
| 96 | 函数体 / 循环每次 / 循环每次 / except OSError as error | 条件 `len(warnings) < 10`：真时执行body，假时进入else/后续。 |
| 97 | 函数体 / 循环每次 / 循环每次 / except OSError as error / 条件为真 | 计算表达式/调用产生动作：`warnings.append('部分文件无法读取: ' + type(error).__name__)`。 |
| 98 | 函数体 / 循环每次 / 循环每次 / except OSError as error | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 99 | 函数体 / 循环每次 / 循环每次 | 遍历 `enumerate(text.splitlines(), start=1)`，每次绑定 `(number, line)`。 |
| 100 | 函数体 / 循环每次 / 循环每次 / 循环每次 | 条件 `time.monotonic() >= deadline`：真时执行body，假时进入else/后续。 |
| 101 | 函数体 / 循环每次 / 循环每次 / 循环每次 / 条件为真 | 返回 `result('搜索时间上限')`，结束当前函数；具体分支见完整源码。 |
| 102 | 函数体 / 循环每次 / 循环每次 / 循环每次 | 将 `line.find(keyword)` 赋给 `position`。 |
| 103 | 函数体 / 循环每次 / 循环每次 / 循环每次 | 条件 `position < 0`：真时执行body，假时进入else/后续。 |
| 104 | 函数体 / 循环每次 / 循环每次 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 105 | 函数体 / 循环每次 / 循环每次 / 循环每次 | 将 `max(0, position - 100) if len(line) > 500 else 0` 赋给 `start`。 |
| 106 | 函数体 / 循环每次 / 循环每次 / 循环每次 | 将 `line[start:start + 500]` 赋给 `snippet`。 |
| 107 | 函数体 / 循环每次 / 循环每次 / 循环每次 | 将 `{'path': relative, 'line_number': number, 'content': snippet, 'content_truncated': start > 0 or start + len(snippet) < len(line)}` 赋给 `entry`。 |
| 109 | 函数体 / 循环每次 / 循环每次 / 循环每次 | 将 `len(json.dumps(entry, ensure_ascii=False))` 赋给 `size`。 |
| 110 | 函数体 / 循环每次 / 循环每次 / 循环每次 | 条件 `output_chars + size > search_config['max_output_chars']`：真时执行body，假时进入else/后续。 |
| 111 | 函数体 / 循环每次 / 循环每次 / 循环每次 / 条件为真 | 返回 `result('结果字符数量上限')`，结束当前函数；具体分支见完整源码。 |
| 112 | 函数体 / 循环每次 / 循环每次 / 循环每次 | 计算表达式/调用产生动作：`matches.append(entry)`。 |
| 113 | 函数体 / 循环每次 / 循环每次 / 循环每次 | 更新已有变量：`output_chars += size`。 |
| 114 | 函数体 / 循环每次 / 循环每次 / 循环每次 | 条件 `len(matches) >= search_config['max_matches']`：真时执行body，假时进入else/后续。 |
| 115 | 函数体 / 循环每次 / 循环每次 / 循环每次 / 条件为真 | 返回 `result('匹配数量上限')`，结束当前函数；具体分支见完整源码。 |
| 116 | 函数体 | 返回 `result()`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L15：`checked`。
- L17：`{'ok': False, 'error': '关键词和文件匹配模式不能为空'}`。
- L20：`{'ok': False, 'error': '项目搜索目标必须是存在的目录'}`。
- L23：`{'ok': False, 'error': '搜索限制必须是正整数'}`。
- L45：`result('搜索时间上限')`。
- L49：`result('搜索时间上限')`。
- L58：`result('搜索时间上限')`。
- L68：`result('扫描文件数量上限')`。
- L78：`result('总读取字节上限')`。
- L83：`result('总读取字节上限')`。
- L101：`result('搜索时间上限')`。
- L111：`result('结果字符数量上限')`。
- L115：`result('匹配数量上限')`。
- L116：`result()`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="search-project-result"></a>
## search_project.result

将本次搜索matches/统计/warnings及可选截断原因组装成成功返回。

```python
def result(reason='')
```

位置：[33行](../../../project_search.py#L33) 至快照 36 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `reason` | `未显式注解` | 明确终止/审批/截断原因，不根据正文措辞推断。 |

**调用表达式（静态提取，不含内层独立函数体）**：`bool`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 34 | 函数体 | 返回 `{'ok': True, 'matches': matches, 'files_scanned': scanned, 'bytes_read': total_bytes, 'skipped': skipped, 'warnings': warnings, 'truncated': bool(reason), 'limit_reason':…（见完整源码）`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L34：`{'ok': True, 'matches': matches, 'files_scanned': scanned, 'bytes_read': total_bytes, 'skipped': skipped, 'warnings': warnings, 'truncated': bool(reason), 'limit_reason': reason}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="search-project-walk-error"></a>
## search_project.walk_error

目录遍历失败时计unreadable并加入有限警告，不假装全部扫描。

```python
def walk_error(error)
```

位置：[38行](../../../project_search.py#L38) 至快照 41 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `error` | `未显式注解` | 捕获的异常或错误字段，返回前可只保留类型以避免泄露。 |

**调用表达式（静态提取，不含内层独立函数体）**：`len`、`type`、`warnings.append`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 39 | 函数体 | 更新已有变量：`skipped['unreadable'] += 1`。 |
| 40 | 函数体 | 条件 `len(warnings) < 10`：真时执行body，假时进入else/后续。 |
| 41 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`warnings.append('部分目录无法遍历: ' + type(error).__name__)`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- 推导式/生成器表达式：循环建容器或逐个产生：L22。
- try/except/finally：异常与保证清理：L69。
- with/yield：资源/状态生命周期或逐个生成：L79。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """项目递归文字搜索：共享路径策略，跳过符号链接并限制读取和结果规模。"""
0002 | import fnmatch
0003 | import json
0004 | import os
0005 | import time
0006 | from pathlib import Path
0007 | 
0008 | import permissions
0009 | from config import search_config
0010 | 
0011 | 
0012 | def search_project(path, keyword, glob="*"):
0013 |     checked = permissions.resolve_project_path(path)
0014 |     if not checked["ok"]:
0015 |         return checked
0016 |     if not isinstance(keyword, str) or not keyword or not isinstance(glob, str) or not glob:
0017 |         return {"ok": False, "error": "关键词和文件匹配模式不能为空"}
0018 |     root = Path(checked["path"])
0019 |     if not root.is_dir():
0020 |         return {"ok": False, "error": "项目搜索目标必须是存在的目录"}
0021 |     numeric_keys = ["max_files", "max_file_bytes", "max_total_bytes", "max_matches", "max_output_chars", "timeout_seconds"]
0022 |     if any(type(search_config.get(key)) is not int or search_config[key] <= 0 for key in numeric_keys):
0023 |         return {"ok": False, "error": "搜索限制必须是正整数"}
0024 |     matches = []
0025 |     warnings = []
0026 |     skipped = {"protected_or_link": 0, "large": 0, "non_text": 0, "unreadable": 0}
0027 |     scanned = 0
0028 |     total_bytes = 0
0029 |     output_chars = 0
0030 |     deadline = time.monotonic() + search_config["timeout_seconds"]
0031 |     ignored = set(search_config["ignored_directories"])
0032 | 
0033 |     def result(reason=""):
0034 |         return {"ok": True, "matches": matches, "files_scanned": scanned,
0035 |                 "bytes_read": total_bytes, "skipped": skipped, "warnings": warnings,
0036 |                 "truncated": bool(reason), "limit_reason": reason}
0037 | 
0038 |     def walk_error(error):
0039 |         skipped["unreadable"] += 1
0040 |         if len(warnings) < 10:
0041 |             warnings.append("部分目录无法遍历: " + type(error).__name__)
0042 | 
0043 |     for directory, directories, files in os.walk(root, followlinks=False, onerror=walk_error):
0044 |         if time.monotonic() >= deadline:
0045 |             return result("搜索时间上限")
0046 |         allowed = []
0047 |         for name in sorted(directories):
0048 |             if time.monotonic() >= deadline:
0049 |                 return result("搜索时间上限")
0050 |             item = Path(directory) / name
0051 |             if name in ignored or item.is_symlink() or not permissions.resolve_project_path(str(item))["ok"]:
0052 |                 skipped["protected_or_link"] += 1
0053 |             else:
0054 |                 allowed.append(name)
0055 |         directories[:] = allowed
0056 |         for name in sorted(files):
0057 |             if time.monotonic() >= deadline:
0058 |                 return result("搜索时间上限")
0059 |             item = Path(directory) / name
0060 |             checked = permissions.resolve_project_path(str(item))
0061 |             if item.is_symlink() or not checked["ok"]:
0062 |                 skipped["protected_or_link"] += 1
0063 |                 continue
0064 |             relative = str(item.relative_to(permissions.PROJECT_ROOT))
0065 |             if not fnmatch.fnmatchcase(relative, glob) and not fnmatch.fnmatchcase(name, glob):
0066 |                 continue
0067 |             if scanned >= search_config["max_files"]:
0068 |                 return result("扫描文件数量上限")
0069 |             try:
0070 |                 if not item.is_file():
0071 |                     continue
0072 |                 scanned += 1
0073 |                 if item.stat().st_size > search_config["max_file_bytes"]:
0074 |                     skipped["large"] += 1
0075 |                     continue
0076 |                 remaining = search_config["max_total_bytes"] - total_bytes
0077 |                 if remaining <= 0:
0078 |                     return result("总读取字节上限")
0079 |                 with open(checked["path"], "rb") as file:
0080 |                     raw = file.read(min(search_config["max_file_bytes"], remaining) + 1)
0081 |                 total_bytes += len(raw)
0082 |                 if len(raw) > remaining:
0083 |                     return result("总读取字节上限")
0084 |                 if len(raw) > search_config["max_file_bytes"]:
0085 |                     skipped["large"] += 1
0086 |                     continue
0087 |                 if b"\x00" in raw:
0088 |                     skipped["non_text"] += 1
0089 |                     continue
0090 |                 text = raw.decode("utf-8-sig")
0091 |             except UnicodeError:
0092 |                 skipped["non_text"] += 1
0093 |                 continue
0094 |             except OSError as error:
0095 |                 skipped["unreadable"] += 1
0096 |                 if len(warnings) < 10:
0097 |                     warnings.append("部分文件无法读取: " + type(error).__name__)
0098 |                 continue
0099 |             for number, line in enumerate(text.splitlines(), start=1):
0100 |                 if time.monotonic() >= deadline:
0101 |                     return result("搜索时间上限")
0102 |                 position = line.find(keyword)
0103 |                 if position < 0:
0104 |                     continue
0105 |                 start = max(0, position - 100) if len(line) > 500 else 0
0106 |                 snippet = line[start:start + 500]
0107 |                 entry = {"path": relative, "line_number": number, "content": snippet,
0108 |                          "content_truncated": start > 0 or start + len(snippet) < len(line)}
0109 |                 size = len(json.dumps(entry, ensure_ascii=False))
0110 |                 if output_chars + size > search_config["max_output_chars"]:
0111 |                     return result("结果字符数量上限")
0112 |                 matches.append(entry)
0113 |                 output_chars += size
0114 |                 if len(matches) >= search_config["max_matches"]:
0115 |                     return result("匹配数量上限")
0116 |     return result()
```
