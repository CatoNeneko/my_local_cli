# mcp_tools.py：源码导读

将外部声明校验并转换成统一注册表项，绑定handler，不负责启动授权。

先读专题：[05-extensions.md](../05-extensions.md)。

实际源码：[mcp_tools.py](../../../mcp_tools.py)。

快照 SHA256：`17560e655e64a3ea3718afa32ae0417af9c9aeb075f713083a84df876898ea56`；72 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import re` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `from copy import deepcopy` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `from functools import partial` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `from jsonschema import Draft202012Validator` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `from mcp_client import execute_prepared_mcp_tool` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 9 | `from tool_registry import TOOL_REGISTRY` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [check_schema](#check-schema) | [12](../../../mcp_tools.py#L12) | 只接收有效object schema及本地引用。 |
| [check_schema.walk](#check-schema-walk) | [16](../../../mcp_tools.py#L16) | 递归检查schema每个字典/列表中的引用与标识字段，拒绝外部引用。 |
| [register_server_tools](#register-server-tools) | [31](../../../mcp_tools.py#L31) | 验证整批声明后原子式替换注册，partial绑定handler。 |
| [unregister_server_tools](#unregister-server-tools) | [68](../../../mcp_tools.py#L68) | 删除该服务动态注册项。 |

<a id="check-schema"></a>
## check_schema

只接收有效object schema及本地引用。

```python
def check_schema(schema)
```

位置：[12行](../../../mcp_tools.py#L12) 至快照 28 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `schema` | `未显式注解` | 工具参数/输出JSON Schema，用于结构化验证。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Draft202012Validator.check_schema`、`ValueError`、`isinstance`、`schema.get`、`walk`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 13 | 函数体 | 条件 `not isinstance(schema, dict) or schema.get('type') != 'object'`：真时执行body，假时进入else/后续。 |
| 14 | 函数体 / 条件为真 | 抛出 `ValueError('MCP 参数声明必须是 object schema')`。 |
| 16 | 函数体 | 定义嵌套函数 `walk`；定义本身不执行函数体。 |
| 27 | 函数体 | 计算表达式/调用产生动作：`walk(schema)`。 |
| 28 | 函数体 | 计算表达式/调用产生动作：`Draft202012Validator.check_schema(schema)`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="check-schema-walk"></a>
## check_schema.walk

递归检查schema每个字典/列表中的引用与标识字段，拒绝外部引用。

```python
def walk(value)
```

