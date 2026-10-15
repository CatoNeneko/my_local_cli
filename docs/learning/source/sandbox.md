# sandbox.py：源码导读

Linux bubblewrap固定pytest执行；只读、禁网、遮蔽私有、最小环境、时间输出限制。

先读专题：[06-processes.md](../06-processes.md)。

实际源码：[sandbox.py](../../../sandbox.py)。

快照 SHA256：`b3a6588df3b51ba2f392cfc76885f5cacb63c6956077283b561020bd469ed8aa`；186 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import os` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import selectors` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `import shutil` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `import signal` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `import subprocess` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `import sys` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `import time` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 9 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 11 | `from config import sandbox_config` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 12 | `from permissions import PROJECT_ROOT, protected_project_paths, resolve_project_path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 15 | `RUNTIME_ENV = PROJECT_ROOT / '.conda-env'` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [build_test_command](#build-test-command) | [18](../../../sandbox.py#L18) | 构造namespace、只读映射、私有遮蔽、最小环境与固定pytest argv。 |
| [collect_output](#collect-output) | [57](../../../sandbox.py#L57) | 非阻塞读管道、限时间/字节、超限/取消杀组回收。 |
| [prepare_tests](#prepare-tests) | [112](../../../sandbox.py#L112) | 检查平台、合法测试目标、bwrap、解释器和配置限制。 |
| [execute_prepared_tests](#execute-prepared-tests) | [151](../../../sandbox.py#L151) | 复查目标，实际沙箱运行，计算成功及截断/取消字段。 |
| [run_tests](#run-tests) | [183](../../../sandbox.py#L183) | 包装到共享执行器，不能旁路授权。 |

<a id="build-test-command"></a>
## build_test_command

构造namespace、只读映射、私有遮蔽、最小环境与固定pytest argv。

```python
def build_test_command(target, bwrap)
```

位置：[18行](../../../sandbox.py#L18) 至快照 54 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `target` | `未显式注解` | 已选定的文件/目录或操作目标，提交前可能需要再次验证。 |
| `bwrap` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`Path(library).exists`、`command.extend`、`protected_project_paths`、`str`、`target.relative_to`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 19 | `relative_path` | `target.relative_to(PROJECT_ROOT)` | 项目目标对应的相对路径，映射到沙箱workspace。 |
| 20 | `sandbox_target` | `str(Path('/workspace') / relative_path)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 21 | `command` | `[bwrap, '--unshare-user', '--unshare-pid', '--unshare-net', '--unshare-ipc', '--unshare-uts', '--die-with-parent', '--new-session'…（见完整源码）` | 安全构造的argv列表或解析出的命令名，避免将它们混为shell字符串。 |
| 38 | `destination` | `str(Path('/workspace') / relative_path)` | 新名称/导出/复制发布的目标路径。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 19 | 函数体 | 将 `target.relative_to(PROJECT_ROOT)` 赋给 `relative_path`。 |
| 20 | 函数体 | 将 `str(Path('/workspace') / relative_path)` 赋给 `sandbox_target`。 |
| 21 | 函数体 | 将 `[bwrap, '--unshare-user', '--unshare-pid', '--unshare-net', '--unshare-ipc', '--unshare-uts', '--die-with-parent', '--new-session', '--ro-bind', '/usr', '/usr']` 赋给 `command`。 |
| 26 | 函数体 | 遍历 `('/lib', '/lib64')`，每次绑定 `library`。 |
| 27 | 函数体 / 循环每次 | 条件 `Path(library).exists()`：真时执行body，假时进入else/后续。 |
| 28 | 函数体 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`command.extend(['--ro-bind', library, library])`。 |
| 30 | 函数体 | 计算表达式/调用产生动作：`command.extend(['--ro-bind', str(RUNTIME_ENV), '/runtime', '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp', '--chmod', '1777', '/tmp', '--ro-bind', str(PROJECT_ROOT…（见完整源码）`。 |
| 37 | 函数体 | 遍历 `protected_project_paths(PROJECT_ROOT)`，每次绑定 `(relative_path, is_directory)`。 |
| 38 | 函数体 / 循环每次 | 将 `str(Path('/workspace') / relative_path)` 赋给 `destination`。 |
| 39 | 函数体 / 循环每次 | 条件 `is_directory`：真时执行body，假时进入else/后续。 |
| 40 | 函数体 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`command.extend(['--tmpfs', destination])`。 |
| 42 | 函数体 / 循环每次 / 条件为假/elif | 计算表达式/调用产生动作：`command.extend(['--ro-bind', '/dev/null', destination])`。 |
| 44 | 函数体 | 计算表达式/调用产生动作：`command.extend(['--chdir', '/workspace', '--clearenv', '--setenv', 'HOME', '/tmp', '--setenv', 'PATH', '/runtime/bin:/usr/bin', '--setenv', 'LANG', 'C.UTF-8', '--setenv',…（见完整源码）`。 |
| 54 | 函数体 | 返回 `command`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L54：`command`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="collect-output"></a>
## collect_output

