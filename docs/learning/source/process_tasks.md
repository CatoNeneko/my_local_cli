# process_tasks.py：源码导读

当前进程任务表、PTY、输出采集线程、终止回收与子代理启动。

先读专题：[06-processes.md](../06-processes.md)。

实际源码：[process_tasks.py](../../../process_tasks.py)。

快照 SHA256：`3b645e35f771efe36cb592bcd0f39fddba1b0ca973b03659e14e68c81adef3e7`；236 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import atexit` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `import os` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `import pty` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `import select` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `import signal` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 9 | `import subprocess` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 10 | `import threading` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 11 | `import time` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 12 | `import uuid` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 14 | `JOBS = {}` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 15 | `LOCK = threading.RLock()` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 16 | `MAX_OUTPUT = 65536` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [launch](#launch) | [19](../../../process_tasks.py#L19) | 有界任务创建，配置PIPE或PTY，启动采集线程后返回task_id。 |
| [_kill](#-kill) | [70](../../../process_tasks.py#L70) | SIGKILL终止任务进程组，已退出则忽略。 |
| [_close](#-close) | [77](../../../process_tasks.py#L77) | 关闭PTY主fd或stdout管道。 |
| [_collect](#-collect) | [84](../../../process_tasks.py#L84) | 后台采集任务输出，时间/体积限制并清理进程和fd。 |
| [inspect_task](#inspect-task) | [122](../../../process_tasks.py#L122) | 按offset给状态与输出；完成子代理仅展示建议摘要。 |
| [send_input](#send-input) | [155](../../../process_tasks.py#L155) | 向活跃owned PTY写UTF-8输入。 |
| [cancel_task](#cancel-task) | [167](../../../process_tasks.py#L167) | 标取消、杀组、join后查结果。 |
| [wait_task](#wait-task) | [179](../../../process_tasks.py#L179) | 最多等待线程指定秒后返回当前状态。 |
| [list_tasks](#list-tasks) | [187](../../../process_tasks.py#L187) | 所有当前任务的简要状态。 |
| [close_tasks](#close-tasks) | [193](../../../process_tasks.py#L193) | 取消所有当前任务并清空内存表。 |
| [prepare_pty](#prepare-pty) | [202](../../../process_tasks.py#L202) | 复用沙箱前缀，恢复控制TTY后执行argv。 |
| [start_pty](#start-pty) | [222](../../../process_tasks.py#L222) | 将prepared命令按PTY启动。 |
| [start_agent](#start-agent) | [226](../../../process_tasks.py#L226) | 将任务、规则与配置快照发给独立可信worker。 |

<a id="launch"></a>
## launch

有界任务创建，配置PIPE或PTY，启动采集线程后返回task_id。

```python
def launch(command, *, terminal=False, payload=None, timeout=120, kind='pty')
```

位置：[19行](../../../process_tasks.py#L19) 至快照 67 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `command` | `未显式注解` | 安全构造的argv列表或解析出的命令名，避免将它们混为shell字符串。 |
| `terminal` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `payload` | `未显式注解` | 传给子进程/独立审查/摘要请求的结构化数据快照。 |
| `timeout` | `未显式注解` | 操作/任务超时秒数。 |
| `kind` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`JOBS.pop`、`JOBS.values`、`ValueError`、`_close`、`_kill`、`all`、`bytearray`、`current_task`、`dict`、`isinstance`、`job['process'].poll`、`json.dumps`、`json.dumps(payload, ensure_ascii=False).encode`、`len`、`os.close`、`payload.get`、`process.stdin.close`、`process.stdin.write`、`process.stdout.fileno`、`process.wait`、`pty.openpty`、`subprocess.Popen`、`sum`、`thread.start`、`threading.RLock`、`threading.Thread`、`uuid.uuid4`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 25 | `master,slave` | `None` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 27 | `(master, slave)` | `pty.openpty()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 29 | `process` | `subprocess.Popen(command, stdin=slave if terminal else subprocess.PIPE, stdout=slave if terminal else subprocess.PIPE, stderr=slav…（见完整源码）` | Popen实际子进程句柄，可poll/wait。 |
| 39 | `identifier` | `uuid.uuid4().hex[:12]` | 随机task_id、调用ID或建议ID；不同协议层用途不同。 |
| 40 | `job` | `{'process': process, 'fd': master if terminal else process.stdout.fileno(), 'output': bytearray(), 'reason': '', 'kind': kind, 'te…（见完整源码）` | 当前进程的任务记录字典，包含进程、缓冲、锁和状态。 |
| 45 | `job['workspace']` | `payload['workspace']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 46 | `job['task']` | `current_task() or payload['task']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 47 | `JOBS[identifier]` | `job` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 52 | `thread` | `threading.Thread(target=_collect, args=(job, timeout), daemon=True)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 53 | `job['thread']` | `thread` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 20 | 函数体 | 条件 `kind == 'agent' and (not isinstance(payload, dict) or not all((isinstance(payload.get(key), str) for key in ('workspace', 'task'))))`：真时执行body，假时进入else/后续。 |
| 21 | 函数体 / 条件为真 | 抛出 `ValueError('子代理启动数据无效')`。 |
| 22 | 函数体 | 进入资源/状态范围：`LOCK`；退出执行清理。 |
| 23 | 函数体 / with范围 | 条件 `sum((job['process'].poll() is None for job in JOBS.values())) >= 4 or len(JOBS) >= 64`：真时执行body，假时进入else/后续。 |
| 24 | 函数体 / with范围 / 条件为真 | 返回 `{'ok': False, 'error': '任务数量达到上限（同时 4 个，本进程累计 64 个）'}`，结束当前函数；具体分支见完整源码。 |
| 25 | 函数体 / with范围 | 将 `None` 赋给 `master`, `slave`。 |
| 26 | 函数体 / with范围 | 条件 `terminal`：真时执行body，假时进入else/后续。 |
| 27 | 函数体 / with范围 / 条件为真 | 将 `pty.openpty()` 赋给 `(master, slave)`。 |
| 28 | 函数体 / with范围 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 29 | 函数体 / with范围 / try | 将 `subprocess.Popen(command, stdin=slave if terminal else subprocess.PIPE, stdout=slave if terminal else subprocess.PIPE, stderr=slave if terminal else subprocess.DEVNULL, s…（见完整源码）` 赋给 `process`。 |
| 32 | 函数体 / with范围 | except BaseException：只处理匹配类型的异常。 |
| 33 | 函数体 / with范围 / except BaseException | 条件 `master is not None`：真时执行body，假时进入else/后续。 |
| 34 | 函数体 / with范围 / except BaseException / 条件为真 | 计算表达式/调用产生动作：`os.close(master)`。 |
| 35 | 函数体 / with范围 / except BaseException | 抛出 `None`。 |
| 37 | 函数体 / with范围 / finally保证清理 | 条件 `slave is not None`：真时执行body，假时进入else/后续。 |
| 38 | 函数体 / with范围 / finally保证清理 / 条件为真 | 计算表达式/调用产生动作：`os.close(slave)`。 |
| 39 | 函数体 / with范围 | 将 `uuid.uuid4().hex[:12]` 赋给 `identifier`。 |
| 40 | 函数体 / with范围 | 将 `{'process': process, 'fd': master if terminal else process.stdout.fileno(), 'output': bytearray(), 'reason': '', 'kind': kind, 'terminal': terminal, 'done': False, 'lock'…（见完整源码）` 赋给 `job`。 |
| 43 | 函数体 / with范围 | 条件 `kind == 'agent'`：真时执行body，假时进入else/后续。 |
| 44 | 函数体 / with范围 / 条件为真 | 在此处导入依赖：`from approval import current_task`；局部导入可延迟加载或避免循环。 |
| 45 | 函数体 / with范围 / 条件为真 | 将 `payload['workspace']` 赋给 `job['workspace']`。 |
| 46 | 函数体 / with范围 / 条件为真 | 将 `current_task() or payload['task']` 赋给 `job['task']`。 |
| 47 | 函数体 / with范围 | 将 `job` 赋给 `JOBS[identifier]`。 |
| 48 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 49 | 函数体 / try | 条件 `payload is not None`：真时执行body，假时进入else/后续。 |
| 50 | 函数体 / try / 条件为真 | 计算表达式/调用产生动作：`process.stdin.write(json.dumps(payload, ensure_ascii=False).encode())`。 |
| 51 | 函数体 / try / 条件为真 | 计算表达式/调用产生动作：`process.stdin.close()`。 |
| 52 | 函数体 / try | 将 `threading.Thread(target=_collect, args=(job, timeout), daemon=True)` 赋给 `thread`。 |
| 53 | 函数体 / try | 将 `thread` 赋给 `job['thread']`。 |
| 54 | 函数体 / try | 计算表达式/调用产生动作：`thread.start()`。 |
| 55 | 函数体 | except BaseException：只处理匹配类型的异常。 |
| 56 | 函数体 / except BaseException | 计算表达式/调用产生动作：`_kill(job)`。 |
| 57 | 函数体 / except BaseException | 条件 `process.stdin is not None and (not terminal)`：真时执行body，假时进入else/后续。 |
| 58 | 函数体 / except BaseException / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 59 | 函数体 / except BaseException / 条件为真 / try | 计算表达式/调用产生动作：`process.stdin.close()`。 |
| 60 | 函数体 / except BaseException / 条件为真 | except OSError：只处理匹配类型的异常。 |
| 61 | 函数体 / except BaseException / 条件为真 / except OSError | pass占位，无动作。 |
| 62 | 函数体 / except BaseException | 计算表达式/调用产生动作：`process.wait()`。 |
| 63 | 函数体 / except BaseException | 计算表达式/调用产生动作：`_close(job)`。 |
| 64 | 函数体 / except BaseException | 进入资源/状态范围：`LOCK`；退出执行清理。 |
| 65 | 函数体 / except BaseException / with范围 | 计算表达式/调用产生动作：`JOBS.pop(identifier, None)`。 |
| 66 | 函数体 / except BaseException | 抛出 `None`。 |
| 67 | 函数体 | 返回 `{'ok': True, 'task_id': identifier, 'kind': kind, 'state': 'running'}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L24：`{'ok': False, 'error': '任务数量达到上限（同时 4 个，本进程累计 64 个）'}`。
- L67：`{'ok': True, 'task_id': identifier, 'kind': kind, 'state': 'running'}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="-kill"></a>
## _kill

SIGKILL终止任务进程组，已退出则忽略。

```python
def _kill(job)
```

位置：[70行](../../../process_tasks.py#L70) 至快照 74 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `job` | `未显式注解` | 当前进程的任务记录字典，包含进程、缓冲、锁和状态。 |

**调用表达式（静态提取，不含内层独立函数体）**：`os.killpg`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 71 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 72 | 函数体 / try | 计算表达式/调用产生动作：`os.killpg(job['process'].pid, signal.SIGKILL)`。 |
| 73 | 函数体 | except ProcessLookupError：只处理匹配类型的异常。 |
| 74 | 函数体 / except ProcessLookupError | pass占位，无动作。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="-close"></a>
## _close

关闭PTY主fd或stdout管道。

```python
def _close(job)
```

位置：[77行](../../../process_tasks.py#L77) 至快照 81 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `job` | `未显式注解` | 当前进程的任务记录字典，包含进程、缓冲、锁和状态。 |

**调用表达式（静态提取，不含内层独立函数体）**：`job['process'].stdout.close`、`os.close`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 78 | 函数体 | 条件 `job['terminal']`：真时执行body，假时进入else/后续。 |
| 79 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`os.close(job['fd'])`。 |
| 81 | 函数体 / 条件为假/elif | 计算表达式/调用产生动作：`job['process'].stdout.close()`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="-collect"></a>
## _collect

后台采集任务输出，时间/体积限制并清理进程和fd。

```python
def _collect(job, timeout)
```

位置：[84行](../../../process_tasks.py#L84) 至快照 119 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `job` | `未显式注解` | 当前进程的任务记录字典，包含进程、缓冲、锁和状态。 |
| `timeout` | `未显式注解` | 操作/任务超时秒数。 |

**调用表达式（静态提取，不含内层独立函数体）**：`_close`、`_kill`、`job['output'].extend`、`job['process'].poll`、`job['process'].wait`、`len`、`os.read`、`select.select`、`time.monotonic`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 85 | `deadline` | `time.monotonic() + timeout` | monotonic算出的结束时刻，不受墙上时钟调整影响。 |
| 89 | `job['reason']` | `'timeout'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 92 | `(ready, _, _)` | `select.select([job['fd']], [], [], 0.1)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 95 | `chunk` | `os.read(job['fd'], 8192)` | 本次读取的输出字节或流式JSON块。 |
| 101 | `remaining` | `MAX_OUTPUT - len(job['output'])` | 还可读取/保存的字节配额。 |
| 104 | `job['reason']` | `'output_limit'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 119 | `job['done']` | `True` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 85 | 函数体 | 将 `time.monotonic() + timeout` 赋给 `deadline`。 |
| 86 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 87 | 函数体 / try | 循环检查 `True`，break/return/异常可结束。 |
| 88 | 函数体 / try / 循环每次 | 条件 `time.monotonic() >= deadline`：真时执行body，假时进入else/后续。 |
| 89 | 函数体 / try / 循环每次 / 条件为真 | 将 `'timeout'` 赋给 `job['reason']`。 |
| 90 | 函数体 / try / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`_kill(job)`。 |
| 91 | 函数体 / try / 循环每次 / 条件为真 | break结束最近一层循环。 |
| 92 | 函数体 / try / 循环每次 | 将 `select.select([job['fd']], [], [], 0.1)` 赋给 `(ready, _, _)`。 |
| 93 | 函数体 / try / 循环每次 | 条件 `ready`：真时执行body，假时进入else/后续。 |
| 94 | 函数体 / try / 循环每次 / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 95 | 函数体 / try / 循环每次 / 条件为真 / try | 将 `os.read(job['fd'], 8192)` 赋给 `chunk`。 |
| 96 | 函数体 / try / 循环每次 / 条件为真 | except OSError：只处理匹配类型的异常。 |
| 97 | 函数体 / try / 循环每次 / 条件为真 / except OSError | break结束最近一层循环。 |
| 98 | 函数体 / try / 循环每次 / 条件为真 | 条件 `not chunk`：真时执行body，假时进入else/后续。 |
| 99 | 函数体 / try / 循环每次 / 条件为真 / 条件为真 | break结束最近一层循环。 |
| 100 | 函数体 / try / 循环每次 / 条件为真 | 进入资源/状态范围：`job['lock']`；退出执行清理。 |
| 101 | 函数体 / try / 循环每次 / 条件为真 / with范围 | 将 `MAX_OUTPUT - len(job['output'])` 赋给 `remaining`。 |
| 102 | 函数体 / try / 循环每次 / 条件为真 / with范围 | 计算表达式/调用产生动作：`job['output'].extend(chunk[:remaining])`。 |
| 103 | 函数体 / try / 循环每次 / 条件为真 / with范围 | 条件 `len(chunk) > remaining`：真时执行body，假时进入else/后续。 |
| 104 | 函数体 / try / 循环每次 / 条件为真 / with范围 / 条件为真 | 将 `'output_limit'` 赋给 `job['reason']`。 |
| 105 | 函数体 / try / 循环每次 / 条件为真 / with范围 / 条件为真 | 计算表达式/调用产生动作：`_kill(job)`。 |
| 106 | 函数体 / try / 循环每次 / 条件为真 / with范围 / 条件为真 | break结束最近一层循环。 |
| 107 | 函数体 / try / 循环每次 / 条件为假/elif | 条件 `job['process'].poll() is not None`：真时执行body，假时进入else/后续。 |
| 108 | 函数体 / try / 循环每次 / 条件为假/elif / 条件为真 | break结束最近一层循环。 |
| 111 | 函数体 / finally保证清理 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 112 | 函数体 / finally保证清理 / try | 计算表达式/调用产生动作：`job['process'].wait(timeout=0.2)`。 |
| 113 | 函数体 / finally保证清理 | except subprocess.TimeoutExpired：只处理匹配类型的异常。 |
| 114 | 函数体 / finally保证清理 / except subprocess.TimeoutExpired | pass占位，无动作。 |
| 115 | 函数体 / finally保证清理 | 计算表达式/调用产生动作：`_kill(job)`。 |
| 116 | 函数体 / finally保证清理 | 计算表达式/调用产生动作：`job['process'].wait()`。 |
| 117 | 函数体 / finally保证清理 | 进入资源/状态范围：`job['lock']`；退出执行清理。 |
| 118 | 函数体 / finally保证清理 / with范围 | 计算表达式/调用产生动作：`_close(job)`。 |
| 119 | 函数体 / finally保证清理 / with范围 | 将 `True` 赋给 `job['done']`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="inspect-task"></a>
## inspect_task

按offset给状态与输出；完成子代理仅展示建议摘要。

```python
def inspect_task(task_id, offset=0)
```

位置：[122行](../../../process_tasks.py#L122) 至快照 152 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `task_id` | `未显式注解` | 仅当前CLI有效的owned任务ID。 |
| `offset` | `未显式注解` | 任务输出字节偏移，从0开始。 |

**调用表达式（静态提取，不含内层独立函数体）**：`JOBS.get`、`bytes`、`item.get`、`job['process'].poll`、`json.loads`、`len`、`min`、`raw[offset:offset + 16000].decode`、`result['agent_result'].get`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 123 | `job` | `JOBS.get(task_id)` | 当前进程的任务记录字典，包含进程、缓冲、锁和状态。 |
| 127 | `raw` | `bytes(job['output'])` | 未解码字节/完整输出快照，按编码与限额再处理。 |
| 128 | `result` | `{'ok': True, 'task_id': task_id, 'kind': job['kind'], 'state': 'finished' if job['done'] else 'running', 'exit_code': job['process…（见完整源码）` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 138 | `result['agent_result']` | `json.loads(raw)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 139 | `proposals` | `result['agent_result'].get('proposals', [])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 140 | `result['agent_result']['proposals']` | `[{key: item.get(key) for key in ('proposal_id', 'tool', 'path')} for item in proposals]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 143 | `result['output']` | `''` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 144 | `result['more_output']` | `False` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 145 | `reply` | `result['agent_result'].get('reply', '')` | 模型最终文字或明确终止说明。 |
| 147 | `result['agent_result']['reply']` | `reply[:16000]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 148 | `result['agent_result']['reply_truncated']` | `True` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 150 | `result['ok']` | `False` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 151 | `result['error']` | `'子代理异常结束，未返回有效结果'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 123 | 函数体 | 将 `JOBS.get(task_id)` 赋给 `job`。 |
| 124 | 函数体 | 条件 `job is None`：真时执行body，假时进入else/后续。 |
| 125 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '未知任务 ID；任务仅在当前 CLI 进程有效'}`，结束当前函数；具体分支见完整源码。 |
| 126 | 函数体 | 进入资源/状态范围：`job['lock']`；退出执行清理。 |
| 127 | 函数体 / with范围 | 将 `bytes(job['output'])` 赋给 `raw`。 |
| 128 | 函数体 / with范围 | 将 `{'ok': True, 'task_id': task_id, 'kind': job['kind'], 'state': 'finished' if job['done'] else 'running', 'exit_code': job['process'].poll(), 'reason': job['reason'], 'out…（见完整源码）` 赋给 `result`。 |
| 134 | 函数体 / with范围 | 条件 `offset > len(raw)`：真时执行body，假时进入else/后续。 |
| 135 | 函数体 / with范围 / 条件为真 | 返回 `{'ok': False, 'error': '输出偏移超过已收集长度'}`，结束当前函数；具体分支见完整源码。 |
| 136 | 函数体 / with范围 | 条件 `job['kind'] == 'agent' and job['done']`：真时执行body，假时进入else/后续。 |
| 137 | 函数体 / with范围 / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 138 | 函数体 / with范围 / 条件为真 / try | 将 `json.loads(raw)` 赋给 `result['agent_result']`。 |
| 139 | 函数体 / with范围 / 条件为真 / try | 将 `result['agent_result'].get('proposals', [])` 赋给 `proposals`。 |
| 140 | 函数体 / with范围 / 条件为真 / try | 将 `[{key: item.get(key) for key in ('proposal_id', 'tool', 'path')} for item in proposals]` 赋给 `result['agent_result']['proposals']`。 |
| 143 | 函数体 / with范围 / 条件为真 / try | 将 `''` 赋给 `result['output']`。 |
| 144 | 函数体 / with范围 / 条件为真 / try | 将 `False` 赋给 `result['more_output']`。 |
| 145 | 函数体 / with范围 / 条件为真 / try | 将 `result['agent_result'].get('reply', '')` 赋给 `reply`。 |
| 146 | 函数体 / with范围 / 条件为真 / try | 条件 `len(reply) > 16000`：真时执行body，假时进入else/后续。 |
| 147 | 函数体 / with范围 / 条件为真 / try / 条件为真 | 将 `reply[:16000]` 赋给 `result['agent_result']['reply']`。 |
| 148 | 函数体 / with范围 / 条件为真 / try / 条件为真 | 将 `True` 赋给 `result['agent_result']['reply_truncated']`。 |
| 149 | 函数体 / with范围 / 条件为真 | except (ValueError, UnicodeError)：只处理匹配类型的异常。 |
| 150 | 函数体 / with范围 / 条件为真 / except (ValueError, UnicodeError) | 将 `False` 赋给 `result['ok']`。 |
| 151 | 函数体 / with范围 / 条件为真 / except (ValueError, UnicodeError) | 将 `'子代理异常结束，未返回有效结果'` 赋给 `result['error']`。 |
| 152 | 函数体 / with范围 | 返回 `result`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L125：`{'ok': False, 'error': '未知任务 ID；任务仅在当前 CLI 进程有效'}`。
- L135：`{'ok': False, 'error': '输出偏移超过已收集长度'}`。
- L152：`result`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="send-input"></a>
## send_input

向活跃owned PTY写UTF-8输入。

```python
def send_input(task_id, text)
```

位置：[155行](../../../process_tasks.py#L155) 至快照 164 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `task_id` | `未显式注解` | 仅当前CLI有效的owned任务ID。 |
| `text` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`JOBS.get`、`job['process'].poll`、`len`、`os.write`、`text.encode`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 156 | `job` | `JOBS.get(task_id)` | 当前进程的任务记录字典，包含进程、缓冲、锁和状态。 |
| 162 | `data` | `text.encode('utf-8')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 163 | `written` | `os.write(job['fd'], data)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 156 | 函数体 | 将 `JOBS.get(task_id)` 赋给 `job`。 |
| 157 | 函数体 | 条件 `job is None or not job['terminal']`：真时执行body，假时进入else/后续。 |
| 158 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '未知 PTY 任务'}`，结束当前函数；具体分支见完整源码。 |
| 159 | 函数体 | 进入资源/状态范围：`job['lock']`；退出执行清理。 |
| 160 | 函数体 / with范围 | 条件 `job['done'] or job['process'].poll() is not None`：真时执行body，假时进入else/后续。 |
| 161 | 函数体 / with范围 / 条件为真 | 返回 `{'ok': False, 'error': '任务已结束'}`，结束当前函数；具体分支见完整源码。 |
| 162 | 函数体 / with范围 | 将 `text.encode('utf-8')` 赋给 `data`。 |
| 163 | 函数体 / with范围 | 将 `os.write(job['fd'], data)` 赋给 `written`。 |
| 164 | 函数体 / with范围 | 返回 `{'ok': written == len(data), 'bytes_written': written}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L158：`{'ok': False, 'error': '未知 PTY 任务'}`。
- L161：`{'ok': False, 'error': '任务已结束'}`。
- L164：`{'ok': written == len(data), 'bytes_written': written}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="cancel-task"></a>
## cancel_task

标取消、杀组、join后查结果。

```python
def cancel_task(task_id)
```

位置：[167行](../../../process_tasks.py#L167) 至快照 176 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `task_id` | `未显式注解` | 仅当前CLI有效的owned任务ID。 |

**调用表达式（静态提取，不含内层独立函数体）**：`JOBS.get`、`_kill`、`inspect_task`、`job['thread'].join`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 168 | `job` | `JOBS.get(task_id)` | 当前进程的任务记录字典，包含进程、缓冲、锁和状态。 |
| 173 | `job['reason']` | `'cancelled'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 168 | 函数体 | 将 `JOBS.get(task_id)` 赋给 `job`。 |
| 169 | 函数体 | 条件 `job is None`：真时执行body，假时进入else/后续。 |
| 170 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '未知任务'}`，结束当前函数；具体分支见完整源码。 |
| 171 | 函数体 | 条件 `job['done']`：真时执行body，假时进入else/后续。 |
| 172 | 函数体 / 条件为真 | 返回 `inspect_task(task_id)`，结束当前函数；具体分支见完整源码。 |
| 173 | 函数体 | 将 `'cancelled'` 赋给 `job['reason']`。 |
| 174 | 函数体 | 计算表达式/调用产生动作：`_kill(job)`。 |
| 175 | 函数体 | 计算表达式/调用产生动作：`job['thread'].join(timeout=2)`。 |
| 176 | 函数体 | 返回 `inspect_task(task_id)`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L170：`{'ok': False, 'error': '未知任务'}`。
- L172：`inspect_task(task_id)`。
- L176：`inspect_task(task_id)`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="wait-task"></a>
## wait_task

最多等待线程指定秒后返回当前状态。

```python
def wait_task(task_id, seconds=10)
```

位置：[179行](../../../process_tasks.py#L179) 至快照 184 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `task_id` | `未显式注解` | 仅当前CLI有效的owned任务ID。 |
| `seconds` | `未显式注解` | 等待任务的最大秒数。 |

**调用表达式（静态提取，不含内层独立函数体）**：`JOBS.get`、`inspect_task`、`job['thread'].join`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 180 | `job` | `JOBS.get(task_id)` | 当前进程的任务记录字典，包含进程、缓冲、锁和状态。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 180 | 函数体 | 将 `JOBS.get(task_id)` 赋给 `job`。 |
| 181 | 函数体 | 条件 `job is None`：真时执行body，假时进入else/后续。 |
| 182 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '未知任务'}`，结束当前函数；具体分支见完整源码。 |
| 183 | 函数体 | 计算表达式/调用产生动作：`job['thread'].join(timeout=seconds)`。 |
| 184 | 函数体 | 返回 `inspect_task(task_id)`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L182：`{'ok': False, 'error': '未知任务'}`。
- L184：`inspect_task(task_id)`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="list-tasks"></a>
## list_tasks

所有当前任务的简要状态。

```python
def list_tasks()
```

位置：[187行](../../../process_tasks.py#L187) 至快照 190 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`inspect_task`、`inspect_task(identifier).items`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 188 | 函数体 | 返回 `{'ok': True, 'tasks': [{key: value for key, value in inspect_task(identifier).items() if key in ('task_id', 'kind', 'state', 'exit_code', 'reason')} for identifier in JOB…（见完整源码）`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L188：`{'ok': True, 'tasks': [{key: value for key, value in inspect_task(identifier).items() if key in ('task_id', 'kind', 'state', 'exit_code', 'reason')} for identifier in JOBS]}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="close-tasks"></a>
## close_tasks

取消所有当前任务并清空内存表。

```python
def close_tasks()
```

位置：[193行](../../../process_tasks.py#L193) 至快照 196 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`JOBS.clear`、`cancel_task`、`list`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 194 | 函数体 | 遍历 `list(JOBS)`，每次绑定 `identifier`。 |
| 195 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`cancel_task(identifier)`。 |
| 196 | 函数体 | 计算表达式/调用产生动作：`JOBS.clear()`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="prepare-pty"></a>
## prepare_pty

复用沙箱前缀，恢复控制TTY后执行argv。

```python
def prepare_pty(path, argv, timeout=120)
```

位置：[202行](../../../process_tasks.py#L202) 至快照 219 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| `argv` | `未显式注解` | 待运行程序及参数列表，每项独立，不隐式shell拼接。 |
| `timeout` | `未显式注解` | 操作/任务超时秒数。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`build_test_command`、`command.index`、`json.dumps`、`prepare_tests`、`str`、`target.is_dir`、`target.relative_to`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 205 | `checked` | `prepare_tests(path)` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 208 | `target` | `Path(checked['path'])` | 已选定的文件/目录或操作目标，提交前可能需要再次验证。 |
| 211 | `command` | `build_test_command(target, checked['bwrap'])` | 安全构造的argv列表或解析出的命令名，避免将它们混为shell字符串。 |
| 212 | `split` | `command.index('--')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 214 | `helper` | `'import os,sys,fcntl,termios;\ntry: os.setsid()\nexcept PermissionError: pass\nfcntl.ioctl(0,termios.TIOCSCTTY,0); os.execvpe(sys.…（见完整源码）` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 215 | `command` | `command[:split + 1] + ['/usr/bin/python3', '-c', helper] + argv` | 安全构造的argv列表或解析出的命令名，避免将它们混为shell字符串。 |
| 216 | `cwd_index` | `command.index('--chdir') + 1` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 217 | `command[cwd_index]` | `str(Path('/workspace') / target.relative_to(PROJECT_ROOT))` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 203 | 函数体 | 在此处导入依赖：`from sandbox import prepare_tests, build_test_command`；局部导入可延迟加载或避免循环。 |
| 204 | 函数体 | 在此处导入依赖：`from permissions import PROJECT_ROOT`；局部导入可延迟加载或避免循环。 |
| 205 | 函数体 | 将 `prepare_tests(path)` 赋给 `checked`。 |
| 206 | 函数体 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 207 | 函数体 / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 208 | 函数体 | 将 `Path(checked['path'])` 赋给 `target`。 |
| 209 | 函数体 | 条件 `not target.is_dir()`：真时执行body，假时进入else/后续。 |
| 210 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': 'PTY 工作路径必须是目录'}`，结束当前函数；具体分支见完整源码。 |
| 211 | 函数体 | 将 `build_test_command(target, checked['bwrap'])` 赋给 `command`。 |
| 212 | 函数体 | 将 `command.index('--')` 赋给 `split`。 |
| 214 | 函数体 | 将 `'import os,sys,fcntl,termios;\ntry: os.setsid()\nexcept PermissionError: pass\nfcntl.ioctl(0,termios.TIOCSCTTY,0); os.execvpe(sys.argv[1],sys.argv[1:],os.environ)'` 赋给 `helper`。 |
| 215 | 函数体 | 将 `command[:split + 1] + ['/usr/bin/python3', '-c', helper] + argv` 赋给 `command`。 |
| 216 | 函数体 | 将 `command.index('--chdir') + 1` 赋给 `cwd_index`。 |
| 217 | 函数体 | 将 `str(Path('/workspace') / target.relative_to(PROJECT_ROOT))` 赋给 `command[cwd_index]`。 |
| 218 | 函数体 | 返回 `{'ok': True, 'command': command, 'timeout': timeout, 'details': '只读、禁网 PTY 命令: ' + json.dumps(argv, ensure_ascii=False) + '; 超时 ' + str(timeout)}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L207：`checked`。
- L210：`{'ok': False, 'error': 'PTY 工作路径必须是目录'}`。
- L218：`{'ok': True, 'command': command, 'timeout': timeout, 'details': '只读、禁网 PTY 命令: ' + json.dumps(argv, ensure_ascii=False) + '; 超时 ' + str(timeout)}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="start-pty"></a>
## start_pty

将prepared命令按PTY启动。

```python
def start_pty(prepared)
```

位置：[222行](../../../process_tasks.py#L222) 至快照 223 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `prepared` | `未显式注解` | prepare形成的待审快照：diff/字节或沙箱命令参数。 |

**调用表达式（静态提取，不含内层独立函数体）**：`launch`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 223 | 函数体 | 返回 `launch(prepared['command'], terminal=True, timeout=prepared['timeout'])`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L223：`launch(prepared['command'], terminal=True, timeout=prepared['timeout'])`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="start-agent"></a>
## start_agent

将任务、规则与配置快照发给独立可信worker。

```python
def start_agent(path, task)
```

位置：[226行](../../../process_tasks.py#L226) 至快照 236 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| `task` | `未显式注解` | 本轮用户目标或子代理独立任务文字，不等于授权。 |

**调用表达式（静态提取，不含内层独立函数体）**：`build_model_messages`、`dict`、`launch`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 232 | `payload` | `{'workspace': str(PROJECT_ROOT), 'path': path, 'task': task, 'model_config': dict(model_config), 'agent_config': dict(agent_config…（见完整源码）` | 传给子进程/独立审查/摘要请求的结构化数据快照。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 227 | 函数体 | 在此处导入依赖：`from config import model_config, agent_config`；局部导入可延迟加载或避免循环。 |
| 228 | 函数体 | 在此处导入依赖：`from project_instructions import build_model_messages`；局部导入可延迟加载或避免循环。 |
| 229 | 函数体 | 在此处导入依赖：`from permissions import PROJECT_ROOT`；局部导入可延迟加载或避免循环。 |
| 230 | 函数体 | 在此处导入依赖：`from workspace import APP_ROOT`；局部导入可延迟加载或避免循环。 |
| 232 | 函数体 | 将 `{'workspace': str(PROJECT_ROOT), 'path': path, 'task': task, 'model_config': dict(model_config), 'agent_config': dict(agent_config), 'instructions': build_model_messages(…（见完整源码）` 赋给 `payload`。 |
| 235 | 函数体 | 返回 `launch([str(APP_ROOT / '.conda-env/bin/python'), str(APP_ROOT / 'subagent_worker.py')], payload=payload, kind='agent', timeout=180)`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L235：`launch([str(APP_ROOT / '.conda-env/bin/python'), str(APP_ROOT / 'subagent_worker.py')], payload=payload, kind='agent', timeout=180)`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- with/yield：资源/状态生命周期或逐个生成：L22, L64, L100, L117, L126, L159。
- try/except/finally：异常与保证清理：L28, L48, L58, L71, L86, L94, L111, L137。
- 推导式/生成器表达式：循环建容器或逐个产生：L20, L23, L140, L141, L188。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """当前 CLI 的有界进程任务；PTY 使用沙箱，子代理使用独立可信工作进程。"""
0002 | import atexit
0003 | import json
0004 | import os
0005 | from pathlib import Path
0006 | import pty
0007 | import select
0008 | import signal
0009 | import subprocess
0010 | import threading
0011 | import time
0012 | import uuid
0013 | 
0014 | JOBS = {}
0015 | LOCK = threading.RLock()
0016 | MAX_OUTPUT = 65536
0017 | 
0018 | 
0019 | def launch(command, *, terminal=False, payload=None, timeout=120, kind='pty'):
0020 |     if kind == 'agent' and (not isinstance(payload, dict) or not all(isinstance(payload.get(key), str) for key in ('workspace', 'task'))):
0021 |         raise ValueError('子代理启动数据无效')
0022 |     with LOCK:
0023 |         if sum(job['process'].poll() is None for job in JOBS.values()) >= 4 or len(JOBS) >= 64:
0024 |             return {'ok': False, 'error': '任务数量达到上限（同时 4 个，本进程累计 64 个）'}
0025 |         master = slave = None
0026 |         if terminal:
0027 |             master, slave = pty.openpty()
0028 |         try:
0029 |             process = subprocess.Popen(command, stdin=slave if terminal else subprocess.PIPE,
0030 |                 stdout=slave if terminal else subprocess.PIPE, stderr=slave if terminal else subprocess.DEVNULL,
0031 |                 start_new_session=True, env=dict(os.environ) if kind == 'agent' else {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'})
0032 |         except BaseException:
0033 |             if master is not None:
0034 |                 os.close(master)
0035 |             raise
0036 |         finally:
0037 |             if slave is not None:
0038 |                 os.close(slave)
0039 |         identifier = uuid.uuid4().hex[:12]
0040 |         job = {'process': process, 'fd': master if terminal else process.stdout.fileno(),
0041 |                'output': bytearray(), 'reason': '', 'kind': kind, 'terminal': terminal,
0042 |                'done': False, 'lock': threading.RLock()}
0043 |         if kind == 'agent':
0044 |             from approval import current_task
0045 |             job['workspace'] = payload['workspace']
0046 |             job['task'] = current_task() or payload['task']
0047 |         JOBS[identifier] = job
0048 |     try:
0049 |         if payload is not None:
0050 |             process.stdin.write(json.dumps(payload, ensure_ascii=False).encode())
0051 |             process.stdin.close()
0052 |         thread = threading.Thread(target=_collect, args=(job, timeout), daemon=True)
0053 |         job['thread'] = thread
0054 |         thread.start()
0055 |     except BaseException:
0056 |         _kill(job)
0057 |         if process.stdin is not None and not terminal:
0058 |             try:
0059 |                 process.stdin.close()
0060 |             except OSError:
0061 |                 pass
0062 |         process.wait()
0063 |         _close(job)
0064 |         with LOCK:
0065 |             JOBS.pop(identifier, None)
0066 |         raise
0067 |     return {'ok': True, 'task_id': identifier, 'kind': kind, 'state': 'running'}
0068 | 
0069 | 
0070 | def _kill(job):
0071 |     try:
0072 |         os.killpg(job['process'].pid, signal.SIGKILL)
0073 |     except ProcessLookupError:
0074 |         pass
0075 | 
0076 | 
0077 | def _close(job):
0078 |     if job['terminal']:
0079 |         os.close(job['fd'])
0080 |     else:
0081 |         job['process'].stdout.close()
0082 | 
0083 | 
0084 | def _collect(job, timeout):
0085 |     deadline = time.monotonic() + timeout
0086 |     try:
0087 |         while True:
0088 |             if time.monotonic() >= deadline:
0089 |                 job['reason'] = 'timeout'
0090 |                 _kill(job)
0091 |                 break
0092 |             ready, _, _ = select.select([job['fd']], [], [], 0.1)
0093 |             if ready:
0094 |                 try:
0095 |                     chunk = os.read(job['fd'], 8192)
0096 |                 except OSError:
0097 |                     break
0098 |                 if not chunk:
0099 |                     break
0100 |                 with job['lock']:
0101 |                     remaining = MAX_OUTPUT - len(job['output'])
0102 |                     job['output'].extend(chunk[:remaining])
0103 |                     if len(chunk) > remaining:
0104 |                         job['reason'] = 'output_limit'
0105 |                         _kill(job)
0106 |                         break
0107 |             elif job['process'].poll() is not None:
0108 |                 break
0109 |     finally:
0110 |         # 给正常退出留出时间，然后清理仍占用终端的后代。
0111 |         try:
0112 |             job['process'].wait(timeout=0.2)
0113 |         except subprocess.TimeoutExpired:
0114 |             pass
0115 |         _kill(job)
0116 |         job['process'].wait()
0117 |         with job['lock']:
0118 |             _close(job)
0119 |             job['done'] = True
0120 | 
0121 | 
0122 | def inspect_task(task_id, offset=0):
0123 |     job = JOBS.get(task_id)
0124 |     if job is None:
0125 |         return {'ok': False, 'error': '未知任务 ID；任务仅在当前 CLI 进程有效'}
0126 |     with job['lock']:
0127 |         raw = bytes(job['output'])
0128 |         result = {'ok': True, 'task_id': task_id, 'kind': job['kind'],
0129 |                   'state': 'finished' if job['done'] else 'running',
0130 |                   'exit_code': job['process'].poll(), 'reason': job['reason'],
0131 |                   'output': raw[offset:offset+16000].decode('utf-8', errors='replace'),
0132 |                   'next_offset': min(len(raw), offset+16000), 'output_bytes': len(raw),
0133 |                   'more_output': len(raw) > offset+16000}
0134 |         if offset > len(raw):
0135 |             return {'ok': False, 'error': '输出偏移超过已收集长度'}
0136 |         if job['kind'] == 'agent' and job['done']:
0137 |             try:
0138 |                 result['agent_result'] = json.loads(raw)
0139 |                 proposals = result['agent_result'].get('proposals', [])
0140 |                 result['agent_result']['proposals'] = [
0141 |                     {key: item.get(key) for key in ('proposal_id', 'tool', 'path')} for item in proposals]
0142 |                 # 原始输出含建议源码；模型查询仅收到摘要，实际应用取内部完整数据。
0143 |                 result['output'] = ''
0144 |                 result['more_output'] = False
0145 |                 reply = result['agent_result'].get('reply', '')
0146 |                 if len(reply) > 16000:
0147 |                     result['agent_result']['reply'] = reply[:16000]
0148 |                     result['agent_result']['reply_truncated'] = True
0149 |             except (ValueError, UnicodeError):
0150 |                 result['ok'] = False
0151 |                 result['error'] = '子代理异常结束，未返回有效结果'
0152 |         return result
0153 | 
0154 | 
0155 | def send_input(task_id, text):
0156 |     job = JOBS.get(task_id)
0157 |     if job is None or not job['terminal']:
0158 |         return {'ok': False, 'error': '未知 PTY 任务'}
0159 |     with job['lock']:
0160 |         if job['done'] or job['process'].poll() is not None:
0161 |             return {'ok': False, 'error': '任务已结束'}
0162 |         data = text.encode('utf-8')
0163 |         written = os.write(job['fd'], data)
0164 |         return {'ok': written == len(data), 'bytes_written': written}
0165 | 
0166 | 
0167 | def cancel_task(task_id):
0168 |     job = JOBS.get(task_id)
0169 |     if job is None:
0170 |         return {'ok': False, 'error': '未知任务'}
0171 |     if job['done']:
0172 |         return inspect_task(task_id)
0173 |     job['reason'] = 'cancelled'
0174 |     _kill(job)
0175 |     job['thread'].join(timeout=2)
0176 |     return inspect_task(task_id)
0177 | 
0178 | 
0179 | def wait_task(task_id, seconds=10):
0180 |     job = JOBS.get(task_id)
0181 |     if job is None:
0182 |         return {'ok': False, 'error': '未知任务'}
0183 |     job['thread'].join(timeout=seconds)
0184 |     return inspect_task(task_id)
0185 | 
0186 | 
0187 | def list_tasks():
0188 |     return {'ok': True, 'tasks': [{key: value for key, value in inspect_task(identifier).items()
0189 |                                   if key in ('task_id', 'kind', 'state', 'exit_code', 'reason')}
0190 |                                  for identifier in JOBS]}
0191 | 
0192 | 
0193 | def close_tasks():
0194 |     for identifier in list(JOBS):
0195 |         cancel_task(identifier)
0196 |     JOBS.clear()
0197 | 
0198 | 
0199 | atexit.register(close_tasks)
0200 | 
0201 | 
0202 | def prepare_pty(path, argv, timeout=120):
0203 |     from sandbox import prepare_tests, build_test_command
0204 |     from permissions import PROJECT_ROOT
0205 |     checked = prepare_tests(path)
0206 |     if not checked['ok']:
0207 |         return checked
0208 |     target = Path(checked['path'])
0209 |     if not target.is_dir():
0210 |         return {'ok': False, 'error': 'PTY 工作路径必须是目录'}
0211 |     command = build_test_command(target, checked['bwrap'])
0212 |     split = command.index('--')
0213 |     # 在沙箱内恢复控制终端；在独立辅助解释器中执行，避免线程里 preexec_fn。
0214 |     helper = "import os,sys,fcntl,termios;\ntry: os.setsid()\nexcept PermissionError: pass\nfcntl.ioctl(0,termios.TIOCSCTTY,0); os.execvpe(sys.argv[1],sys.argv[1:],os.environ)"
0215 |     command = command[:split+1] + ['/usr/bin/python3', '-c', helper] + argv
0216 |     cwd_index = command.index('--chdir') + 1
0217 |     command[cwd_index] = str(Path('/workspace') / target.relative_to(PROJECT_ROOT))
0218 |     return {'ok': True, 'command': command, 'timeout': timeout,
0219 |             'details': '只读、禁网 PTY 命令: ' + json.dumps(argv, ensure_ascii=False) + '; 超时 ' + str(timeout)}
0220 | 
0221 | 
0222 | def start_pty(prepared):
0223 |     return launch(prepared['command'], terminal=True, timeout=prepared['timeout'])
0224 | 
0225 | 
0226 | def start_agent(path, task):
0227 |     from config import model_config, agent_config
0228 |     from project_instructions import build_model_messages
0229 |     from permissions import PROJECT_ROOT
0230 |     from workspace import APP_ROOT
0231 |     # 不共享父会话、MCP、可变模型配置；只读工具集合由可信工作进程确定。
0232 |     payload = {'workspace': str(PROJECT_ROOT), 'path': path, 'task': task,
0233 |                'model_config': dict(model_config), 'agent_config': dict(agent_config),
0234 |                'instructions': build_model_messages([])}
0235 |     return launch([str(APP_ROOT / '.conda-env/bin/python'), str(APP_ROOT / 'subagent_worker.py')],
0236 |                   payload=payload, kind='agent', timeout=180)
```
