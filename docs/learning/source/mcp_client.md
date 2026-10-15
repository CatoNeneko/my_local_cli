# mcp_client.py：源码导读

MCP配置、初始化后的分页发现、真实协议调用及结果规格。

先读专题：[05-extensions.md](../05-extensions.md)。

实际源码：[mcp_client.py](../../../mcp_client.py)。

快照 SHA256：`f5548b476af9c37ad3ec295874b9d412c429c3cddccabf15bb02cc356eebc71b`；91 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import shlex` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `from mcp import StdioServerParameters` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `from config import mcp_config` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 9 | `from workspace import APP_ROOT as PROJECT_ROOT` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [prepare_server_connection](#prepare-server-connection) | [12](../../../mcp_client.py#L12) | 验证固定MCP配置，构造最小环境、解释器、args/cwd/超时。 |
| [collect_tools](#collect-tools) | [49](../../../mcp_client.py#L49) | 分页发现工具，限制总量并拒绝游标循环。 |
| [call_session_tool](#call-session-tool) | [67](../../../mcp_client.py#L67) | 重查声明后调用，收文字和结构化JSON，限制大小。 |
| [execute_prepared_mcp_tool](#execute-prepared-mcp-tool) | [87](../../../mcp_client.py#L87) | 通过绑定的manager路由执行协议调用。 |

<a id="prepare-server-connection"></a>
## prepare_server_connection

验证固定MCP配置，构造最小环境、解释器、args/cwd/超时。

```python
def prepare_server_connection(server_name)
```

位置：[12行](../../../mcp_client.py#L12) 至快照 46 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `server_name` | `未显式注解` | 可信MCP配置中的服务名，决定启动哪一项。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`StdioServerParameters`、`all`、`executable.is_absolute`、`executable.is_file`、`executable.resolve`、`isinstance`、`list`、`mcp_config.get`、`shlex.join`、`specification.get`、`str`、`type`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 13 | `specification` | `mcp_config.get(server_name)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 16 | `command` | `specification.get('command')` | 安全构造的argv列表或解析出的命令名，避免将它们混为shell字符串。 |
| 17 | `args` | `specification.get('args')` | 解析启动参数Namespace或工具参数字典，按来源区分。 |
| 18 | `timeout` | `specification.get('timeout_seconds')` | 操作/任务超时秒数。 |
| 25 | `executable` | `Path(command)` | 已解析存在的MCP解释器/可执行程序路径。 |
| 27 | `executable` | `PROJECT_ROOT / executable` | 已解析存在的MCP解释器/可执行程序路径。 |
| 28 | `executable` | `executable.resolve()` | 已解析存在的MCP解释器/可执行程序路径。 |
| 31 | `details` | `shlex.join([str(executable), *args])` | 用户确认/审批展示的动作说明。 |
| 34 | `environment` | `{'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'}` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 37 | `root` | `permissions.PROJECT_ROOT` | 本次目录扫描/工作项目根。 |
| 38 | `state` | `root if root == PROJECT_ROOT else root / '.ai-cli'` | 状态目录/有效摘要状态，当前表达式决定。 |
| 39 | `environment['PLAYWRIGHT_BROWSERS_PATH']` | `str(PROJECT_ROOT / '.browser-runtime')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 40 | `environment['AI_CLI_BROWSER_ARTIFACTS']` | `str(state / '.browser-artifacts')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 42 | `parameters` | `StdioServerParameters(command=str(executable), args=list(args), cwd=str(PROJECT_ROOT), env=environment)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 13 | 函数体 | 将 `mcp_config.get(server_name)` 赋给 `specification`。 |
| 14 | 函数体 | 条件 `not isinstance(specification, dict)`：真时执行body，假时进入else/后续。 |
| 15 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '未知 MCP 服务: ' + str(server_name)}`，结束当前函数；具体分支见完整源码。 |
| 16 | 函数体 | 将 `specification.get('command')` 赋给 `command`。 |
| 17 | 函数体 | 将 `specification.get('args')` 赋给 `args`。 |
| 18 | 函数体 | 将 `specification.get('timeout_seconds')` 赋给 `timeout`。 |
| 19 | 函数体 | 条件 `not isinstance(command, str) or not command or '\x00' in command`：真时执行body，假时进入else/后续。 |
| 20 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': 'MCP 启动命令无效'}`，结束当前函数；具体分支见完整源码。 |
| 21 | 函数体 | 条件 `not isinstance(args, list) or not all((isinstance(arg, str) and '\x00' not in arg for arg in args))`：真时执行body，假时进入else/后续。 |
| 22 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': 'MCP args 必须是字符串列表'}`，结束当前函数；具体分支见完整源码。 |
| 23 | 函数体 | 条件 `type(timeout) is not int or not 1 <= timeout <= 60`：真时执行body，假时进入else/后续。 |
| 24 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': 'MCP 超时必须是 1～60 秒的整数'}`，结束当前函数；具体分支见完整源码。 |
| 25 | 函数体 | 将 `Path(command)` 赋给 `executable`。 |
| 26 | 函数体 | 条件 `not executable.is_absolute()`：真时执行body，假时进入else/后续。 |
| 27 | 函数体 / 条件为真 | 将 `PROJECT_ROOT / executable` 赋给 `executable`。 |
| 28 | 函数体 | 将 `executable.resolve()` 赋给 `executable`。 |
| 29 | 函数体 | 条件 `not executable.is_file()`：真时执行body，假时进入else/后续。 |
| 30 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '找不到 MCP 服务的启动程序'}`，结束当前函数；具体分支见完整源码。 |
| 31 | 函数体 | 将 `shlex.join([str(executable), *args])` 赋给 `details`。 |
| 32 | 函数体 | 更新已有变量：`details += '\n工作目录: ' + str(PROJECT_ROOT)`。 |
| 33 | 函数体 | 更新已有变量：`details += '\n该服务以当前用户权限运行，尚未接入沙箱。'`。 |
| 34 | 函数体 | 将 `{'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'}` 赋给 `environment`。 |
| 35 | 函数体 | 条件 `server_name == 'browser'`：真时执行body，假时进入else/后续。 |
| 36 | 函数体 / 条件为真 | 在此处导入依赖：`import permissions`；局部导入可延迟加载或避免循环。 |
| 37 | 函数体 / 条件为真 | 将 `permissions.PROJECT_ROOT` 赋给 `root`。 |
| 38 | 函数体 / 条件为真 | 将 `root if root == PROJECT_ROOT else root / '.ai-cli'` 赋给 `state`。 |
| 39 | 函数体 / 条件为真 | 将 `str(PROJECT_ROOT / '.browser-runtime')` 赋给 `environment['PLAYWRIGHT_BROWSERS_PATH']`。 |
| 40 | 函数体 / 条件为真 | 将 `str(state / '.browser-artifacts')` 赋给 `environment['AI_CLI_BROWSER_ARTIFACTS']`。 |
| 41 | 函数体 / 条件为真 | 更新已有变量：`details += '\n浏览器可访问网络；临时 Cookie，不加载用户浏览器档案；截图保存于私有目录。'`。 |
| 42 | 函数体 | 将 `StdioServerParameters(command=str(executable), args=list(args), cwd=str(PROJECT_ROOT), env=environment)` 赋给 `parameters`。 |
| 46 | 函数体 | 返回 `{'ok': True, 'parameters': parameters, 'timeout': timeout, 'details': details}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L15：`{'ok': False, 'error': '未知 MCP 服务: ' + str(server_name)}`。
- L20：`{'ok': False, 'error': 'MCP 启动命令无效'}`。
- L22：`{'ok': False, 'error': 'MCP args 必须是字符串列表'}`。
- L24：`{'ok': False, 'error': 'MCP 超时必须是 1～60 秒的整数'}`。
- L30：`{'ok': False, 'error': '找不到 MCP 服务的启动程序'}`。
- L46：`{'ok': True, 'parameters': parameters, 'timeout': timeout, 'details': details}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="collect-tools"></a>
## collect_tools

分页发现工具，限制总量并拒绝游标循环。

```python
async def collect_tools(session)
```

位置：[49行](../../../mcp_client.py#L49) 至快照 64 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `session` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ValueError`、`len`、`seen_cursors.add`、`session.list_tools`、`set`、`tool.model_dump`、`tools.extend`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 50 | `tools` | `[]` | 发给模型的工具声明列表，不含handler函数对象。 |
| 51 | `cursor` | `None` | 分页/模糊查找位置，具体按调用来源判断。 |
| 52 | `seen_cursors` | `set()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 54 | `page` | `await session.list_tools(cursor=cursor)` | Playwright单页面对象，具体DOM操作由它执行。 |
| 58 | `cursor` | `page.nextCursor` | 分页/模糊查找位置，具体按调用来源判断。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 50 | 函数体 | 将 `[]` 赋给 `tools`。 |
| 51 | 函数体 | 将 `None` 赋给 `cursor`。 |
| 52 | 函数体 | 将 `set()` 赋给 `seen_cursors`。 |
| 53 | 函数体 | 循环检查 `True`，break/return/异常可结束。 |
| 54 | 函数体 / 循环每次 | 将 `await session.list_tools(cursor=cursor)` 赋给 `page`。 |
| 55 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`tools.extend((tool.model_dump(mode='json') for tool in page.tools))`。 |
| 56 | 函数体 / 循环每次 | 条件 `len(tools) > 200`：真时执行body，假时进入else/后续。 |
| 57 | 函数体 / 循环每次 / 条件为真 | 抛出 `ValueError('MCP 工具数量超过本阶段的 200 个上限')`。 |
| 58 | 函数体 / 循环每次 | 将 `page.nextCursor` 赋给 `cursor`。 |
| 59 | 函数体 / 循环每次 | 条件 `not cursor`：真时执行body，假时进入else/后续。 |
| 60 | 函数体 / 循环每次 / 条件为真 | break结束最近一层循环。 |
| 61 | 函数体 / 循环每次 | 条件 `cursor in seen_cursors`：真时执行body，假时进入else/后续。 |
| 62 | 函数体 / 循环每次 / 条件为真 | 抛出 `ValueError('MCP 工具列表分页游标重复')`。 |
| 63 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`seen_cursors.add(cursor)`。 |
| 64 | 函数体 | 返回 `tools`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L64：`tools`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="call-session-tool"></a>
## call_session_tool

重查声明后调用，收文字和结构化JSON，限制大小。

```python
async def call_session_tool(session, tool_name, expected_schema, arguments)
```

位置：[67行](../../../mcp_client.py#L67) 至快照 84 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `session` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `tool_name` | `未显式注解` | 远端/内置工具标识，用于路由及结果对应。 |
| `expected_schema` | `未显式注解` | 调用前登记的schema快照，真实发现变化则拒绝。 |
| `arguments` | `未显式注解` | 外部或模型提交的工具参数，必须经schema检查。 |

**调用表达式（静态提取，不含内层独立函数体）**：`any`、`collect_tools`、`json.dumps`、`len`、`session.call_tool`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 68 | `tools` | `await collect_tools(session)` | 发给模型的工具声明列表，不含handler函数对象。 |
| 69 | `matches` | `[tool for tool in tools if tool['name'] == tool_name]` | 文字搜索实际匹配记录列表；空列表表示无匹配。 |
| 72 | `result` | `await session.call_tool(tool_name, arguments=arguments)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 75 | `normalized` | `{'ok': not result.isError, 'content': [item.text for item in result.content], 'structured_content': result.structuredContent}` | 默认值合并并经schema验证后的参数/规范结果。 |
| 81 | `normalized['error']` | `'MCP 服务报告工具执行失败'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 68 | 函数体 | 将 `await collect_tools(session)` 赋给 `tools`。 |
| 69 | 函数体 | 将 `[tool for tool in tools if tool['name'] == tool_name]` 赋给 `matches`。 |
| 70 | 函数体 | 条件 `len(matches) != 1 or matches[0]['inputSchema'] != expected_schema`：真时执行body，假时进入else/后续。 |
| 71 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': 'MCP 工具声明已变化，请运行 /mcp refresh'}`，结束当前函数；具体分支见完整源码。 |
| 72 | 函数体 | 将 `await session.call_tool(tool_name, arguments=arguments)` 赋给 `result`。 |
| 73 | 函数体 | 条件 `any((item.type != 'text' for item in result.content))`：真时执行body，假时进入else/后续。 |
| 74 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '本阶段 MCP 只支持文字和结构化 JSON 结果'}`，结束当前函数；具体分支见完整源码。 |
| 75 | 函数体 | 将 `{'ok': not result.isError, 'content': [item.text for item in result.content], 'structured_content': result.structuredContent}` 赋给 `normalized`。 |
| 80 | 函数体 | 条件 `result.isError`：真时执行body，假时进入else/后续。 |
| 81 | 函数体 / 条件为真 | 将 `'MCP 服务报告工具执行失败'` 赋给 `normalized['error']`。 |
| 82 | 函数体 | 条件 `len(json.dumps(normalized, ensure_ascii=False)) > 16000`：真时执行body，假时进入else/后续。 |
| 83 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': 'MCP 返回内容超过 16000 字符上限'}`，结束当前函数；具体分支见完整源码。 |
| 84 | 函数体 | 返回 `normalized`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L71：`{'ok': False, 'error': 'MCP 工具声明已变化，请运行 /mcp refresh'}`。
- L74：`{'ok': False, 'error': '本阶段 MCP 只支持文字和结构化 JSON 结果'}`。
- L83：`{'ok': False, 'error': 'MCP 返回内容超过 16000 字符上限'}`。
- L84：`normalized`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="execute-prepared-mcp-tool"></a>
## execute_prepared_mcp_tool