非阻塞读管道、限时间/字节、超限/取消杀组回收。

```python
def collect_output(command, timeout_seconds, max_output_bytes)
```

位置：[57行](../../../sandbox.py#L57) 至快照 109 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `command` | `未显式注解` | 安全构造的argv列表或解析出的命令名，避免将它们混为shell字符串。 |
| `timeout_seconds` | `未显式注解` | 真实进程运行超时秒数。 |
| `max_output_bytes` | `未显式注解` | 进程累计输出字节上限。 |

**调用表达式（静态提取，不含内层独立函数体）**：`bytearray`、`len`、`os.killpg`、`os.read`、`os.set_blocking`、`output_bytes.decode`、`output_bytes.extend`、`process.poll`、`process.stdout.close`、`process.stdout.fileno`、`process.wait`、`selector.get_map`、`selector.register`、`selector.select`、`selector.unregister`、`selectors.DefaultSelector`、`subprocess.Popen`、`time.monotonic`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 59 | `process` | `subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True, env=…（见完整源码）` | Popen实际子进程句柄，可poll/wait。 |
| 64 | `output_bytes` | `bytearray()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 65 | `timed_out` | `False` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 66 | `output_limit_exceeded` | `False` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 67 | `cancelled` | `False` | 当前任务/工具发生取消，之后不应继续执行同批动作。 |
| 68 | `deadline` | `time.monotonic() + timeout_seconds` | monotonic算出的结束时刻，不受墙上时钟调整影响。 |
| 76 | `timed_out` | `True` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 79 | `chunk` | `os.read(key.fd, 65536)` | 本次读取的输出字节或流式JSON块。 |
| 83 | `remaining` | `max_output_bytes - len(output_bytes)` | 还可读取/保存的字节配额。 |
| 86 | `output_limit_exceeded` | `True` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 93 | `cancelled` | `True` | 当前任务/工具发生取消，之后不应继续执行同批动作。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 58 | 函数体 | 文档字符串：说明职责，不作为普通语句动作执行。 |
| 59 | 函数体 | 将 `subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True, env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF…（见完整源码）` 赋给 `process`。 |
| 64 | 函数体 | 将 `bytearray()` 赋给 `output_bytes`。 |
| 65 | 函数体 | 将 `False` 赋给 `timed_out`。 |
| 66 | 函数体 | 将 `False` 赋给 `output_limit_exceeded`。 |
| 67 | 函数体 | 将 `False` 赋给 `cancelled`。 |
| 68 | 函数体 | 将 `time.monotonic() + timeout_seconds` 赋给 `deadline`。 |
| 70 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 71 | 函数体 / try | 进入资源/状态范围：`selectors.DefaultSelector()` 绑定 `selector`；退出执行清理。 |
| 72 | 函数体 / try / with范围 | 计算表达式/调用产生动作：`os.set_blocking(process.stdout.fileno(), False)`。 |
| 73 | 函数体 / try / with范围 | 计算表达式/调用产生动作：`selector.register(process.stdout, selectors.EVENT_READ)`。 |
| 74 | 函数体 / try / with范围 | 循环检查 `True`，break/return/异常可结束。 |
| 75 | 函数体 / try / with范围 / 循环每次 | 条件 `time.monotonic() >= deadline`：真时执行body，假时进入else/后续。 |
| 76 | 函数体 / try / with范围 / 循环每次 / 条件为真 | 将 `True` 赋给 `timed_out`。 |
| 77 | 函数体 / try / with范围 / 循环每次 / 条件为真 | break结束最近一层循环。 |
| 78 | 函数体 / try / with范围 / 循环每次 | 遍历 `selector.select(timeout=0.1)`，每次绑定 `(key, _)`。 |
| 79 | 函数体 / try / with范围 / 循环每次 / 循环每次 | 将 `os.read(key.fd, 65536)` 赋给 `chunk`。 |
| 80 | 函数体 / try / with范围 / 循环每次 / 循环每次 | 条件 `not chunk`：真时执行body，假时进入else/后续。 |
| 81 | 函数体 / try / with范围 / 循环每次 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`selector.unregister(key.fileobj)`。 |
| 82 | 函数体 / try / with范围 / 循环每次 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 83 | 函数体 / try / with范围 / 循环每次 / 循环每次 | 将 `max_output_bytes - len(output_bytes)` 赋给 `remaining`。 |
| 84 | 函数体 / try / with范围 / 循环每次 / 循环每次 | 计算表达式/调用产生动作：`output_bytes.extend(chunk[:remaining])`。 |
| 85 | 函数体 / try / with范围 / 循环每次 / 循环每次 | 条件 `len(chunk) > remaining`：真时执行body，假时进入else/后续。 |
| 86 | 函数体 / try / with范围 / 循环每次 / 循环每次 / 条件为真 | 将 `True` 赋给 `output_limit_exceeded`。 |
| 87 | 函数体 / try / with范围 / 循环每次 / 循环每次 / 条件为真 | break结束最近一层循环。 |
| 88 | 函数体 / try / with范围 / 循环每次 | 条件 `output_limit_exceeded`：真时执行body，假时进入else/后续。 |
| 89 | 函数体 / try / with范围 / 循环每次 / 条件为真 | break结束最近一层循环。 |
| 90 | 函数体 / try / with范围 / 循环每次 | 条件 `process.poll() is not None and (not selector.get_map())`：真时执行body，假时进入else/后续。 |
| 91 | 函数体 / try / with范围 / 循环每次 / 条件为真 | break结束最近一层循环。 |
| 92 | 函数体 | except KeyboardInterrupt：只处理匹配类型的异常。 |
| 93 | 函数体 / except KeyboardInterrupt | 将 `True` 赋给 `cancelled`。 |
| 95 | 函数体 / finally保证清理 | 条件 `process.poll() is None or cancelled or timed_out or output_limit_exceeded`：真时执行body，假时进入else/后续。 |
| 96 | 函数体 / finally保证清理 / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 97 | 函数体 / finally保证清理 / 条件为真 / try | 计算表达式/调用产生动作：`os.killpg(process.pid, signal.SIGKILL)`。 |
| 98 | 函数体 / finally保证清理 / 条件为真 | except ProcessLookupError：只处理匹配类型的异常。 |
| 99 | 函数体 / finally保证清理 / 条件为真 / except ProcessLookupError | pass占位，无动作。 |
| 100 | 函数体 / finally保证清理 | 计算表达式/调用产生动作：`process.wait()`。 |
| 101 | 函数体 / finally保证清理 | 计算表达式/调用产生动作：`process.stdout.close()`。 |
| 103 | 函数体 | 返回 `{'exit_code': process.returncode, 'output': output_bytes.decode('utf-8', errors='replace'), 'timed_out': timed_out, 'output_limit_exceeded': output_limit_exceeded, 'cance…（见完整源码）`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L103：`{'exit_code': process.returncode, 'output': output_bytes.decode('utf-8', errors='replace'), 'timed_out': timed_out, 'output_limit_exceeded': output_limit_exceeded, 'cancelled': cancelled}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="prepare-tests"></a>
## prepare_tests

检查平台、合法测试目标、bwrap、解释器和配置限制。

```python
def prepare_tests(path='.')
```

位置：[112行](../../../sandbox.py#L112) 至快照 148 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |

**调用表达式（静态提取，不含内层独立函数体）**：`(RUNTIME_ENV / 'bin/python').is_file`、`Path`、`any`、`isinstance`、`part.startswith`、`resolve_project_path`、`shutil.which`、`str`、`target.exists`、`target.is_dir`、`target.is_file`、`target.relative_to`、`type`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 118 | `path_result` | `resolve_project_path(path)` | 路径解析检查结果；成功携带真实绝对路径。 |
| 121 | `target` | `Path(path_result['path'])` | 已选定的文件/目录或操作目标，提交前可能需要再次验证。 |
| 127 | `relative_path` | `target.relative_to(PROJECT_ROOT)` | 项目目标对应的相对路径，映射到沙箱workspace。 |
| 131 | `bwrap` | `shutil.which('bwrap')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 135 | `timeout_seconds` | `sandbox_config['timeout_seconds']` | 真实进程运行超时秒数。 |
| 136 | `max_output_bytes` | `sandbox_config['max_output_bytes']` | 进程累计输出字节上限。 |
| 137 | `max_output_chars` | `sandbox_config['max_output_chars']` | 返回模型的输出文字字符上限。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 113 | 函数体 | 条件 `not isinstance(path, str) or not path`：真时执行body，假时进入else/后续。 |
| 114 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '测试路径必须是非空字符串'}`，结束当前函数；具体分支见完整源码。 |
| 115 | 函数体 | 条件 `sys.platform != 'linux'`：真时执行body，假时进入else/后续。 |
| 116 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '此沙箱仅支持 Linux/WSL，不会在宿主回退执行'}`，结束当前函数；具体分支见完整源码。 |
| 118 | 函数体 | 将 `resolve_project_path(path)` 赋给 `path_result`。 |
| 119 | 函数体 | 条件 `not path_result['ok']`：真时执行body，假时进入else/后续。 |
| 120 | 函数体 / 条件为真 | 返回 `path_result`，结束当前函数；具体分支见完整源码。 |
| 121 | 函数体 | 将 `Path(path_result['path'])` 赋给 `target`。 |
| 122 | 函数体 | 条件 `not target.exists()`：真时执行body，假时进入else/后续。 |
| 123 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '测试路径不存在'}`，结束当前函数；具体分支见完整源码。 |
| 124 | 函数体 | 条件 `not target.is_dir() and (not target.is_file() or target.suffix != '.py')`：真时执行body，假时进入else/后续。 |
| 125 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '请选择目录或 Python 测试文件'}`，结束当前函数；具体分支见完整源码。 |
| 127 | 函数体 | 将 `target.relative_to(PROJECT_ROOT)` 赋给 `relative_path`。 |
| 128 | 函数体 | 条件 `any((part.startswith('.') for part in relative_path.parts))`：真时执行body，假时进入else/后续。 |
| 129 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '不能以隐藏目录或隐藏文件作为测试目标'}`，结束当前函数；具体分支见完整源码。 |
| 131 | 函数体 | 将 `shutil.which('bwrap')` 赋给 `bwrap`。 |
| 132 | 函数体 | 条件 `not bwrap or not (RUNTIME_ENV / 'bin/python').is_file()`：真时执行body，假时进入else/后续。 |
| 133 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '缺少 bubblewrap 或项目解释器；拒绝回退到宿主'}`，结束当前函数；具体分支见完整源码。 |
| 135 | 函数体 | 将 `sandbox_config['timeout_seconds']` 赋给 `timeout_seconds`。 |
| 136 | 函数体 | 将 `sandbox_config['max_output_bytes']` 赋给 `max_output_bytes`。 |
| 137 | 函数体 | 将 `sandbox_config['max_output_chars']` 赋给 `max_output_chars`。 |
| 138 | 函数体 | 遍历 `(timeout_seconds, max_output_bytes, max_output_chars)`，每次绑定 `value`。 |
| 139 | 函数体 / 循环每次 | 条件 `type(value) is not int or value <= 0`：真时执行body，假时进入else/后续。 |
| 140 | 函数体 / 循环每次 / 条件为真 | 返回 `{'ok': False, 'error': '沙箱限制必须是正整数'}`，结束当前函数；具体分支见完整源码。 |
| 142 | 函数体 | 返回 `{'ok': True, 'path': str(target), 'bwrap': bwrap, 'timeout_seconds': timeout_seconds, 'max_output_bytes': max_output_bytes, 'max_output_chars': max_output_chars, 'details…（见完整源码）`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L114：`{'ok': False, 'error': '测试路径必须是非空字符串'}`。
- L116：`{'ok': False, 'error': '此沙箱仅支持 Linux/WSL，不会在宿主回退执行'}`。
- L120：`path_result`。
- L123：`{'ok': False, 'error': '测试路径不存在'}`。
- L125：`{'ok': False, 'error': '请选择目录或 Python 测试文件'}`。
- L129：`{'ok': False, 'error': '不能以隐藏目录或隐藏文件作为测试目标'}`。
- L133：`{'ok': False, 'error': '缺少 bubblewrap 或项目解释器；拒绝回退到宿主'}`。
- L140：`{'ok': False, 'error': '沙箱限制必须是正整数'}`。
- L142：`{'ok': True, 'path': str(target), 'bwrap': bwrap, 'timeout_seconds': timeout_seconds, 'max_output_bytes': max_output_bytes, 'max_output_chars': max_output_chars, 'details': '运行 pytest；项目只读、默认禁网；超时 ' + str(timeo…（见完整源码）`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="execute-prepared-tests"></a>
## execute_prepared_tests

复查目标，实际沙箱运行，计算成功及截断/取消字段。

```python
def execute_prepared_tests(prepared)
```

位置：[151行](../../../sandbox.py#L151) 至快照 180 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `prepared` | `未显式注解` | prepare形成的待审快照：diff/字节或沙箱命令参数。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`build_test_command`、`collect_output`、`len`、`resolve_project_path`、`result.get`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 153 | `checked` | `resolve_project_path(prepared['path'])` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 158 | `target` | `Path(checked['path'])` | 已选定的文件/目录或操作目标，提交前可能需要再次验证。 |
| 159 | `bwrap` | `prepared['bwrap']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 160 | `timeout_seconds` | `prepared['timeout_seconds']` | 真实进程运行超时秒数。 |
| 161 | `max_output_bytes` | `prepared['max_output_bytes']` | 进程累计输出字节上限。 |
| 162 | `max_output_chars` | `prepared['max_output_chars']` | 返回模型的输出文字字符上限。 |
| 163 | `command` | `build_test_command(target, bwrap)` | 安全构造的argv列表或解析出的命令名，避免将它们混为shell字符串。 |
| 165 | `result` | `collect_output(command, timeout_seconds, max_output_bytes)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 169 | `result['output_truncated']` | `len(result['output']) > max_output_chars or result['output_limit_exceeded']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 170 | `result['output']` | `result['output'][:max_output_chars]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 171 | `result['ok']` | `result['exit_code'] == 0 and (not result['timed_out']) and (not result['output_limit_exceeded']) and (not result.get('cancelled'))` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 173 | `result['error']` | `'测试已取消，沙箱子进程组已终止'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 175 | `result['error']` | `'测试超时，沙箱进程已终止'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 177 | `result['error']` | `'测试输出超限，沙箱进程已终止'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 179 | `result['error']` | `'测试未通过或沙箱启动失败，请查看 output 和 exit_code'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 152 | 函数体 | 文档字符串：说明职责，不作为普通语句动作执行。 |
| 153 | 函数体 | 将 `resolve_project_path(prepared['path'])` 赋给 `checked`。 |
| 154 | 函数体 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 155 | 函数体 / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 156 | 函数体 | 条件 `checked['path'] != prepared['path']`：真时执行body，假时进入else/后续。 |
| 157 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '测试目标已变化，请重新提交'}`，结束当前函数；具体分支见完整源码。 |
| 158 | 函数体 | 将 `Path(checked['path'])` 赋给 `target`。 |
| 159 | 函数体 | 将 `prepared['bwrap']` 赋给 `bwrap`。 |
| 160 | 函数体 | 将 `prepared['timeout_seconds']` 赋给 `timeout_seconds`。 |
| 161 | 函数体 | 将 `prepared['max_output_bytes']` 赋给 `max_output_bytes`。 |
| 162 | 函数体 | 将 `prepared['max_output_chars']` 赋给 `max_output_chars`。 |
| 163 | 函数体 | 将 `build_test_command(target, bwrap)` 赋给 `command`。 |
| 164 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 165 | 函数体 / try | 将 `collect_output(command, timeout_seconds, max_output_bytes)` 赋给 `result`。 |
| 166 | 函数体 | except OSError as error：只处理匹配类型的异常。 |
| 167 | 函数体 / except OSError as error | 返回 `{'ok': False, 'error': '无法启动沙箱: ' + str(error)}`，结束当前函数；具体分支见完整源码。 |
| 169 | 函数体 | 将 `len(result['output']) > max_output_chars or result['output_limit_exceeded']` 赋给 `result['output_truncated']`。 |
| 170 | 函数体 | 将 `result['output'][:max_output_chars]` 赋给 `result['output']`。 |
| 171 | 函数体 | 将 `result['exit_code'] == 0 and (not result['timed_out']) and (not result['output_limit_exceeded']) and (not result.get('cancelled'))` 赋给 `result['ok']`。 |
| 172 | 函数体 | 条件 `result.get('cancelled')`：真时执行body，假时进入else/后续。 |
| 173 | 函数体 / 条件为真 | 将 `'测试已取消，沙箱子进程组已终止'` 赋给 `result['error']`。 |
| 174 | 函数体 / 条件为假/elif | 条件 `result['timed_out']`：真时执行body，假时进入else/后续。 |
| 175 | 函数体 / 条件为假/elif / 条件为真 | 将 `'测试超时，沙箱进程已终止'` 赋给 `result['error']`。 |
| 176 | 函数体 / 条件为假/elif / 条件为假/elif | 条件 `result['output_limit_exceeded']`：真时执行body，假时进入else/后续。 |
| 177 | 函数体 / 条件为假/elif / 条件为假/elif / 条件为真 | 将 `'测试输出超限，沙箱进程已终止'` 赋给 `result['error']`。 |
| 178 | 函数体 / 条件为假/elif / 条件为假/elif / 条件为假/elif | 条件 `result['exit_code'] != 0`：真时执行body，假时进入else/后续。 |
| 179 | 函数体 / 条件为假/elif / 条件为假/elif / 条件为假/elif / 条件为真 | 将 `'测试未通过或沙箱启动失败，请查看 output 和 exit_code'` 赋给 `result['error']`。 |
| 180 | 函数体 | 返回 `result`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L155：`checked`。
- L157：`{'ok': False, 'error': '测试目标已变化，请重新提交'}`。
- L167：`{'ok': False, 'error': '无法启动沙箱: ' + str(error)}`。
- L180：`result`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="run-tests"></a>
## run_tests

包装到共享执行器，不能旁路授权。

```python
def run_tests(path='.')
```

位置：[183行](../../../sandbox.py#L183) 至快照 186 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |

**调用表达式（静态提取，不含内层独立函数体）**：`execute_tool`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 185 | 函数体 | 在此处导入依赖：`from tool_runtime import execute_tool`；局部导入可延迟加载或避免循环。 |
| 186 | 函数体 | 返回 `execute_tool('run_tests', {'path': path})`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L186：`execute_tool('run_tests', {'path': path})`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L70, L96, L164。
- with/yield：资源/状态生命周期或逐个生成：L71。
- 推导式/生成器表达式：循环建容器或逐个产生：L128。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """Linux bubblewrap 中的只读项目测试执行器，不提供宿主回退。"""
0002 | import os
0003 | import selectors
0004 | import shutil
0005 | import signal
0006 | import subprocess
0007 | import sys
0008 | import time
0009 | from pathlib import Path
0010 | 
0011 | from config import sandbox_config
0012 | from permissions import PROJECT_ROOT, protected_project_paths, resolve_project_path
0013 | 
0014 | 
0015 | RUNTIME_ENV = PROJECT_ROOT / ".conda-env"
0016 | 
0017 | 
0018 | def build_test_command(target, bwrap):
0019 |     relative_path = target.relative_to(PROJECT_ROOT)
0020 |     sandbox_target = str(Path("/workspace") / relative_path)
0021 |     command = [
0022 |         bwrap, "--unshare-user", "--unshare-pid", "--unshare-net",
0023 |         "--unshare-ipc", "--unshare-uts", "--die-with-parent", "--new-session",
0024 |         "--ro-bind", "/usr", "/usr"
0025 |     ]
0026 |     for library in ("/lib", "/lib64"):
0027 |         if Path(library).exists():
0028 |             command.extend(["--ro-bind", library, library])
0029 | 
0030 |     command.extend([
0031 |         "--ro-bind", str(RUNTIME_ENV), "/runtime",
0032 |         "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
0033 |         "--chmod", "1777", "/tmp",
0034 |         "--ro-bind", str(PROJECT_ROOT), "/workspace"
0035 |     ])
0036 |     # 项目内容可读；环境、控制配置及历史不暴露给测试进程。
0037 |     for relative_path, is_directory in protected_project_paths(PROJECT_ROOT):
0038 |         destination = str(Path("/workspace") / relative_path)
0039 |         if is_directory:
0040 |             command.extend(["--tmpfs", destination])
0041 |         else:
0042 |             command.extend(["--ro-bind", "/dev/null", destination])
0043 | 
0044 |     command.extend([
0045 |         "--chdir", "/workspace", "--clearenv",
0046 |         "--setenv", "HOME", "/tmp",
0047 |         "--setenv", "PATH", "/runtime/bin:/usr/bin",
0048 |         "--setenv", "LANG", "C.UTF-8",
0049 |         "--setenv", "PYTHONDONTWRITEBYTECODE", "1",
0050 |         "--setenv", "PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1",
0051 |         "--", "/runtime/bin/python", "-m", "pytest",
0052 |         "-q", "-p", "no:cacheprovider", "--", sandbox_target
0053 |     ])
0054 |     return command
0055 | 
0056 | 
0057 | def collect_output(command, timeout_seconds, max_output_bytes):
0058 |     """同时限制运行时间和捕获字节，超限时终止整个子进程组。"""
0059 |     process = subprocess.Popen(
0060 |         command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
0061 |         stderr=subprocess.STDOUT, start_new_session=True,
0062 |         env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
0063 |     )
0064 |     output_bytes = bytearray()
0065 |     timed_out = False
0066 |     output_limit_exceeded = False
0067 |     cancelled = False
0068 |     deadline = time.monotonic() + timeout_seconds
0069 | 
0070 |     try:
0071 |         with selectors.DefaultSelector() as selector:
0072 |             os.set_blocking(process.stdout.fileno(), False)
0073 |             selector.register(process.stdout, selectors.EVENT_READ)
0074 |             while True:
0075 |                 if time.monotonic() >= deadline:
0076 |                     timed_out = True
0077 |                     break
0078 |                 for key, _ in selector.select(timeout=0.1):
0079 |                     chunk = os.read(key.fd, 65536)
0080 |                     if not chunk:
0081 |                         selector.unregister(key.fileobj)
0082 |                         continue
0083 |                     remaining = max_output_bytes - len(output_bytes)
0084 |                     output_bytes.extend(chunk[:remaining])
0085 |                     if len(chunk) > remaining:
0086 |                         output_limit_exceeded = True
0087 |                         break
0088 |                 if output_limit_exceeded:
0089 |                     break
0090 |                 if process.poll() is not None and not selector.get_map():
0091 |                     break
0092 |     except KeyboardInterrupt:
0093 |         cancelled = True
0094 |     finally:
0095 |         if process.poll() is None or cancelled or timed_out or output_limit_exceeded:
0096 |             try:
0097 |                 os.killpg(process.pid, signal.SIGKILL)
0098 |             except ProcessLookupError:
0099 |                 pass
0100 |         process.wait()
0101 |         process.stdout.close()
0102 | 
0103 |     return {
0104 |         "exit_code": process.returncode,
0105 |         "output": output_bytes.decode("utf-8", errors="replace"),
0106 |         "timed_out": timed_out,
0107 |         "output_limit_exceeded": output_limit_exceeded,
0108 |         "cancelled": cancelled
0109 |     }
0110 | 
0111 | 
0112 | def prepare_tests(path="."):
0113 |     if not isinstance(path, str) or not path:
0114 |         return {"ok": False, "error": "测试路径必须是非空字符串"}
0115 |     if sys.platform != "linux":
0116 |         return {"ok": False, "error": "此沙箱仅支持 Linux/WSL，不会在宿主回退执行"}
0117 | 
0118 |     path_result = resolve_project_path(path)
0119 |     if not path_result["ok"]:
0120 |         return path_result
0121 |     target = Path(path_result["path"])
0122 |     if not target.exists():
0123 |         return {"ok": False, "error": "测试路径不存在"}
0124 |     if not target.is_dir() and (not target.is_file() or target.suffix != ".py"):
0125 |         return {"ok": False, "error": "请选择目录或 Python 测试文件"}
0126 |     # 即使调用者指定运行时/隐藏控制目录，也不能拿它们作为测试目标。
0127 |     relative_path = target.relative_to(PROJECT_ROOT)
0128 |     if any(part.startswith(".") for part in relative_path.parts):
0129 |         return {"ok": False, "error": "不能以隐藏目录或隐藏文件作为测试目标"}
0130 | 
0131 |     bwrap = shutil.which("bwrap")
0132 |     if not bwrap or not (RUNTIME_ENV / "bin/python").is_file():
0133 |         return {"ok": False, "error": "缺少 bubblewrap 或项目解释器；拒绝回退到宿主"}
0134 | 
0135 |     timeout_seconds = sandbox_config["timeout_seconds"]
0136 |     max_output_bytes = sandbox_config["max_output_bytes"]
0137 |     max_output_chars = sandbox_config["max_output_chars"]
0138 |     for value in (timeout_seconds, max_output_bytes, max_output_chars):
0139 |         if type(value) is not int or value <= 0:
0140 |             return {"ok": False, "error": "沙箱限制必须是正整数"}
0141 | 
0142 |     return {
0143 |         "ok": True, "path": str(target), "bwrap": bwrap,
0144 |         "timeout_seconds": timeout_seconds,
0145 |         "max_output_bytes": max_output_bytes,
0146 |         "max_output_chars": max_output_chars,
0147 |         "details": "运行 pytest；项目只读、默认禁网；超时 " + str(timeout_seconds) + " 秒"
0148 |     }
0149 | 
0150 | 
0151 | def execute_prepared_tests(prepared):
0152 |     """内部执行实现；调用前须经过统一授权入口。"""
0153 |     checked = resolve_project_path(prepared["path"])
0154 |     if not checked["ok"]:
0155 |         return checked
0156 |     if checked["path"] != prepared["path"]:
0157 |         return {"ok": False, "error": "测试目标已变化，请重新提交"}
0158 |     target = Path(checked["path"])
0159 |     bwrap = prepared["bwrap"]
0160 |     timeout_seconds = prepared["timeout_seconds"]
0161 |     max_output_bytes = prepared["max_output_bytes"]
0162 |     max_output_chars = prepared["max_output_chars"]
0163 |     command = build_test_command(target, bwrap)
0164 |     try:
0165 |         result = collect_output(command, timeout_seconds, max_output_bytes)
0166 |     except OSError as error:
0167 |         return {"ok": False, "error": "无法启动沙箱: " + str(error)}
0168 | 
0169 |     result["output_truncated"] = len(result["output"]) > max_output_chars or result["output_limit_exceeded"]
0170 |     result["output"] = result["output"][:max_output_chars]
0171 |     result["ok"] = result["exit_code"] == 0 and not result["timed_out"] and not result["output_limit_exceeded"] and not result.get('cancelled')
0172 |     if result.get('cancelled'):
0173 |         result['error'] = '测试已取消，沙箱子进程组已终止'
0174 |     elif result["timed_out"]:
0175 |         result["error"] = "测试超时，沙箱进程已终止"
0176 |     elif result["output_limit_exceeded"]:
0177 |         result["error"] = "测试输出超限，沙箱进程已终止"
0178 |     elif result["exit_code"] != 0:
0179 |         result["error"] = "测试未通过或沙箱启动失败，请查看 output 和 exit_code"
0180 |     return result
0181 | 
0182 | 
0183 | def run_tests(path="."):
0184 |     # 对 Python 调用也保留同一授权路径，不能绕过确认。
0185 |     from tool_runtime import execute_tool
0186 |     return execute_tool("run_tests", {"path": path})
```
