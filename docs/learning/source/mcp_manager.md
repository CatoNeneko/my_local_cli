# mcp_manager.py：源码导读

同步CLI与异步常驻MCP连接的桥；同任务持有SDK资源并关闭。

先读专题：[05-extensions.md](../05-extensions.md)。

实际源码：[mcp_manager.py](../../../mcp_manager.py)。

快照 SHA256：`804a11235c1138accee7a1da2a9b5b52f93dc73a70d87601f20a324bda6b9a8a`；183 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import asyncio` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `from datetime import timedelta` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `from anyio import TASK_STATUS_IGNORED` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `from anyio.from_thread import start_blocking_portal` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `from mcp import ClientSession` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `from mcp.client.stdio import stdio_client` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 10 | `from audit import record_tool_event` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 11 | `from config import mcp_config` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 12 | `from mcp_client import call_session_tool, collect_tools, prepare_server_connection` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 13 | `from mcp_tools import register_server_tools, unregister_server_tools` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 14 | `from permissions import authorize_external_tool` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [MCPManager.__init__](#mcpmanager---init--) | [18](../../../mcp_manager.py#L18) | 构造对象的初始状态；调用类创建对象时自动执行。 |
| [MCPManager.__enter__](#mcpmanager---enter--) | [22](../../../mcp_manager.py#L22) | 启动blocking portal并返回本对象，建立with资源范围。 |
| [MCPManager.__exit__](#mcpmanager---exit--) | [27](../../../mcp_manager.py#L27) | 逐服务disconnect，finally关闭portal。 |
| [MCPManager._serve](#mcpmanager--serve) | [35](../../../mcp_manager.py#L35) | 确保连接任务退出时设置closed事件。 |
| [MCPManager._serve_connected](#mcpmanager--serve-connected) | [42](../../../mcp_manager.py#L42) | 同异步任务持有SDK上下文，用队列处理call/refresh/close。 |
| [MCPManager._request](#mcpmanager--request) | [80](../../../mcp_manager.py#L80) | 放入队列，等待响应或连接拥有者结束，超时失败。 |
| [MCPManager.connect](#mcpmanager-connect) | [93](../../../mcp_manager.py#L93) | 授权启动，等待真实握手与发现后登记服务及工具。 |
| [MCPManager.load_configured](#mcpmanager-load-configured) | [119](../../../mcp_manager.py#L119) | 逐个连接可信配置中服务。 |
| [MCPManager.request](#mcpmanager-request) | [122](../../../mcp_manager.py#L122) | 同步portal桥接请求，异常断开，取消则abort。 |
| [MCPManager.call_tool](#mcpmanager-call-tool) | [138](../../../mcp_manager.py#L138) | 组装call操作，转共享request。 |
| [MCPManager.refresh](#mcpmanager-refresh) | [141](../../../mcp_manager.py#L141) | 断开则重连，否则发现并重新注册。 |
| [MCPManager.disconnect](#mcpmanager-disconnect) | [155](../../../mcp_manager.py#L155) | 注销工具，通知close，等待或取消连接拥有者。 |
| [MCPManager._wait_closed](#mcpmanager--wait-closed) | [166](../../../mcp_manager.py#L166) | 等待异步退出事件，最多5秒。 |
| [MCPManager.abort](#mcpmanager-abort) | [170](../../../mcp_manager.py#L170) | 取消拥有者而非排队close，注销并等清理。 |
| [MCPManager.tool_names](#mcpmanager-tool-names) | [181](../../../mcp_manager.py#L181) | 从注册表列出当前MCP名称。 |

<a id="mcpmanager---init--"></a>
## MCPManager.__init__

构造对象的初始状态；self上的字段会在后续方法中继续使用。

```python
def __init__(self)
```

位置：[18行](../../../mcp_manager.py#L18) 至快照 20 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：无直接调用。

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 19 | `self.services` | `{}` | 服务名到常驻MCP连接句柄的字典。 |
| 20 | `self.portal` | `None` | 同步CLI向后台异步事件循环发请求的桥接对象。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 19 | 函数体 | 将 `{}` 赋给 `self.services`。 |
| 20 | 函数体 | 将 `None` 赋给 `self.portal`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="mcpmanager---enter--"></a>
## MCPManager.__enter__

启动blocking portal并返回本对象，建立with资源范围。

```python
def __enter__(self)
```

位置：[22行](../../../mcp_manager.py#L22) 至快照 25 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：`self.portal_context.__enter__`、`start_blocking_portal`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 23 | `self.portal_context` | `start_blocking_portal()` | 持有portal资源范围，退出关闭异步循环线程。 |
| 24 | `self.portal` | `self.portal_context.__enter__()` | 同步CLI向后台异步事件循环发请求的桥接对象。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 23 | 函数体 | 将 `start_blocking_portal()` 赋给 `self.portal_context`。 |
| 24 | 函数体 | 将 `self.portal_context.__enter__()` 赋给 `self.portal`。 |
| 25 | 函数体 | 返回 `self`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L25：`self`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="mcpmanager---exit--"></a>
## MCPManager.__exit__

逐服务disconnect，finally关闭portal。

```python
def __exit__(self, exc_type, exc_value, traceback)
```

位置：[27行](../../../mcp_manager.py#L27) 至快照 33 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `exc_type` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `exc_value` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `traceback` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`list`、`self.disconnect`、`self.portal_context.__exit__`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 33 | `self.portal` | `None` | 同步CLI向后台异步事件循环发请求的桥接对象。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 28 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 29 | 函数体 / try | 遍历 `list(self.services)`，每次绑定 `name`。 |
| 30 | 函数体 / try / 循环每次 | 计算表达式/调用产生动作：`self.disconnect(name)`。 |
| 32 | 函数体 / finally保证清理 | 计算表达式/调用产生动作：`self.portal_context.__exit__(exc_type, exc_value, traceback)`。 |
| 33 | 函数体 / finally保证清理 | 将 `None` 赋给 `self.portal`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="mcpmanager--serve"></a>
## MCPManager._serve

确保连接任务退出时设置closed事件。

```python
async def _serve(self, connection, *, task_status=TASK_STATUS_IGNORED)
```

位置：[35行](../../../mcp_manager.py#L35) 至快照 40 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `connection` | `未显式注解` | 固定MCP启动参数与路由信息。 |
| `task_status` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`asyncio.Event`、`closed.set`、`self._serve_connected`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 36 | `closed` | `asyncio.Event()` | 连接清理完成时设置的Event。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 36 | 函数体 | 将 `asyncio.Event()` 赋给 `closed`。 |
| 37 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 38 | 函数体 / try | 计算表达式/调用产生动作：`await self._serve_connected(connection, closed, task_status=task_status)`。 |
| 40 | 函数体 / finally保证清理 | 计算表达式/调用产生动作：`closed.set()`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="mcpmanager--serve-connected"></a>
## MCPManager._serve_connected

同异步任务持有SDK上下文，用队列处理call/refresh/close。

```python
async def _serve_connected(self, connection, closed, *, task_status=TASK_STATUS_IGNORED)
```

位置：[42行](../../../mcp_manager.py#L42) 至快照 78 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `connection` | `未显式注解` | 固定MCP启动参数与路由信息。 |
| `closed` | `未显式注解` | 连接清理完成时设置的Event。 |
| `task_status` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ClientSession`、`asyncio.Queue`、`asyncio.timeout`、`call_session_tool`、`collect_tools`、`initialized.serverInfo.model_dump`、`queue.get`、`response.done`、`response.set_result`、`session.initialize`、`stdio_client`、`task_status.started`、`timedelta`、`type`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 44 | `queue` | `asyncio.Queue()` | MCP连接拥有者的异步操作队列，串行处理调用。 |
| 51 | `initialized` | `await session.initialize()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 52 | `tools` | `await collect_tools(session)` | 发给模型的工具声明列表，不含handler函数对象。 |
| 60 | `(operation, arguments, response)` | `await queue.get()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 67 | `result` | `{'ok': True, 'tools': await collect_tools(session)}` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 69 | `result` | `await call_session_tool(session, *arguments)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 44 | 函数体 | 将 `asyncio.Queue()` 赋给 `queue`。 |
| 45 | 函数体 | 进入资源/状态范围：`stdio_client(connection['parameters'])` 绑定 `(read_stream, write_stream)`；退出执行清理。 |
| 46 | 函数体 / with范围 | 进入资源/状态范围：`ClientSession(read_stream, write_stream, read_timeout_seconds=timedelta(seconds=connection['timeout']))` 绑定 `session`；退出执行清理。 |
| 50 | 函数体 / with范围 / with范围 | 进入资源/状态范围：`asyncio.timeout(connection['timeout'])`；退出执行清理。 |
| 51 | 函数体 / with范围 / with范围 / with范围 | 将 `await session.initialize()` 赋给 `initialized`。 |
| 52 | 函数体 / with范围 / with范围 / with范围 | 将 `await collect_tools(session)` 赋给 `tools`。 |
| 53 | 函数体 / with范围 / with范围 | 计算表达式/调用产生动作：`task_status.started({'queue': queue, 'closed': closed, 'server': initialized.serverInfo.model_dump(mode='json'), 'tools': tools})`。 |
| 59 | 函数体 / with范围 / with范围 | 循环检查 `True`，break/return/异常可结束。 |
| 60 | 函数体 / with范围 / with范围 / 循环每次 | 将 `await queue.get()` 赋给 `(operation, arguments, response)`。 |
| 61 | 函数体 / with范围 / with范围 / 循环每次 | 条件 `operation == 'close'`：真时执行body，假时进入else/后续。 |
| 62 | 函数体 / with范围 / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`response.set_result({'ok': True})`。 |
| 63 | 函数体 / with范围 / with范围 / 循环每次 / 条件为真 | 返回 `None`，结束当前函数；具体分支见完整源码。 |
| 64 | 函数体 / with范围 / with范围 / 循环每次 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 65 | 函数体 / with范围 / with范围 / 循环每次 / try | 进入资源/状态范围：`asyncio.timeout(connection['timeout'])`；退出执行清理。 |
| 66 | 函数体 / with范围 / with范围 / 循环每次 / try / with范围 | 条件 `operation == 'refresh'`：真时执行body，假时进入else/后续。 |
| 67 | 函数体 / with范围 / with范围 / 循环每次 / try / with范围 / 条件为真 | 将 `{'ok': True, 'tools': await collect_tools(session)}` 赋给 `result`。 |
| 69 | 函数体 / with范围 / with范围 / 循环每次 / try / with范围 / 条件为假/elif | 将 `await call_session_tool(session, *arguments)` 赋给 `result`。 |
| 70 | 函数体 / with范围 / with范围 / 循环每次 / try | 条件 `not response.done()`：真时执行body，假时进入else/后续。 |
| 71 | 函数体 / with范围 / with范围 / 循环每次 / try / 条件为真 | 计算表达式/调用产生动作：`response.set_result(result)`。 |
| 72 | 函数体 / with范围 / with范围 / 循环每次 | except Exception as error：只处理匹配类型的异常。 |
| 73 | 函数体 / with范围 / with范围 / 循环每次 / except Exception as error | 条件 `not response.done()`：真时执行body，假时进入else/后续。 |
| 74 | 函数体 / with范围 / with范围 / 循环每次 / except Exception as error / 条件为真 | 计算表达式/调用产生动作：`response.set_result({'ok': False, 'disconnected': True, 'error': 'MCP 通信失败: ' + type(error).__name__})`。 |
| 78 | 函数体 / with范围 / with范围 / 循环每次 / except Exception as error | 返回 `None`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L63：`None`。
- L78：`None`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="mcpmanager--request"></a>
## MCPManager._request

放入队列，等待响应或连接拥有者结束，超时失败。

```python
async def _request(self, handle, operation, arguments)
```

位置：[80行](../../../mcp_manager.py#L80) 至快照 91 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `handle` | `未显式注解` | MCP连接句柄，或当前资源引用。 |
| `operation` | `未显式注解` | read/write/execute操作分类，用于权限与Hook。 |
| `arguments` | `未显式注解` | 外部或模型提交的工具参数，必须经schema检查。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ConnectionError`、`asyncio.get_running_loop`、`asyncio.get_running_loop().create_future`、`asyncio.wait`、`asyncio.wrap_future`、`handle['queue'].put`、`response.cancel`、`response.result`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 81 | `response` | `asyncio.get_running_loop().create_future()` | HTTP响应流或异步请求Future，依当前模块。 |
| 83 | `stopped` | `asyncio.wrap_future(handle['future'])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 84 | `(done, pending)` | `await asyncio.wait([response, stopped], timeout=handle['connection']['timeout'] + 3, return_when=asyncio.FIRST_COMPLETED)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 81 | 函数体 | 将 `asyncio.get_running_loop().create_future()` 赋给 `response`。 |
| 82 | 函数体 | 计算表达式/调用产生动作：`await handle['queue'].put((operation, arguments, response))`。 |
| 83 | 函数体 | 将 `asyncio.wrap_future(handle['future'])` 赋给 `stopped`。 |
| 84 | 函数体 | 将 `await asyncio.wait([response, stopped], timeout=handle['connection']['timeout'] + 3, return_when=asyncio.FIRST_COMPLETED)` 赋给 `(done, pending)`。 |
| 88 | 函数体 | 条件 `response in done`：真时执行body，假时进入else/后续。 |
| 89 | 函数体 / 条件为真 | 返回 `response.result()`，结束当前函数；具体分支见完整源码。 |
| 90 | 函数体 | 计算表达式/调用产生动作：`response.cancel()`。 |
| 91 | 函数体 | 抛出 `ConnectionError('MCP 服务已停止或请求超时')`。 |