通过绑定的manager路由执行协议调用。

```python
def execute_prepared_mcp_tool(connection, tool_name, expected_schema, arguments)
```

位置：[87行](../../../mcp_client.py#L87) 至快照 91 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `connection` | `未显式注解` | 固定MCP启动参数与路由信息。 |
| `tool_name` | `未显式注解` | 远端/内置工具标识，用于路由及结果对应。 |
| `expected_schema` | `未显式注解` | 调用前登记的schema快照，真实发现变化则拒绝。 |
| `arguments` | `未显式注解` | 外部或模型提交的工具参数，必须经schema检查。 |

**调用表达式（静态提取，不含内层独立函数体）**：`connection['manager'].call_tool`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 88 | 函数体 | 文档字符串：说明职责，不作为普通语句动作执行。 |
| 89 | 函数体 | 返回 `connection['manager'].call_tool(connection['server_name'], tool_name, expected_schema, arguments)`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L89：`connection['manager'].call_tool(connection['server_name'], tool_name, expected_schema, arguments)`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- async/await：异步等待与资源范围：L49, L54, L67, L68, L72。
- 推导式/生成器表达式：循环建容器或逐个产生：L21, L55, L69, L73, L77。
- 星号展开：展开已有容器：L31。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """MCP 协议操作：连接参数、握手、发现工具和执行调用。"""
0002 | import json
0003 | import shlex
0004 | from pathlib import Path
0005 | 
0006 | from mcp import StdioServerParameters
0007 | 
0008 | from config import mcp_config
0009 | from workspace import APP_ROOT as PROJECT_ROOT
0010 | 
0011 | 
0012 | def prepare_server_connection(server_name):
0013 |     specification = mcp_config.get(server_name)
0014 |     if not isinstance(specification, dict):
0015 |         return {"ok": False, "error": "未知 MCP 服务: " + str(server_name)}
0016 |     command = specification.get("command")
0017 |     args = specification.get("args")
0018 |     timeout = specification.get("timeout_seconds")
0019 |     if not isinstance(command, str) or not command or "\x00" in command:
0020 |         return {"ok": False, "error": "MCP 启动命令无效"}
0021 |     if not isinstance(args, list) or not all(isinstance(arg, str) and "\x00" not in arg for arg in args):
0022 |         return {"ok": False, "error": "MCP args 必须是字符串列表"}
0023 |     if type(timeout) is not int or not 1 <= timeout <= 60:
0024 |         return {"ok": False, "error": "MCP 超时必须是 1～60 秒的整数"}
0025 |     executable = Path(command)
0026 |     if not executable.is_absolute():
0027 |         executable = PROJECT_ROOT / executable
0028 |     executable = executable.resolve()
0029 |     if not executable.is_file():
0030 |         return {"ok": False, "error": "找不到 MCP 服务的启动程序"}
0031 |     details = shlex.join([str(executable), *args])
0032 |     details += "\n工作目录: " + str(PROJECT_ROOT)
0033 |     details += "\n该服务以当前用户权限运行，尚未接入沙箱。"
0034 |     environment = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
0035 |     if server_name == 'browser':
0036 |         import permissions
0037 |         root = permissions.PROJECT_ROOT
0038 |         state = root if root == PROJECT_ROOT else root / '.ai-cli'
0039 |         environment['PLAYWRIGHT_BROWSERS_PATH'] = str(PROJECT_ROOT / '.browser-runtime')
0040 |         environment['AI_CLI_BROWSER_ARTIFACTS'] = str(state / '.browser-artifacts')
0041 |         details += '\n浏览器可访问网络；临时 Cookie，不加载用户浏览器档案；截图保存于私有目录。'
0042 |     parameters = StdioServerParameters(
0043 |         command=str(executable), args=list(args), cwd=str(PROJECT_ROOT),
0044 |         env=environment
0045 |     )
0046 |     return {"ok": True, "parameters": parameters, "timeout": timeout, "details": details}
0047 | 
0048 | 
0049 | async def collect_tools(session):
0050 |     tools = []
0051 |     cursor = None
0052 |     seen_cursors = set()
0053 |     while True:
0054 |         page = await session.list_tools(cursor=cursor)
0055 |         tools.extend(tool.model_dump(mode="json") for tool in page.tools)
0056 |         if len(tools) > 200:
0057 |             raise ValueError("MCP 工具数量超过本阶段的 200 个上限")
0058 |         cursor = page.nextCursor
0059 |         if not cursor:
0060 |             break
0061 |         if cursor in seen_cursors:
0062 |             raise ValueError("MCP 工具列表分页游标重复")
0063 |         seen_cursors.add(cursor)
0064 |     return tools
0065 | 
0066 | 
0067 | async def call_session_tool(session, tool_name, expected_schema, arguments):
0068 |     tools = await collect_tools(session)
0069 |     matches = [tool for tool in tools if tool["name"] == tool_name]
0070 |     if len(matches) != 1 or matches[0]["inputSchema"] != expected_schema:
0071 |         return {"ok": False, "error": "MCP 工具声明已变化，请运行 /mcp refresh"}
0072 |     result = await session.call_tool(tool_name, arguments=arguments)
0073 |     if any(item.type != "text" for item in result.content):
0074 |         return {"ok": False, "error": "本阶段 MCP 只支持文字和结构化 JSON 结果"}
0075 |     normalized = {
0076 |         "ok": not result.isError,
0077 |         "content": [item.text for item in result.content],
0078 |         "structured_content": result.structuredContent
0079 |     }
0080 |     if result.isError:
0081 |         normalized["error"] = "MCP 服务报告工具执行失败"
0082 |     if len(json.dumps(normalized, ensure_ascii=False)) > 16000:
0083 |         return {"ok": False, "error": "MCP 返回内容超过 16000 字符上限"}
0084 |     return normalized
0085 | 
0086 | 
0087 | def execute_prepared_mcp_tool(connection, tool_name, expected_schema, arguments):
0088 |     """内部执行函数：仅在 tool_runtime 完成授权后调用。"""
0089 |     return connection["manager"].call_tool(
0090 |         connection["server_name"], tool_name, expected_schema, arguments
0091 |     )
```