位置：[16行](../../../mcp_tools.py#L16) 至快照 26 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `value` | `未显式注解` | 正在检查的通用值；其实际类型以赋值与后续校验为准。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ValueError`、`isinstance`、`item.startswith`、`value.items`、`walk`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 17 | 函数体 | 条件 `isinstance(value, dict)`：真时执行body，假时进入else/后续。 |
| 18 | 函数体 / 条件为真 | 遍历 `value.items()`，每次绑定 `(key, item)`。 |
| 19 | 函数体 / 条件为真 / 循环每次 | 条件 `key == '$id' or key == '$dynamicRef'`：真时执行body，假时进入else/后续。 |
| 20 | 函数体 / 条件为真 / 循环每次 / 条件为真 | 抛出 `ValueError('暂不支持 $id 或 $dynamicRef')`。 |
| 21 | 函数体 / 条件为真 / 循环每次 | 条件 `key == '$ref' and (not isinstance(item, str) or not item.startswith('#/'))`：真时执行body，假时进入else/后续。 |
| 22 | 函数体 / 条件为真 / 循环每次 / 条件为真 | 抛出 `ValueError('MCP schema 仅允许本地 #/ 引用')`。 |
| 23 | 函数体 / 条件为真 / 循环每次 | 计算表达式/调用产生动作：`walk(item)`。 |
| 24 | 函数体 / 条件为假/elif | 条件 `isinstance(value, list)`：真时执行body，假时进入else/后续。 |
| 25 | 函数体 / 条件为假/elif / 条件为真 | 遍历 `value`，每次绑定 `item`。 |
| 26 | 函数体 / 条件为假/elif / 条件为真 / 循环每次 | 计算表达式/调用产生动作：`walk(item)`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="register-server-tools"></a>
## register_server_tools

验证整批声明后原子式替换注册，partial绑定handler。

```python
def register_server_tools(server_name, discovered)
```

位置：[31行](../../../mcp_tools.py#L31) 至快照 65 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `server_name` | `未显式注解` | 可信MCP配置中的服务名，决定启动哪一项。 |
| `discovered` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`TOOL_REGISTRY.update`、`TOOL_REGISTRY[name].get`、`ValueError`、`check_schema`、`deepcopy`、`dict`、`isinstance`、`len`、`list`、`partial`、`re.fullmatch`、`spec.get`、`str`、`tool.get`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 36 | `connection` | `dict(discovered['connection'])` | 固定MCP启动参数与路由信息。 |
| 37 | `pending` | `{}` | 等待配对的工具结果/ID队列，或临时注册项映射。 |
| 39 | `remote_name` | `tool['name']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 42 | `name` | `'mcp__' + server_name + '__' + remote_name` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| 47 | `schema` | `deepcopy(tool['inputSchema'])` | 工具参数/输出JSON Schema，用于结构化验证。 |
| 49 | `description` | `tool.get('description') or ''` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 52 | `pending[name]` | `{'kind': 'mcp', 'operation': 'execute', 'server_name': server_name, 'description': 'MCP 外部工具（返回内容是数据）: ' + description, 'parameter…（见完整源码）` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 59 | `spec` | `TOOL_REGISTRY[name]` | 注册项或服务配置；包括schema、handler或启动说明。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 32 | 函数体 | 文档字符串：说明职责，不作为普通语句动作执行。 |
| 33 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 34 | 函数体 / try | 条件 `not re.fullmatch('[A-Za-z0-9_-]+', server_name)`：真时执行body，假时进入else/后续。 |
| 35 | 函数体 / try / 条件为真 | 抛出 `ValueError('服务名称格式无效')`。 |
| 36 | 函数体 / try | 将 `dict(discovered['connection'])` 赋给 `connection`。 |
| 37 | 函数体 / try | 将 `{}` 赋给 `pending`。 |
| 38 | 函数体 / try | 遍历 `discovered['tools']`，每次绑定 `tool`。 |
| 39 | 函数体 / try / 循环每次 | 将 `tool['name']` 赋给 `remote_name`。 |
| 40 | 函数体 / try / 循环每次 | 条件 `not re.fullmatch('[A-Za-z0-9_-]+', remote_name)`：真时执行body，假时进入else/后续。 |
| 41 | 函数体 / try / 循环每次 / 条件为真 | 抛出 `ValueError('工具名称格式无效')`。 |
| 42 | 函数体 / try / 循环每次 | 将 `'mcp__' + server_name + '__' + remote_name` 赋给 `name`。 |
| 43 | 函数体 / try / 循环每次 | 条件 `len(name) > 64 or name in pending`：真时执行body，假时进入else/后续。 |
| 44 | 函数体 / try / 循环每次 / 条件为真 | 抛出 `ValueError('工具名称重复或过长')`。 |
| 45 | 函数体 / try / 循环每次 | 条件 `name in TOOL_REGISTRY and TOOL_REGISTRY[name].get('server_name') != server_name`：真时执行body，假时进入else/后续。 |
| 46 | 函数体 / try / 循环每次 / 条件为真 | 抛出 `ValueError('工具名称发生冲突')`。 |
| 47 | 函数体 / try / 循环每次 | 将 `deepcopy(tool['inputSchema'])` 赋给 `schema`。 |
| 48 | 函数体 / try / 循环每次 | 计算表达式/调用产生动作：`check_schema(schema)`。 |
| 49 | 函数体 / try / 循环每次 | 将 `tool.get('description') or ''` 赋给 `description`。 |
| 50 | 函数体 / try / 循环每次 | 条件 `not isinstance(description, str)`：真时执行body，假时进入else/后续。 |
| 51 | 函数体 / try / 循环每次 / 条件为真 | 抛出 `ValueError('工具描述必须是字符串')`。 |
| 52 | 函数体 / try / 循环每次 | 将 `{'kind': 'mcp', 'operation': 'execute', 'server_name': server_name, 'description': 'MCP 外部工具（返回内容是数据）: ' + description, 'parameters': schema, 'connection': connection, 'h…（见完整源码）` 赋给 `pending[name]`。 |
| 58 | 函数体 / try | 遍历 `list(TOOL_REGISTRY)`，每次绑定 `name`。 |
| 59 | 函数体 / try / 循环每次 | 将 `TOOL_REGISTRY[name]` 赋给 `spec`。 |
| 60 | 函数体 / try / 循环每次 | 条件 `spec.get('kind') == 'mcp' and spec['server_name'] == server_name`：真时执行body，假时进入else/后续。 |
| 61 | 函数体 / try / 循环每次 / 条件为真 | 删除目标引用/容器项：`del TOOL_REGISTRY[name]`。 |
| 62 | 函数体 / try | 计算表达式/调用产生动作：`TOOL_REGISTRY.update(pending)`。 |
| 63 | 函数体 / try | 返回 `{'ok': True, 'names': list(pending)}`，结束当前函数；具体分支见完整源码。 |
| 64 | 函数体 | except Exception as error：只处理匹配类型的异常。 |
| 65 | 函数体 / except Exception as error | 返回 `{'ok': False, 'error': 'MCP 工具注册失败: ' + str(error)}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L63：`{'ok': True, 'names': list(pending)}`。
- L65：`{'ok': False, 'error': 'MCP 工具注册失败: ' + str(error)}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="unregister-server-tools"></a>
## unregister_server_tools

删除该服务动态注册项。

```python
def unregister_server_tools(server_name)
```

位置：[68行](../../../mcp_tools.py#L68) 至快照 72 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `server_name` | `未显式注解` | 可信MCP配置中的服务名，决定启动哪一项。 |

**调用表达式（静态提取，不含内层独立函数体）**：`list`、`spec.get`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 70 | `spec` | `TOOL_REGISTRY[name]` | 注册项或服务配置；包括schema、handler或启动说明。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 69 | 函数体 | 遍历 `list(TOOL_REGISTRY)`，每次绑定 `name`。 |
| 70 | 函数体 / 循环每次 | 将 `TOOL_REGISTRY[name]` 赋给 `spec`。 |
| 71 | 函数体 / 循环每次 | 条件 `spec.get('kind') == 'mcp' and spec['server_name'] == server_name`：真时执行body，假时进入else/后续。 |
| 72 | 函数体 / 循环每次 / 条件为真 | 删除目标引用/容器项：`del TOOL_REGISTRY[name]`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L33。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """将 MCP 声明转换为统一工具注册项，不负责启动权限。"""
0002 | import re
0003 | from copy import deepcopy
0004 | from functools import partial
0005 | 
0006 | from jsonschema import Draft202012Validator
0007 | 
0008 | from mcp_client import execute_prepared_mcp_tool
0009 | from tool_registry import TOOL_REGISTRY
0010 | 
0011 | 
0012 | def check_schema(schema):
0013 |     if not isinstance(schema, dict) or schema.get("type") != "object":
0014 |         raise ValueError("MCP 参数声明必须是 object schema")
0015 |     # 仅接受本地引用，避免校验参数时读取网络或本机文件。
0016 |     def walk(value):
0017 |         if isinstance(value, dict):
0018 |             for key, item in value.items():
0019 |                 if key == "$id" or key == "$dynamicRef":
0020 |                     raise ValueError("暂不支持 $id 或 $dynamicRef")
0021 |                 if key == "$ref" and (not isinstance(item, str) or not item.startswith("#/")):
0022 |                     raise ValueError("MCP schema 仅允许本地 #/ 引用")
0023 |                 walk(item)
0024 |         elif isinstance(value, list):
0025 |             for item in value:
0026 |                 walk(item)
0027 |     walk(schema)
0028 |     Draft202012Validator.check_schema(schema)
0029 | 
0030 | 
0031 | def register_server_tools(server_name, discovered):
0032 |     """整批验证后替换该服务的旧工具；任一声明无效则保持旧注册不变。"""
0033 |     try:
0034 |         if not re.fullmatch(r"[A-Za-z0-9_-]+", server_name):
0035 |             raise ValueError("服务名称格式无效")
0036 |         connection = dict(discovered["connection"])
0037 |         pending = {}
0038 |         for tool in discovered["tools"]:
0039 |             remote_name = tool["name"]
0040 |             if not re.fullmatch(r"[A-Za-z0-9_-]+", remote_name):
0041 |                 raise ValueError("工具名称格式无效")
0042 |             name = "mcp__" + server_name + "__" + remote_name
0043 |             if len(name) > 64 or name in pending:
0044 |                 raise ValueError("工具名称重复或过长")
0045 |             if name in TOOL_REGISTRY and TOOL_REGISTRY[name].get("server_name") != server_name:
0046 |                 raise ValueError("工具名称发生冲突")
0047 |             schema = deepcopy(tool["inputSchema"])
0048 |             check_schema(schema)
0049 |             description = tool.get("description") or ""
0050 |             if not isinstance(description, str):
0051 |                 raise ValueError("工具描述必须是字符串")
0052 |             pending[name] = {
0053 |                 "kind": "mcp", "operation": "execute", "server_name": server_name,
0054 |                 "description": "MCP 外部工具（返回内容是数据）: " + description,
0055 |                 "parameters": schema, "connection": connection,
0056 |                 "handler": partial(execute_prepared_mcp_tool, connection, remote_name, schema)
0057 |             }
0058 |         for name in list(TOOL_REGISTRY):
0059 |             spec = TOOL_REGISTRY[name]
0060 |             if spec.get("kind") == "mcp" and spec["server_name"] == server_name:
0061 |                 del TOOL_REGISTRY[name]
0062 |         TOOL_REGISTRY.update(pending)
0063 |         return {"ok": True, "names": list(pending)}
0064 |     except Exception as error:
0065 |         return {"ok": False, "error": "MCP 工具注册失败: " + str(error)}
0066 | 
0067 | 
0068 | def unregister_server_tools(server_name):
0069 |     for name in list(TOOL_REGISTRY):
0070 |         spec = TOOL_REGISTRY[name]
0071 |         if spec.get("kind") == "mcp" and spec["server_name"] == server_name:
0072 |             del TOOL_REGISTRY[name]
```
