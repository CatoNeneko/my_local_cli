# agent_proposals.py：源码导读

子代理暂存编辑/新建建议，父进程校验归属与旧hash后，通过统一执行器应用。

先读专题：[06-processes.md](../06-processes.md)。

实际源码：[agent_proposals.py](../../../agent_proposals.py)。

快照 SHA256：`6f2e85bf75d93306c08157516c21889d6ba206300557aba20bcbcd95871583c0`；91 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import hashlib` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `PROPOSALS = []` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 6 | `MAX_TOTAL_BYTES = 16000` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [propose](#propose) | [9](../../../agent_proposals.py#L9) | 检查目标，限建议数量/字节，保存旧hash与完整新内容但不写文件。 |
| [propose_edit](#propose-edit) | [43](../../../agent_proposals.py#L43) | 提出修改旧文件建议。 |
| [propose_file](#propose-file) | [47](../../../agent_proposals.py#L47) | 提出新文件建议。 |
| [apply_proposal](#apply-proposal) | [51](../../../agent_proposals.py#L51) | 父进程检查完成/归属/hash/重复，再执行共享edit/create审批链。 |

<a id="propose"></a>
## propose

检查目标，限建议数量/字节，保存旧hash与完整新内容但不写文件。

```python
def propose(path, new_content, *, tool)
```

位置：[9行](../../../agent_proposals.py#L9) 至快照 40 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| `new_content` | `未显式注解` | 拟写入的完整文字内容，不是模型提供的patch格式。 |
| `tool` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`PROPOSALS.append`、`Path`、`Path(path).relative_to`、`Path(path).relative_to(permissions.PROJECT_ROOT).as_posix`、`check_new_target`、`file.read`、`hashlib.sha256`、`hashlib.sha256(original).hexdigest`、`item['new_content'].encode`、`len`、`new_content.encode`、`open`、`original.decode`、`permissions.resolve_project_path`、`str`、`sum`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 11 | `checked` | `permissions.resolve_project_path(path)` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 14 | `path` | `checked['path']` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| 15 | `raw` | `new_content.encode('utf-8')` | 未解码字节/完整输出快照，按编码与限额再处理。 |
| 20 | `original_hash` | `None` | 子代理建议基于的旧文件字节hash。 |
| 24 | `original` | `file.read(1048577)` | 旧文件字节/原始路径对象等，具体以当前赋值为准。 |
| 28 | `original_hash` | `hashlib.sha256(original).hexdigest()` | 子代理建议基于的旧文件字节hash。 |
| 33 | `checked` | `check_new_target(path)` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 36 | `identifier` | `str(len(PROPOSALS) + 1)` | 随机task_id、调用ID或建议ID；不同协议层用途不同。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 10 | 函数体 | 在此处导入依赖：`import permissions`；局部导入可延迟加载或避免循环。 |
| 11 | 函数体 | 将 `permissions.resolve_project_path(path)` 赋给 `checked`。 |
| 12 | 函数体 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 13 | 函数体 / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 14 | 函数体 | 将 `checked['path']` 赋给 `path`。 |
| 15 | 函数体 | 将 `new_content.encode('utf-8')` 赋给 `raw`。 |
| 16 | 函数体 | 条件 `len(PROPOSALS) >= 3 or sum((len(item['new_content'].encode('utf-8')) for item in PROPOSALS)) + len(raw) > MAX_TOTAL_BYTES`：真时执行body，假时进入else/后续。 |
| 17 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '子代理建议最多 3 个文件、合计 16000 字节'}`，结束当前函数；具体分支见完整源码。 |
| 18 | 函数体 | 条件 `'\x00' in new_content`：真时执行body，假时进入else/后续。 |
| 19 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '建议不能包含空字符'}`，结束当前函数；具体分支见完整源码。 |
| 20 | 函数体 | 将 `None` 赋给 `original_hash`。 |
| 21 | 函数体 | 条件 `tool == 'edit_file'`：真时执行body，假时进入else/后续。 |
| 22 | 函数体 / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 23 | 函数体 / 条件为真 / try | 进入资源/状态范围：`open(path, 'rb')` 绑定 `file`；退出执行清理。 |
| 24 | 函数体 / 条件为真 / try / with范围 | 将 `file.read(1048577)` 赋给 `original`。 |
| 25 | 函数体 / 条件为真 / try | 条件 `len(original) > 1048576`：真时执行body，假时进入else/后续。 |
| 26 | 函数体 / 条件为真 / try / 条件为真 | 返回 `{'ok': False, 'error': '建议目标文件超过 1 MiB'}`，结束当前函数；具体分支见完整源码。 |
| 27 | 函数体 / 条件为真 / try | 计算表达式/调用产生动作：`original.decode('utf-8')`。 |
| 28 | 函数体 / 条件为真 / try | 将 `hashlib.sha256(original).hexdigest()` 赋给 `original_hash`。 |
| 29 | 函数体 / 条件为真 | except (OSError, UnicodeError)：只处理匹配类型的异常。 |
| 30 | 函数体 / 条件为真 / except (OSError, UnicodeError) | 返回 `{'ok': False, 'error': '建议目标不是可读取的 UTF-8 文件'}`，结束当前函数；具体分支见完整源码。 |
| 32 | 函数体 / 条件为假/elif | 在此处导入依赖：`from new_files import check_new_target`；局部导入可延迟加载或避免循环。 |
| 33 | 函数体 / 条件为假/elif | 将 `check_new_target(path)` 赋给 `checked`。 |
| 34 | 函数体 / 条件为假/elif | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 35 | 函数体 / 条件为假/elif / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 36 | 函数体 | 将 `str(len(PROPOSALS) + 1)` 赋给 `identifier`。 |
| 37 | 函数体 | 计算表达式/调用产生动作：`PROPOSALS.append({'proposal_id': identifier, 'tool': tool, 'path': Path(path).relative_to(permissions.PROJECT_ROOT).as_posix(), 'new_content': new_content, 'original_hash…（见完整源码）`。 |
| 40 | 函数体 | 返回 `{'ok': True, 'proposal_id': identifier, 'message': '建议已暂存，未写入文件；父代理必须另行审批'}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L13：`checked`。
- L17：`{'ok': False, 'error': '子代理建议最多 3 个文件、合计 16000 字节'}`。
- L19：`{'ok': False, 'error': '建议不能包含空字符'}`。
- L26：`{'ok': False, 'error': '建议目标文件超过 1 MiB'}`。
- L30：`{'ok': False, 'error': '建议目标不是可读取的 UTF-8 文件'}`。
- L35：`checked`。
- L40：`{'ok': True, 'proposal_id': identifier, 'message': '建议已暂存，未写入文件；父代理必须另行审批'}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="propose-edit"></a>
## propose_edit

提出修改旧文件建议。

```python
def propose_edit(path, new_content)
```

位置：[43行](../../../agent_proposals.py#L43) 至快照 44 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| `new_content` | `未显式注解` | 拟写入的完整文字内容，不是模型提供的patch格式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`propose`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 44 | 函数体 | 返回 `propose(path, new_content, tool='edit_file')`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L44：`propose(path, new_content, tool='edit_file')`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="propose-file"></a>
## propose_file

提出新文件建议。

```python
def propose_file(path, new_content)
```

位置：[47行](../../../agent_proposals.py#L47) 至快照 48 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| `new_content` | `未显式注解` | 拟写入的完整文字内容，不是模型提供的patch格式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`propose`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 48 | 函数体 | 返回 `propose(path, new_content, tool='create_file')`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L48：`propose(path, new_content, tool='create_file')`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="apply-proposal"></a>
## apply_proposal

父进程检查完成/归属/hash/重复，再执行共享edit/create审批链。

```python
def apply_proposal(task_id, proposal_id)
```

位置：[51行](../../../agent_proposals.py#L51) 至快照 91 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `task_id` | `未显式注解` | 仅当前CLI有效的owned任务ID。 |
| `proposal_id` | `未显式注解` | 子代理暂存建议ID，应用时检查真实内部数据。 |

**调用表达式（静态提取，不含内层独立函数体）**：`JOBS.get`、`ValueError`、`applied.get`、`bytes`、`execute_tool`、`file.read`、`hashlib.sha256`、`hashlib.sha256(original).hexdigest`、`item.get`、`job.get`、`job.setdefault`、`json.loads`、`len`、`next`、`open`、`permissions.resolve_project_path`、`proposal.get`、`result.get`、`set`、`str`、`task_scope`、`used.add`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 57 | `job` | `JOBS.get(task_id)` | 当前进程的任务记录字典，包含进程、缓冲、锁和状态。 |
| 63 | `result` | `json.loads(bytes(job['output']))` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 66 | `proposal` | `next((item for item in result.get('proposals', []) if item.get('proposal_id') == proposal_id))` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 71 | `used` | `job.setdefault('applied_proposals', set())` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 74 | `checked` | `permissions.resolve_project_path(proposal.get('path'))` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 80 | `original` | `file.read(1048577)` | 旧文件字节/原始路径对象等，具体以当前赋值为准。 |
| 87 | `applied` | `execute_tool(proposal['tool'], {'path': proposal['path'], 'new_content': proposal['new_content']})` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 52 | 函数体 | 在此处导入依赖：`import permissions`；局部导入可延迟加载或避免循环。 |
| 53 | 函数体 | 在此处导入依赖：`from process_tasks import JOBS`；局部导入可延迟加载或避免循环。 |
| 54 | 函数体 | 在此处导入依赖：`from approval import task_scope`；局部导入可延迟加载或避免循环。 |
| 55 | 函数体 | 在此处导入依赖：`from tool_runtime import execute_tool`；局部导入可延迟加载或避免循环。 |
| 56 | 函数体 | 在此处导入依赖：`import json`；局部导入可延迟加载或避免循环。 |
| 57 | 函数体 | 将 `JOBS.get(task_id)` 赋给 `job`。 |
| 58 | 函数体 | 条件 `job is None or job['kind'] != 'agent' or (not job['done'])`：真时执行body，假时进入else/后续。 |
| 59 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '子代理任务尚未完成或不存在'}`，结束当前函数；具体分支见完整源码。 |
| 60 | 函数体 | 条件 `job.get('workspace') != str(permissions.PROJECT_ROOT)`：真时执行body，假时进入else/后续。 |
| 61 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '子代理不属于当前项目'}`，结束当前函数；具体分支见完整源码。 |
| 62 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 63 | 函数体 / try | 将 `json.loads(bytes(job['output']))` 赋给 `result`。 |
| 64 | 函数体 / try | 条件 `result.get('ok') is not True`：真时执行body，假时进入else/后续。 |
| 65 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': '子代理未成功完成，不能应用建议'}`，结束当前函数；具体分支见完整源码。 |
| 66 | 函数体 / try | 将 `next((item for item in result.get('proposals', []) if item.get('proposal_id') == proposal_id))` 赋给 `proposal`。 |
| 67 | 函数体 / try | 条件 `proposal['tool'] not in ('edit_file', 'create_file')`：真时执行body，假时进入else/后续。 |
| 68 | 函数体 / try / 条件为真 | 抛出 `ValueError()`。 |
| 69 | 函数体 | except (ValueError, KeyError, TypeError, StopIteration, AttributeEr…（见完整源码）：只处理匹配类型的异常。 |
| 70 | 函数体 / except (ValueError, KeyError, TypeError, StopIteration, AttributeEr…（见完整源码） | 返回 `{'ok': False, 'error': '建议 ID 不存在或数据无效'}`，结束当前函数；具体分支见完整源码。 |
| 71 | 函数体 | 将 `job.setdefault('applied_proposals', set())` 赋给 `used`。 |
| 72 | 函数体 | 条件 `proposal_id in used`：真时执行body，假时进入else/后续。 |
| 73 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '建议已应用，不能重复写入'}`，结束当前函数；具体分支见完整源码。 |
| 74 | 函数体 | 将 `permissions.resolve_project_path(proposal.get('path'))` 赋给 `checked`。 |
| 75 | 函数体 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 76 | 函数体 / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 77 | 函数体 | 条件 `proposal['tool'] == 'edit_file'`：真时执行body，假时进入else/后续。 |
| 78 | 函数体 / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 79 | 函数体 / 条件为真 / try | 进入资源/状态范围：`open(checked['path'], 'rb')` 绑定 `file`；退出执行清理。 |
| 80 | 函数体 / 条件为真 / try / with范围 | 将 `file.read(1048577)` 赋给 `original`。 |
| 81 | 函数体 / 条件为真 / try | 条件 `len(original) > 1048576 or hashlib.sha256(original).hexdigest() != proposal.get('original_hash')`：真时执行body，假时进入else/后续。 |
| 82 | 函数体 / 条件为真 / try / 条件为真 | 返回 `{'ok': False, 'error': '文件在子代理提出建议后已变化，请重新生成建议'}`，结束当前函数；具体分支见完整源码。 |
| 83 | 函数体 / 条件为真 | except OSError：只处理匹配类型的异常。 |
| 84 | 函数体 / 条件为真 / except OSError | 返回 `{'ok': False, 'error': '建议目标已无法读取'}`，结束当前函数；具体分支见完整源码。 |
| 86 | 函数体 | 进入资源/状态范围：`task_scope(job['task'])`；退出执行清理。 |
| 87 | 函数体 / with范围 | 将 `execute_tool(proposal['tool'], {'path': proposal['path'], 'new_content': proposal['new_content']})` 赋给 `applied`。 |
| 88 | 函数体 | 条件 `applied['ok']`：真时执行body，假时进入else/后续。 |
| 89 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`used.add(proposal_id)`。 |
| 90 | 函数体 | 返回 `{'ok': applied['ok'], 'task_id': task_id, 'proposal_id': proposal_id, 'result': applied, **({'cancelled': True} if applied.get('cancelled') else {})}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L59：`{'ok': False, 'error': '子代理任务尚未完成或不存在'}`。
- L61：`{'ok': False, 'error': '子代理不属于当前项目'}`。
- L65：`{'ok': False, 'error': '子代理未成功完成，不能应用建议'}`。
- L70：`{'ok': False, 'error': '建议 ID 不存在或数据无效'}`。
- L73：`{'ok': False, 'error': '建议已应用，不能重复写入'}`。
- L76：`checked`。
- L82：`{'ok': False, 'error': '文件在子代理提出建议后已变化，请重新生成建议'}`。
- L84：`{'ok': False, 'error': '建议目标已无法读取'}`。
- L90：`{'ok': applied['ok'], 'task_id': task_id, 'proposal_id': proposal_id, 'result': applied, **({'cancelled': True} if applied.get('cancelled') else {})}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L22, L62, L78。
- with/yield：资源/状态生命周期或逐个生成：L23, L79, L86。
- 推导式/生成器表达式：循环建容器或逐个产生：L16, L66。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """子代理只能暂存文件建议；父进程通过共享执行器另行审批、写入。"""
0002 | from pathlib import Path
0003 | import hashlib
0004 | 
0005 | PROPOSALS = []
0006 | MAX_TOTAL_BYTES = 16000
0007 | 
0008 | 
0009 | def propose(path, new_content, *, tool):
0010 |     import permissions
0011 |     checked = permissions.resolve_project_path(path)
0012 |     if not checked['ok']:
0013 |         return checked
0014 |     path = checked['path']
0015 |     raw = new_content.encode('utf-8')
0016 |     if len(PROPOSALS) >= 3 or sum(len(item['new_content'].encode('utf-8')) for item in PROPOSALS) + len(raw) > MAX_TOTAL_BYTES:
0017 |         return {'ok': False, 'error': '子代理建议最多 3 个文件、合计 16000 字节'}
0018 |     if '\x00' in new_content:
0019 |         return {'ok': False, 'error': '建议不能包含空字符'}
0020 |     original_hash = None
0021 |     if tool == 'edit_file':
0022 |         try:
0023 |             with open(path, 'rb') as file:
0024 |                 original = file.read(1048577)
0025 |             if len(original) > 1048576:
0026 |                 return {'ok': False, 'error': '建议目标文件超过 1 MiB'}
0027 |             original.decode('utf-8')
0028 |             original_hash = hashlib.sha256(original).hexdigest()
0029 |         except (OSError, UnicodeError):
0030 |             return {'ok': False, 'error': '建议目标不是可读取的 UTF-8 文件'}
0031 |     else:
0032 |         from new_files import check_new_target
0033 |         checked = check_new_target(path)
0034 |         if not checked['ok']:
0035 |             return checked
0036 |     identifier = str(len(PROPOSALS) + 1)
0037 |     PROPOSALS.append({'proposal_id': identifier, 'tool': tool,
0038 |                       'path': Path(path).relative_to(permissions.PROJECT_ROOT).as_posix(),
0039 |                       'new_content': new_content, 'original_hash': original_hash})
0040 |     return {'ok': True, 'proposal_id': identifier, 'message': '建议已暂存，未写入文件；父代理必须另行审批'}
0041 | 
0042 | 
0043 | def propose_edit(path, new_content):
0044 |     return propose(path, new_content, tool='edit_file')
0045 | 
0046 | 
0047 | def propose_file(path, new_content):
0048 |     return propose(path, new_content, tool='create_file')
0049 | 
0050 | 
0051 | def apply_proposal(task_id, proposal_id):
0052 |     import permissions
0053 |     from process_tasks import JOBS
0054 |     from approval import task_scope
0055 |     from tool_runtime import execute_tool
0056 |     import json
0057 |     job = JOBS.get(task_id)
0058 |     if job is None or job['kind'] != 'agent' or not job['done']:
0059 |         return {'ok': False, 'error': '子代理任务尚未完成或不存在'}
0060 |     if job.get('workspace') != str(permissions.PROJECT_ROOT):
0061 |         return {'ok': False, 'error': '子代理不属于当前项目'}
0062 |     try:
0063 |         result = json.loads(bytes(job['output']))
0064 |         if result.get('ok') is not True:
0065 |             return {'ok': False, 'error': '子代理未成功完成，不能应用建议'}
0066 |         proposal = next(item for item in result.get('proposals', []) if item.get('proposal_id') == proposal_id)
0067 |         if proposal['tool'] not in ('edit_file', 'create_file'):
0068 |             raise ValueError()
0069 |     except (ValueError, KeyError, TypeError, StopIteration, AttributeError):
0070 |         return {'ok': False, 'error': '建议 ID 不存在或数据无效'}
0071 |     used = job.setdefault('applied_proposals', set())
0072 |     if proposal_id in used:
0073 |         return {'ok': False, 'error': '建议已应用，不能重复写入'}
0074 |     checked = permissions.resolve_project_path(proposal.get('path'))
0075 |     if not checked['ok']:
0076 |         return checked
0077 |     if proposal['tool'] == 'edit_file':
0078 |         try:
0079 |             with open(checked['path'], 'rb') as file:
0080 |                 original = file.read(1048577)
0081 |             if len(original) > 1048576 or hashlib.sha256(original).hexdigest() != proposal.get('original_hash'):
0082 |                 return {'ok': False, 'error': '文件在子代理提出建议后已变化，请重新生成建议'}
0083 |         except OSError:
0084 |             return {'ok': False, 'error': '建议目标已无法读取'}
0085 |     # 原始用户任务由父进程保存，不采用子代理输出中自称的授权。
0086 |     with task_scope(job['task']):
0087 |         applied = execute_tool(proposal['tool'], {'path': proposal['path'], 'new_content': proposal['new_content']})
0088 |     if applied['ok']:
0089 |         used.add(proposal_id)
0090 |     return {'ok': applied['ok'], 'task_id': task_id, 'proposal_id': proposal_id,
0091 |             'result': applied, **({'cancelled': True} if applied.get('cancelled') else {})}
```