**实际返回分支**：

- L89：`response.result()`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="mcpmanager-connect"></a>
## MCPManager.connect

授权启动，等待真实握手与发现后登记服务及工具。

```python
def connect(self, name)
```

位置：[93行](../../../mcp_manager.py#L93) 至快照 117 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |

**调用表达式（静态提取，不含内层独立函数体）**：`authorize_external_tool`、`authorized.get`、`prepare_server_connection`、`record_tool_event`、`register_server_tools`、`self.disconnect`、`self.portal.start_task`、`type`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 96 | `connection` | `prepare_server_connection(name)` | 固定MCP启动参数与路由信息。 |
| 99 | `authorized` | `authorize_external_tool('mcp_connect', name, 'user', connection['details'])` | 批准与目标复查结果；失败不能调用实际handler。 |
| 104 | `(future, started)` | `self.portal.start_task(self._serve, connection)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 105 | `connection['manager']` | `self` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 106 | `connection['server_name']` | `name` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 107 | `self.services[name]` | `{**started, 'future': future, 'connection': connection}` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 110 | `result` | `register_server_tools(name, {**started, 'connection': connection})` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 114 | `result` | `{'ok': False, 'error': 'MCP 启动失败: ' + type(error).__name__}` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 115 | `result` | `{**result, 'approval': authorized.get('approval', [])}` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 94 | 函数体 | 条件 `name in self.services`：真时执行body，假时进入else/后续。 |
| 95 | 函数体 / 条件为真 | 返回 `{'ok': True, 'message': 'MCP 服务已经连接'}`，结束当前函数；具体分支见完整源码。 |
| 96 | 函数体 | 将 `prepare_server_connection(name)` 赋给 `connection`。 |
| 97 | 函数体 | 条件 `not connection['ok']`：真时执行body，假时进入else/后续。 |
| 98 | 函数体 / 条件为真 | 返回 `connection`，结束当前函数；具体分支见完整源码。 |
| 99 | 函数体 | 将 `authorize_external_tool('mcp_connect', name, 'user', connection['details'])` 赋给 `authorized`。 |
| 100 | 函数体 | 条件 `not authorized['ok']`：真时执行body，假时进入else/后续。 |
| 101 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`record_tool_event('mcp_connect', authorized)`。 |
| 102 | 函数体 / 条件为真 | 返回 `authorized`，结束当前函数；具体分支见完整源码。 |
| 103 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 104 | 函数体 / try | 将 `self.portal.start_task(self._serve, connection)` 赋给 `(future, started)`。 |
| 105 | 函数体 / try | 将 `self` 赋给 `connection['manager']`。 |
| 106 | 函数体 / try | 将 `name` 赋给 `connection['server_name']`。 |
| 107 | 函数体 / try | 将 `{**started, 'future': future, 'connection': connection}` 赋给 `self.services[name]`。 |
| 110 | 函数体 / try | 将 `register_server_tools(name, {**started, 'connection': connection})` 赋给 `result`。 |
| 111 | 函数体 / try | 条件 `not result['ok']`：真时执行body，假时进入else/后续。 |
| 112 | 函数体 / try / 条件为真 | 计算表达式/调用产生动作：`self.disconnect(name)`。 |
| 113 | 函数体 | except Exception as error：只处理匹配类型的异常。 |
| 114 | 函数体 / except Exception as error | 将 `{'ok': False, 'error': 'MCP 启动失败: ' + type(error).__name__}` 赋给 `result`。 |
| 115 | 函数体 | 将 `{**result, 'approval': authorized.get('approval', [])}` 赋给 `result`。 |
| 116 | 函数体 | 计算表达式/调用产生动作：`record_tool_event('mcp_connect', result)`。 |
| 117 | 函数体 | 返回 `result`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L95：`{'ok': True, 'message': 'MCP 服务已经连接'}`。
- L98：`connection`。
- L102：`authorized`。
- L117：`result`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="mcpmanager-load-configured"></a>
## MCPManager.load_configured

逐个连接可信配置中服务。

```python
def load_configured(self)
```

位置：[119行](../../../mcp_manager.py#L119) 至快照 120 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：`self.connect`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 120 | 函数体 | 返回 `{name: self.connect(name) for name in mcp_config}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L120：`{name: self.connect(name) for name in mcp_config}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="mcpmanager-request"></a>
## MCPManager.request

同步portal桥接请求，异常断开，取消则abort。

```python
def request(self, name, operation, arguments=())
```

位置：[122行](../../../mcp_manager.py#L122) 至快照 136 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| `operation` | `未显式注解` | read/write/execute操作分类，用于权限与Hook。 |
| `arguments` | `未显式注解` | 外部或模型提交的工具参数，必须经schema检查。 |

**调用表达式（静态提取，不含内层独立函数体）**：`handle['future'].done`、`result.get`、`self.abort`、`self.disconnect`、`self.portal.call`、`self.services.get`、`type`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 123 | `handle` | `self.services.get(name)` | MCP连接句柄，或当前资源引用。 |
| 128 | `result` | `self.portal.call(self._request, handle, operation, arguments)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 133 | `result` | `{'ok': False, 'disconnected': True, 'error': 'MCP 请求失败: ' + type(error).__name__}` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 123 | 函数体 | 将 `self.services.get(name)` 赋给 `handle`。 |
| 124 | 函数体 | 条件 `handle is None or handle['future'].done()`：真时执行body，假时进入else/后续。 |
| 125 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`self.disconnect(name)`。 |
| 126 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': 'MCP 服务未连接，请运行 /mcp refresh'}`，结束当前函数；具体分支见完整源码。 |
| 127 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 128 | 函数体 / try | 将 `self.portal.call(self._request, handle, operation, arguments)` 赋给 `result`。 |
| 129 | 函数体 | except KeyboardInterrupt：只处理匹配类型的异常。 |
| 130 | 函数体 / except KeyboardInterrupt | 计算表达式/调用产生动作：`self.abort(name)`。 |
| 131 | 函数体 / except KeyboardInterrupt | 抛出 `None`。 |
| 132 | 函数体 | except Exception as error：只处理匹配类型的异常。 |
| 133 | 函数体 / except Exception as error | 将 `{'ok': False, 'disconnected': True, 'error': 'MCP 请求失败: ' + type(error).__name__}` 赋给 `result`。 |
| 134 | 函数体 | 条件 `result.get('disconnected')`：真时执行body，假时进入else/后续。 |
| 135 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`self.disconnect(name)`。 |
| 136 | 函数体 | 返回 `result`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L126：`{'ok': False, 'error': 'MCP 服务未连接，请运行 /mcp refresh'}`。
- L136：`result`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="mcpmanager-call-tool"></a>
## MCPManager.call_tool

组装call操作，转共享request。

```python
def call_tool(self, name, tool_name, schema, arguments)
```

位置：[138行](../../../mcp_manager.py#L138) 至快照 139 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| `tool_name` | `未显式注解` | 远端/内置工具标识，用于路由及结果对应。 |
| `schema` | `未显式注解` | 工具参数/输出JSON Schema，用于结构化验证。 |
| `arguments` | `未显式注解` | 外部或模型提交的工具参数，必须经schema检查。 |

**调用表达式（静态提取，不含内层独立函数体）**：`self.request`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 139 | 函数体 | 返回 `self.request(name, 'call', (tool_name, schema, arguments))`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L139：`self.request(name, 'call', (tool_name, schema, arguments))`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="mcpmanager-refresh"></a>
## MCPManager.refresh

断开则重连，否则发现并重新注册。

```python
def refresh(self, name)
```

位置：[141行](../../../mcp_manager.py#L141) 至快照 153 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |

**调用表达式（静态提取，不含内层独立函数体）**：`register_server_tools`、`self.connect`、`self.disconnect`、`self.request`、`self.services[name]['future'].done`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 146 | `result` | `self.request(name, 'refresh')` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 149 | `handle` | `self.services[name]` | MCP连接句柄，或当前资源引用。 |
| 150 | `registered` | `register_server_tools(name, {**result, 'connection': handle['connection']})` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 152 | `handle['tools']` | `result['tools']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 142 | 函数体 | 条件 `name in self.services and self.services[name]['future'].done()`：真时执行body，假时进入else/后续。 |
| 143 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`self.disconnect(name)`。 |
| 144 | 函数体 | 条件 `name not in self.services`：真时执行body，假时进入else/后续。 |
| 145 | 函数体 / 条件为真 | 返回 `self.connect(name)`，结束当前函数；具体分支见完整源码。 |
| 146 | 函数体 | 将 `self.request(name, 'refresh')` 赋给 `result`。 |
| 147 | 函数体 | 条件 `not result['ok']`：真时执行body，假时进入else/后续。 |
| 148 | 函数体 / 条件为真 | 返回 `result`，结束当前函数；具体分支见完整源码。 |
| 149 | 函数体 | 将 `self.services[name]` 赋给 `handle`。 |
| 150 | 函数体 | 将 `register_server_tools(name, {**result, 'connection': handle['connection']})` 赋给 `registered`。 |
| 151 | 函数体 | 条件 `registered['ok']`：真时执行body，假时进入else/后续。 |
| 152 | 函数体 / 条件为真 | 将 `result['tools']` 赋给 `handle['tools']`。 |
| 153 | 函数体 | 返回 `registered`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L145：`self.connect(name)`。
- L148：`result`。
- L153：`registered`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="mcpmanager-disconnect"></a>
## MCPManager.disconnect

注销工具，通知close，等待或取消连接拥有者。

```python
def disconnect(self, name)
```

位置：[155行](../../../mcp_manager.py#L155) 至快照 164 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |

**调用表达式（静态提取，不含内层独立函数体）**：`handle['future'].cancel`、`handle['future'].done`、`handle['future'].result`、`self.portal.call`、`self.services.pop`、`unregister_server_tools`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 156 | `handle` | `self.services.pop(name, None)` | MCP连接句柄，或当前资源引用。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 156 | 函数体 | 将 `self.services.pop(name, None)` 赋给 `handle`。 |
| 157 | 函数体 | 计算表达式/调用产生动作：`unregister_server_tools(name)`。 |
| 158 | 函数体 | 条件 `handle is not None`：真时执行body，假时进入else/后续。 |
| 159 | 函数体 / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 160 | 函数体 / 条件为真 / try | 条件 `not handle['future'].done()`：真时执行body，假时进入else/后续。 |
| 161 | 函数体 / 条件为真 / try / 条件为真 | 计算表达式/调用产生动作：`self.portal.call(self._request, handle, 'close', ())`。 |
| 162 | 函数体 / 条件为真 / try | 计算表达式/调用产生动作：`handle['future'].result(timeout=5)`。 |
| 163 | 函数体 / 条件为真 | except Exception：只处理匹配类型的异常。 |
| 164 | 函数体 / 条件为真 / except Exception | 计算表达式/调用产生动作：`handle['future'].cancel()`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="mcpmanager--wait-closed"></a>
## MCPManager._wait_closed

等待异步退出事件，最多5秒。

```python
async def _wait_closed(self, event)
```

位置：[166行](../../../mcp_manager.py#L166) 至快照 168 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `event` | `未显式注解` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |

**调用表达式（静态提取，不含内层独立函数体）**：`asyncio.timeout`、`event.wait`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 167 | 函数体 | 进入资源/状态范围：`asyncio.timeout(5)`；退出执行清理。 |
| 168 | 函数体 / with范围 | 计算表达式/调用产生动作：`await event.wait()`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="mcpmanager-abort"></a>
## MCPManager.abort

取消拥有者而非排队close，注销并等清理。

```python
def abort(self, name)
```

位置：[170行](../../../mcp_manager.py#L170) 至快照 179 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |

**调用表达式（静态提取，不含内层独立函数体）**：`handle['future'].cancel`、`self.portal.call`、`self.services.pop`、`unregister_server_tools`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 172 | `handle` | `self.services.pop(name, None)` | MCP连接句柄，或当前资源引用。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 171 | 函数体 | 文档字符串：说明职责，不作为普通语句动作执行。 |
| 172 | 函数体 | 将 `self.services.pop(name, None)` 赋给 `handle`。 |
| 173 | 函数体 | 计算表达式/调用产生动作：`unregister_server_tools(name)`。 |
| 174 | 函数体 | 条件 `handle is not None`：真时执行body，假时进入else/后续。 |
| 175 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`handle['future'].cancel()`。 |
| 176 | 函数体 / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 177 | 函数体 / 条件为真 / try | 计算表达式/调用产生动作：`self.portal.call(self._wait_closed, handle['closed'])`。 |
| 178 | 函数体 / 条件为真 | except Exception：只处理匹配类型的异常。 |
| 179 | 函数体 / 条件为真 / except Exception | pass占位，无动作。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="mcpmanager-tool-names"></a>
## MCPManager.tool_names

从注册表列出当前MCP名称。

```python
def tool_names(self)
```

位置：[181行](../../../mcp_manager.py#L181) 至快照 183 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：`TOOL_REGISTRY.items`、`spec.get`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 182 | 函数体 | 在此处导入依赖：`from tool_registry import TOOL_REGISTRY`；局部导入可延迟加载或避免循环。 |
| 183 | 函数体 | 返回 `[name for name, spec in TOOL_REGISTRY.items() if spec.get('kind') == 'mcp']`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L183：`[name for name, spec in TOOL_REGISTRY.items() if spec.get('kind') == 'mcp']`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- class：对象状态与方法/继承：L17。
- async/await：异步等待与资源范围：L35, L38, L42, L45, L46, L50, L51, L52, L60, L65, L67, L69, L80, L82, L84, L166, L167, L168。
- try/except/finally：异常与保证清理：L28, L37, L64, L103, L127, L159, L176。
- 推导式/生成器表达式：循环建容器或逐个产生：L120, L183。
- 星号展开：展开已有容器：L69。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """CLI 运行期间持有 MCP 连接；同步主循环通过 portal 请求异步操作。"""
0002 | import asyncio
0003 | from datetime import timedelta
0004 | 
0005 | from anyio import TASK_STATUS_IGNORED
0006 | from anyio.from_thread import start_blocking_portal
0007 | from mcp import ClientSession
0008 | from mcp.client.stdio import stdio_client
0009 | 
0010 | from audit import record_tool_event
0011 | from config import mcp_config
0012 | from mcp_client import call_session_tool, collect_tools, prepare_server_connection
0013 | from mcp_tools import register_server_tools, unregister_server_tools
0014 | from permissions import authorize_external_tool
0015 | 
0016 | 
0017 | class MCPManager:
0018 |     def __init__(self):
0019 |         self.services = {}
0020 |         self.portal = None
0021 | 
0022 |     def __enter__(self):
0023 |         self.portal_context = start_blocking_portal()
0024 |         self.portal = self.portal_context.__enter__()
0025 |         return self
0026 | 
0027 |     def __exit__(self, exc_type, exc_value, traceback):
0028 |         try:
0029 |             for name in list(self.services):
0030 |                 self.disconnect(name)
0031 |         finally:
0032 |             self.portal_context.__exit__(exc_type, exc_value, traceback)
0033 |             self.portal = None
0034 | 
0035 |     async def _serve(self, connection, *, task_status=TASK_STATUS_IGNORED):
0036 |         closed = asyncio.Event()
0037 |         try:
0038 |             await self._serve_connected(connection, closed, task_status=task_status)
0039 |         finally:
0040 |             closed.set()
0041 | 
0042 |     async def _serve_connected(self, connection, closed, *, task_status=TASK_STATUS_IGNORED):
0043 |         # 由同一个异步任务进入、持有并退出 SDK 上下文，避免跨任务清理错误。
0044 |         queue = asyncio.Queue()
0045 |         async with stdio_client(connection["parameters"]) as (read_stream, write_stream):
0046 |             async with ClientSession(
0047 |                 read_stream, write_stream,
0048 |                 read_timeout_seconds=timedelta(seconds=connection["timeout"])
0049 |             ) as session:
0050 |                 async with asyncio.timeout(connection["timeout"]):
0051 |                     initialized = await session.initialize()
0052 |                     tools = await collect_tools(session)
0053 |                 task_status.started({
0054 |                     "queue": queue,
0055 |                     "closed": closed,
0056 |                     "server": initialized.serverInfo.model_dump(mode="json"),
0057 |                     "tools": tools
0058 |                 })
0059 |                 while True:
0060 |                     operation, arguments, response = await queue.get()
0061 |                     if operation == "close":
0062 |                         response.set_result({"ok": True})
0063 |                         return
0064 |                     try:
0065 |                         async with asyncio.timeout(connection["timeout"]):
0066 |                             if operation == "refresh":
0067 |                                 result = {"ok": True, "tools": await collect_tools(session)}
0068 |                             else:
0069 |                                 result = await call_session_tool(session, *arguments)
0070 |                         if not response.done():
0071 |                             response.set_result(result)
0072 |                     except Exception as error:
0073 |                         if not response.done():
0074 |                             response.set_result({
0075 |                                 "ok": False, "disconnected": True,
0076 |                                 "error": "MCP 通信失败: " + type(error).__name__
0077 |                             })
0078 |                         return
0079 | 
0080 |     async def _request(self, handle, operation, arguments):
0081 |         response = asyncio.get_running_loop().create_future()
0082 |         await handle["queue"].put((operation, arguments, response))
0083 |         stopped = asyncio.wrap_future(handle["future"])
0084 |         done, pending = await asyncio.wait(
0085 |             [response, stopped], timeout=handle["connection"]["timeout"] + 3,
0086 |             return_when=asyncio.FIRST_COMPLETED
0087 |         )
0088 |         if response in done:
0089 |             return response.result()
0090 |         response.cancel()
0091 |         raise ConnectionError("MCP 服务已停止或请求超时")
0092 | 
0093 |     def connect(self, name):
0094 |         if name in self.services:
0095 |             return {"ok": True, "message": "MCP 服务已经连接"}
0096 |         connection = prepare_server_connection(name)
0097 |         if not connection["ok"]:
0098 |             return connection
0099 |         authorized = authorize_external_tool("mcp_connect", name, "user", connection["details"])
0100 |         if not authorized["ok"]:
0101 |             record_tool_event("mcp_connect", authorized)
0102 |             return authorized
0103 |         try:
0104 |             future, started = self.portal.start_task(self._serve, connection)
0105 |             connection["manager"] = self
0106 |             connection["server_name"] = name
0107 |             self.services[name] = {
0108 |                 **started, "future": future, "connection": connection
0109 |             }
0110 |             result = register_server_tools(name, {**started, "connection": connection})
0111 |             if not result["ok"]:
0112 |                 self.disconnect(name)
0113 |         except Exception as error:
0114 |             result = {"ok": False, "error": "MCP 启动失败: " + type(error).__name__}
0115 |         result = {**result, "approval": authorized.get("approval", [])}
0116 |         record_tool_event("mcp_connect", result)
0117 |         return result
0118 | 
0119 |     def load_configured(self):
0120 |         return {name: self.connect(name) for name in mcp_config}
0121 | 
0122 |     def request(self, name, operation, arguments=()):
0123 |         handle = self.services.get(name)
0124 |         if handle is None or handle["future"].done():
0125 |             self.disconnect(name)
0126 |             return {"ok": False, "error": "MCP 服务未连接，请运行 /mcp refresh"}
0127 |         try:
0128 |             result = self.portal.call(self._request, handle, operation, arguments)
0129 |         except KeyboardInterrupt:
0130 |             self.abort(name)
0131 |             raise
0132 |         except Exception as error:
0133 |             result = {"ok": False, "disconnected": True, "error": "MCP 请求失败: " + type(error).__name__}
0134 |         if result.get("disconnected"):
0135 |             self.disconnect(name)
0136 |         return result
0137 | 
0138 |     def call_tool(self, name, tool_name, schema, arguments):
0139 |         return self.request(name, "call", (tool_name, schema, arguments))
0140 | 
0141 |     def refresh(self, name):
0142 |         if name in self.services and self.services[name]["future"].done():
0143 |             self.disconnect(name)
0144 |         if name not in self.services:
0145 |             return self.connect(name)
0146 |         result = self.request(name, "refresh")
0147 |         if not result["ok"]:
0148 |             return result
0149 |         handle = self.services[name]
0150 |         registered = register_server_tools(name, {**result, "connection": handle["connection"]})
0151 |         if registered["ok"]:
0152 |             handle["tools"] = result["tools"]
0153 |         return registered
0154 | 
0155 |     def disconnect(self, name):
0156 |         handle = self.services.pop(name, None)
0157 |         unregister_server_tools(name)
0158 |         if handle is not None:
0159 |             try:
0160 |                 if not handle["future"].done():
0161 |                     self.portal.call(self._request, handle, "close", ())
0162 |                 handle["future"].result(timeout=5)
0163 |             except Exception:
0164 |                 handle["future"].cancel()
0165 | 
0166 |     async def _wait_closed(self, event):
0167 |         async with asyncio.timeout(5):
0168 |             await event.wait()
0169 | 
0170 |     def abort(self, name):
0171 |         """取消连接拥有者任务，让 stdio 上下文关闭服务；不等待排队的 close。"""
0172 |         handle = self.services.pop(name, None)
0173 |         unregister_server_tools(name)
0174 |         if handle is not None:
0175 |             handle['future'].cancel()
0176 |             try:
0177 |                 self.portal.call(self._wait_closed, handle['closed'])
0178 |             except Exception:
0179 |                 pass
0180 | 
0181 |     def tool_names(self):
0182 |         from tool_registry import TOOL_REGISTRY
0183 |         return [name for name, spec in TOOL_REGISTRY.items() if spec.get("kind") == "mcp"]
```
