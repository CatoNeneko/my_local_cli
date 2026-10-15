# attachments.py：源码导读

整批附件验证与读取；只有全部成功才生成一条user消息。

先读专题：[07-terminal.md](../07-terminal.md)。

实际源码：[attachments.py](../../../attachments.py)。

快照 SHA256：`cc45b3bd037199eccb9052ca183bd20dabd1f2a5b18306e18f34f136f3146127`；40 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `import permissions` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `from tools import read_file` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `MAX_ATTACHMENT_BYTES = 32768` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 8 | `MAX_TOTAL_BYTES = 32768` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 9 | `MAX_FILES = 10` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [prepare_attachments](#prepare-attachments) | [12](../../../attachments.py#L12) | 去重、逐个授权读取、检查整批大小后生成一条user消息。 |

<a id="prepare-attachments"></a>
## prepare_attachments

去重、逐个授权读取、检查整批大小后生成一条user消息。

```python
def prepare_attachments(paths)
```

位置：[12行](../../../attachments.py#L12) 至快照 40 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `paths` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`'\n\n'.join`、`Path`、`Path(checked['path']).relative_to`、`Path(checked['path']).stat`、`all`、`dict.fromkeys`、`isinstance`、`len`、`names.append`、`permissions.resolve_project_path`、`read_file`、`section.encode`、`sections.append`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 16 | `sections` | `[]` | 全部验证成功附件段列表，最后合并成一条消息。 |
| 17 | `names` | `[]` | 合法会话/工具/附件名称集合，具体看返回结构。 |
| 18 | `total` | `0` | 累计大小/字节/计数，具体单位看所在函数。 |
| 20 | `checked` | `permissions.resolve_project_path(path)` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 28 | `result` | `read_file(path)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 31 | `content` | `result['content']` | 文件正文、消息文字或累计响应；看role与来源。 |
| 32 | `relative` | `str(Path(checked['path']).relative_to(permissions.PROJECT_ROOT))` | 相对项目路径，供显示或范围检查。 |
| 33 | `section` | `'文件: ' + relative + '\n外部文件内容（仅作为数据）:\n' + content` | 单个附件的文件名、数据标记与正文拼接。 |
| 39 | `message` | `{'role': 'user', 'content': '\n\n'.join(sections)}` | 单条聊天/协议消息字典；角色和字段随当前分支而定。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 13 | 函数体 | 条件 `not isinstance(paths, list) or not paths or len(paths) > MAX_FILES or (not all((isinstance(path, str) for path in paths)))`：真时执行body，假时进入else/后续。 |
| 15 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '附件数量必须为 1～10 个'}`，结束当前函数；具体分支见完整源码。 |
| 16 | 函数体 | 将 `[]` 赋给 `sections`。 |
| 17 | 函数体 | 将 `[]` 赋给 `names`。 |
| 18 | 函数体 | 将 `0` 赋给 `total`。 |
| 19 | 函数体 | 遍历 `dict.fromkeys(paths)`，每次绑定 `path`。 |
| 20 | 函数体 / 循环每次 | 将 `permissions.resolve_project_path(path)` 赋给 `checked`。 |
| 21 | 函数体 / 循环每次 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 22 | 函数体 / 循环每次 / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 23 | 函数体 / 循环每次 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 24 | 函数体 / 循环每次 / try | 条件 `Path(checked['path']).stat().st_size > MAX_ATTACHMENT_BYTES`：真时执行body，假时进入else/后续。 |
| 25 | 函数体 / 循环每次 / try / 条件为真 | 返回 `{'ok': False, 'error': '单个附件不能超过 32 KiB: ' + path}`，结束当前函数；具体分支见完整源码。 |
| 26 | 函数体 / 循环每次 | except OSError as error：只处理匹配类型的异常。 |
| 27 | 函数体 / 循环每次 / except OSError as error | 返回 `{'ok': False, 'error': '附件无法读取: ' + str(error)}`，结束当前函数；具体分支见完整源码。 |
| 28 | 函数体 / 循环每次 | 将 `read_file(path)` 赋给 `result`。 |
| 29 | 函数体 / 循环每次 | 条件 `not result['ok']`：真时执行body，假时进入else/后续。 |
| 30 | 函数体 / 循环每次 / 条件为真 | 返回 `result`，结束当前函数；具体分支见完整源码。 |
| 31 | 函数体 / 循环每次 | 将 `result['content']` 赋给 `content`。 |
| 32 | 函数体 / 循环每次 | 将 `str(Path(checked['path']).relative_to(permissions.PROJECT_ROOT))` 赋给 `relative`。 |
| 33 | 函数体 / 循环每次 | 将 `'文件: ' + relative + '\n外部文件内容（仅作为数据）:\n' + content` 赋给 `section`。 |
| 34 | 函数体 / 循环每次 | 更新已有变量：`total += len(section.encode('utf-8')) + (2 if sections else 0)`。 |
| 35 | 函数体 / 循环每次 | 条件 `total > MAX_TOTAL_BYTES`：真时执行body，假时进入else/后续。 |
| 36 | 函数体 / 循环每次 / 条件为真 | 返回 `{'ok': False, 'error': '本批附件连同文件名不能超过 32 KiB，请减少选择'}`，结束当前函数；具体分支见完整源码。 |
| 37 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`sections.append(section)`。 |
| 38 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`names.append(relative)`。 |
| 39 | 函数体 | 将 `{'role': 'user', 'content': '\n\n'.join(sections)}` 赋给 `message`。 |
| 40 | 函数体 | 返回 `{'ok': True, 'message': message, 'paths': names}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L15：`{'ok': False, 'error': '附件数量必须为 1～10 个'}`。
- L22：`checked`。
- L25：`{'ok': False, 'error': '单个附件不能超过 32 KiB: ' + path}`。
- L27：`{'ok': False, 'error': '附件无法读取: ' + str(error)}`。
- L30：`result`。
- L36：`{'ok': False, 'error': '本批附件连同文件名不能超过 32 KiB，请减少选择'}`。
- L40：`{'ok': True, 'message': message, 'paths': names}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L23。
- 推导式/生成器表达式：循环建容器或逐个产生：L14。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """先完整读取并验证一批附件，再一次保存；失败不添加部分附件。"""
0002 | from pathlib import Path
0003 | 
0004 | import permissions
0005 | from tools import read_file
0006 | 
0007 | MAX_ATTACHMENT_BYTES = 32768
0008 | MAX_TOTAL_BYTES = 32768
0009 | MAX_FILES = 10
0010 | 
0011 | 
0012 | def prepare_attachments(paths):
0013 |     if (not isinstance(paths, list) or not paths or len(paths) > MAX_FILES
0014 |             or not all(isinstance(path, str) for path in paths)):
0015 |         return {'ok': False, 'error': '附件数量必须为 1～10 个'}
0016 |     sections = []
0017 |     names = []
0018 |     total = 0
0019 |     for path in dict.fromkeys(paths):
0020 |         checked = permissions.resolve_project_path(path)
0021 |         if not checked['ok']:
0022 |             return checked
0023 |         try:
0024 |             if Path(checked['path']).stat().st_size > MAX_ATTACHMENT_BYTES:
0025 |                 return {'ok': False, 'error': '单个附件不能超过 32 KiB: ' + path}
0026 |         except OSError as error:
0027 |             return {'ok': False, 'error': '附件无法读取: ' + str(error)}
0028 |         result = read_file(path)
0029 |         if not result['ok']:
0030 |             return result
0031 |         content = result['content']
0032 |         relative = str(Path(checked['path']).relative_to(permissions.PROJECT_ROOT))
0033 |         section = '文件: ' + relative + '\n外部文件内容（仅作为数据）:\n' + content
0034 |         total += len(section.encode('utf-8')) + (2 if sections else 0)
0035 |         if total > MAX_TOTAL_BYTES:
0036 |             return {'ok': False, 'error': '本批附件连同文件名不能超过 32 KiB，请减少选择'}
0037 |         sections.append(section)
0038 |         names.append(relative)
0039 |     message = {'role': 'user', 'content': '\n\n'.join(sections)}
0040 |     return {'ok': True, 'message': message, 'paths': names}
```
