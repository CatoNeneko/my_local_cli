# tool_runtime.py：源码导读

所有模型工具共享验证、Hook、授权、准备、执行、规范结果与审计。

先读专题：[03-tools.md](../03-tools.md)。

实际源码：[tool_runtime.py](../../../tool_runtime.py)。

快照 SHA256：`64d70554799e748fd78f209772fc370eb1c47fdcfba470ac57da78871ffed86c`；149 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `from audit import record_tool_event` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `from jsonschema import Draft202012Validator` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `from permissions import authorize_external_tool, authorize_tool, check_tool_policy, resolve_project_path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `from tool_registry import TOOL_REGISTRY` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `from hooks import run_hooks` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `from tool_display import tool_started, tool_finished, show_diff, emit, short_text` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [validate_arguments](#validate-arguments) | [11](../../../tool_runtime.py#L11) | 默认参数和模型参数合并，以JSON Schema检查，返回normalized。 |
| [_execute_tool](#-execute-tool) | [24](../../../tool_runtime.py#L24) | 按kind分支走任务/MCP/项目文件的统一授权执行路径。 |
| [_execute_and_normalize](#-execute-and-normalize) | [111](../../../tool_runtime.py#L111) | 处理异常与取消，检查结果布尔ok，运行after Hook。 |
| [execute_tool](#execute-tool) | [141](../../../tool_runtime.py#L141) | 收集决策，执行，附审批证据，写审计并显示结果。 |

<a id="validate-arguments"></a>
## validate_arguments

默认参数和模型参数合并，以JSON Schema检查，返回normalized。

```python
def validate_arguments(spec, arguments)
```

位置：[11行](../../../tool_runtime.py#L11) 至快照 21 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `spec` | `未显式注解` | 注册项或服务配置；包括schema、handler或启动说明。 |
| `arguments` | `未显式注解` | 外部或模型提交的工具参数，必须经schema检查。 |

**调用表达式（静态提取，不含内层独立函数体）**：`'.'.join`、`Draft202012Validator`、`Draft202012Validator(schema).iter_errors`、`dict`、`isinstance`、`next`、`normalized.update`、`spec.get`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 14 | `schema` | `spec['parameters']` | 工具参数/输出JSON Schema，用于结构化验证。 |
| 15 | `normalized` | `dict(spec.get('defaults', {}))` | 默认值合并并经schema验证后的参数/规范结果。 |
| 17 | `error` | `next(Draft202012Validator(schema).iter_errors(normalized), None)` | 捕获的异常或错误字段，返回前可只保留类型以避免泄露。 |
| 19 | `location` | `'.'.join((str(part) for part in error.path)) or '参数'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 12 | 函数体 | 条件 `not isinstance(arguments, dict)`：真时执行body，假时进入else/后续。 |
| 13 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '工具参数必须是字典'}`，结束当前函数；具体分支见完整源码。 |
| 14 | 函数体 | 将 `spec['parameters']` 赋给 `schema`。 |
| 15 | 函数体 | 将 `dict(spec.get('defaults', {}))` 赋给 `normalized`。 |
| 16 | 函数体 | 计算表达式/调用产生动作：`normalized.update(arguments)`。 |
| 17 | 函数体 | 将 `next(Draft202012Validator(schema).iter_errors(normalized), None)` 赋给 `error`。 |
| 18 | 函数体 | 条件 `error is not None`：真时执行body，假时进入else/后续。 |
| 19 | 函数体 / 条件为真 | 将 `'.'.join((str(part) for part in error.path)) or '参数'` 赋给 `location`。 |
| 20 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '工具参数不符合声明: ' + location}`，结束当前函数；具体分支见完整源码。 |
| 21 | 函数体 | 返回 `{'ok': True, 'arguments': normalized}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L13：`{'ok': False, 'error': '工具参数必须是字典'}`。
- L20：`{'ok': False, 'error': '工具参数不符合声明: ' + location}`。
- L21：`{'ok': True, 'arguments': normalized}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="-execute-tool"></a>
## _execute_tool

按kind分支走任务/MCP/项目文件的统一授权执行路径。

```python
def _execute_tool(name, arguments, source)
```

位置：[24行](../../../tool_runtime.py#L24) 至快照 108 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| `arguments` | `未显式注解` | 外部或模型提交的工具参数，必须经schema检查。 |
| `source` | `未显式注解` | 可信调用方指定的来源，model或user；不能从模型参数中采纳。 |

**调用表达式（静态提取，不含内层独立函数体）**：`authorize_action`、`authorize_external_tool`、`authorize_tool`、`check_tool_policy`、`isinstance`、`json.dumps`、`prepared.get`、`record_decision`、`resolve_project_path`、`run_hooks`、`show_diff`、`spec.get`、`spec['handler']`、`spec['prepare']`、`type`、`validate_arguments`、`write_boundary`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 27 | `spec` | `TOOL_REGISTRY[name]` | 注册项或服务配置；包括schema、handler或启动说明。 |
| 28 | `operation` | `spec.get('operation')` | read/write/execute操作分类，用于权限与Hook。 |
| 29 | `policy` | `check_tool_policy(operation, source)` | 来源与操作的权限配置/检查结果。 |
| 32 | `validated` | `validate_arguments(spec, arguments)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 35 | `normalized` | `validated['arguments']` | 默认值合并并经schema验证后的参数/规范结果。 |
| 41 | `hooks` | `run_hooks('before_tool', {'name': name, 'operation': operation, 'source': source, 'arguments': normalized})` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 45 | `approved` | `authorize_action(name, operation, normalized['task_id'], source, json.dumps(normalized, ensure_ascii=False))` | 审批器结果；不等于已经执行。 |
| 50 | `hook_result` | `run_hooks('before_tool', {'name': name, 'operation': operation, 'source': source, 'arguments': normalized})` | 回调检查结果；before失败拒绝，after失败仅警告。 |
| 55 | `details` | `spec['connection']['details']` | 用户确认/审批展示的动作说明。 |
| 57 | `authorization` | `authorize_external_tool(name, spec['server_name'], source, details)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 63 | `original_path` | `normalized['path']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 64 | `checked` | `resolve_project_path(original_path)` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 67 | `normalized['path']` | `checked['path']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 69 | `hook_result` | `run_hooks('before_tool', {'name': name, 'operation': operation, 'source': source, 'arguments': normalized})` | 回调检查结果；before失败拒绝，after失败仅警告。 |
| 77 | `boundary` | `write_boundary(normalized['path'])` | 写入硬边界检查结果，优先于模型审查。 |
| 82 | `prepared` | `None` | prepare形成的待审快照：diff/字节或沙箱命令参数。 |
| 85 | `prepared` | `spec['prepare'](**{**normalized, 'path': original_path})` | prepare形成的待审快照：diff/字节或沙箱命令参数。 |
| 95 | `details` | `spec.get('details', '')` | 用户确认/审批展示的动作说明。 |
| 97 | `details` | `'关键词: ' + normalized['keyword']` | 用户确认/审批展示的动作说明。 |
| 99 | `details` | `prepared.get('details', details)` | 用户确认/审批展示的动作说明。 |
| 100 | `authorized` | `authorize_tool(name, operation, original_path, source, details, prepared=prepared)` | 批准与目标复查结果；失败不能调用实际handler。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 25 | 函数体 | 条件 `not isinstance(name, str) or name not in TOOL_REGISTRY`：真时执行body，假时进入else/后续。 |
| 26 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '未知工具'}`，结束当前函数；具体分支见完整源码。 |
| 27 | 函数体 | 将 `TOOL_REGISTRY[name]` 赋给 `spec`。 |
| 28 | 函数体 | 将 `spec.get('operation')` 赋给 `operation`。 |
| 29 | 函数体 | 将 `check_tool_policy(operation, source)` 赋给 `policy`。 |
| 30 | 函数体 | 条件 `not policy['ok']`：真时执行body，假时进入else/后续。 |
| 31 | 函数体 / 条件为真 | 返回 `policy`，结束当前函数；具体分支见完整源码。 |
| 32 | 函数体 | 将 `validate_arguments(spec, arguments)` 赋给 `validated`。 |
| 33 | 函数体 | 条件 `not validated['ok']`：真时执行body，假时进入else/后续。 |
| 34 | 函数体 / 条件为真 | 返回 `validated`，结束当前函数；具体分支见完整源码。 |
| 35 | 函数体 | 将 `validated['arguments']` 赋给 `normalized`。 |
| 36 | 函数体 | 条件 `spec.get('kind') == 'task'`：真时执行body，假时进入else/后续。 |
| 37 | 函数体 / 条件为真 | 在此处导入依赖：`from process_tasks import JOBS`；局部导入可延迟加载或避免循环。 |
| 38 | 函数体 / 条件为真 | 在此处导入依赖：`from approval import authorize_action`；局部导入可延迟加载或避免循环。 |
| 39 | 函数体 / 条件为真 | 条件 `normalized['task_id'] not in JOBS`：真时执行body，假时进入else/后续。 |
| 40 | 函数体 / 条件为真 / 条件为真 | 返回 `{'ok': False, 'error': '未知当前进程任务 ID'}`，结束当前函数；具体分支见完整源码。 |
| 41 | 函数体 / 条件为真 | 将 `run_hooks('before_tool', {'name': name, 'operation': operation, 'source': source, 'arguments': normalized})` 赋给 `hooks`。 |
| 43 | 函数体 / 条件为真 | 条件 `not hooks['ok']`：真时执行body，假时进入else/后续。 |
| 44 | 函数体 / 条件为真 / 条件为真 | 返回 `hooks`，结束当前函数；具体分支见完整源码。 |
| 45 | 函数体 / 条件为真 | 将 `authorize_action(name, operation, normalized['task_id'], source, json.dumps(normalized, ensure_ascii=False))` 赋给 `approved`。 |
| 46 | 函数体 / 条件为真 | 条件 `not approved['ok']`：真时执行body，假时进入else/后续。 |
| 47 | 函数体 / 条件为真 / 条件为真 | 返回 `approved`，结束当前函数；具体分支见完整源码。 |
| 48 | 函数体 / 条件为真 | 返回 `spec['handler'](**normalized)`，结束当前函数；具体分支见完整源码。 |
| 49 | 函数体 | 条件 `spec.get('kind') == 'mcp'`：真时执行body，假时进入else/后续。 |
| 50 | 函数体 / 条件为真 | 将 `run_hooks('before_tool', {'name': name, 'operation': operation, 'source': source, 'arguments': normalized})` 赋给 `hook_result`。 |
| 53 | 函数体 / 条件为真 | 条件 `not hook_result['ok']`：真时执行body，假时进入else/后续。 |
| 54 | 函数体 / 条件为真 / 条件为真 | 返回 `hook_result`，结束当前函数；具体分支见完整源码。 |
| 55 | 函数体 / 条件为真 | 将 `spec['connection']['details']` 赋给 `details`。 |
| 56 | 函数体 / 条件为真 | 更新已有变量：`details += '\n工具参数: ' + json.dumps(normalized, ensure_ascii=False)`。 |
| 57 | 函数体 / 条件为真 | 将 `authorize_external_tool(name, spec['server_name'], source, details)` 赋给 `authorization`。 |
| 58 | 函数体 / 条件为真 | 条件 `not authorization['ok']`：真时执行body，假时进入else/后续。 |
| 59 | 函数体 / 条件为真 / 条件为真 | 返回 `authorization`，结束当前函数；具体分支见完整源码。 |
| 60 | 函数体 / 条件为真 | 返回 `spec['handler'](normalized)`，结束当前函数；具体分支见完整源码。 |
| 61 | 函数体 | 条件 `'path' not in normalized`：真时执行body，假时进入else/后续。 |
| 62 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '当前执行器要求声明 path 参数'}`，结束当前函数；具体分支见完整源码。 |
| 63 | 函数体 | 将 `normalized['path']` 赋给 `original_path`。 |
| 64 | 函数体 | 将 `resolve_project_path(original_path)` 赋给 `checked`。 |
| 65 | 函数体 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 66 | 函数体 / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 67 | 函数体 | 将 `checked['path']` 赋给 `normalized['path']`。 |
| 69 | 函数体 | 将 `run_hooks('before_tool', {'name': name, 'operation': operation, 'source': source, 'arguments': normalized})` 赋给 `hook_result`。 |
| 72 | 函数体 | 条件 `not hook_result['ok']`：真时执行body，假时进入else/后续。 |
| 73 | 函数体 / 条件为真 | 返回 `hook_result`，结束当前函数；具体分支见完整源码。 |
| 75 | 函数体 | 条件 `operation == 'write'`：真时执行body，假时进入else/后续。 |
| 76 | 函数体 / 条件为真 | 在此处导入依赖：`from approval import write_boundary, record_decision`；局部导入可延迟加载或避免循环。 |
| 77 | 函数体 / 条件为真 | 将 `write_boundary(normalized['path'])` 赋给 `boundary`。 |
| 78 | 函数体 / 条件为真 | 条件 `not boundary['ok']`：真时执行body，假时进入else/后续。 |
| 79 | 函数体 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`record_decision(name, 'rule', 'deny', 'client_control')`。 |
| 80 | 函数体 / 条件为真 / 条件为真 | 返回 `boundary`，结束当前函数；具体分支见完整源码。 |
| 82 | 函数体 | 将 `None` 赋给 `prepared`。 |
| 83 | 函数体 | 条件 `spec.get('prepare') is not None`：真时执行body，假时进入else/后续。 |
| 85 | 函数体 / 条件为真 | 将 `spec['prepare'](**{**normalized, 'path': original_path})` 赋给 `prepared`。 |
| 86 | 函数体 / 条件为真 | 条件 `not isinstance(prepared, dict) or type(prepared.get('ok')) is not bool`：真时执行body，假时进入else/后续。 |
| 87 | 函数体 / 条件为真 / 条件为真 | 返回 `{'ok': False, 'error': '工具准备结果格式错误'}`，结束当前函数；具体分支见完整源码。 |
| 88 | 函数体 / 条件为真 | 条件 `not prepared['ok']`：真时执行body，假时进入else/后续。 |
| 89 | 函数体 / 条件为真 / 条件为真 | 返回 `prepared`，结束当前函数；具体分支见完整源码。 |
| 90 | 函数体 / 条件为真 | 条件 `operation == 'write' and prepared.get('changed') is False`：真时执行body，假时进入else/后续。 |
| 91 | 函数体 / 条件为真 / 条件为真 | 返回 `{'ok': True, 'changed': False, 'message': '文件内容没有变化'}`，结束当前函数；具体分支见完整源码。 |
| 92 | 函数体 / 条件为真 | 条件 `'diff' in prepared`：真时执行body，假时进入else/后续。 |
| 93 | 函数体 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`show_diff(prepared['diff'])`。 |
| 95 | 函数体 | 将 `spec.get('details', '')` 赋给 `details`。 |
| 96 | 函数体 | 条件 `'keyword' in normalized`：真时执行body，假时进入else/后续。 |
| 97 | 函数体 / 条件为真 | 将 `'关键词: ' + normalized['keyword']` 赋给 `details`。 |
| 98 | 函数体 | 条件 `prepared is not None`：真时执行body，假时进入else/后续。 |
| 99 | 函数体 / 条件为真 | 将 `prepared.get('details', details)` 赋给 `details`。 |
| 100 | 函数体 | 将 `authorize_tool(name, operation, original_path, source, details, prepared=prepared)` 赋给 `authorized`。 |
| 101 | 函数体 | 条件 `not authorized['ok']`：真时执行body，假时进入else/后续。 |
| 102 | 函数体 / 条件为真 | 返回 `authorized`，结束当前函数；具体分支见完整源码。 |
| 103 | 函数体 | 条件 `authorized['path'] != normalized['path']`：真时执行body，假时进入else/后续。 |
| 104 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '工具准备期间路径目标已变化，请重新提交'}`，结束当前函数；具体分支见完整源码。 |
| 106 | 函数体 | 条件 `prepared is not None`：真时执行body，假时进入else/后续。 |
| 107 | 函数体 / 条件为真 | 返回 `spec['handler'](prepared)`，结束当前函数；具体分支见完整源码。 |
| 108 | 函数体 | 返回 `spec['handler'](**normalized)`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L26：`{'ok': False, 'error': '未知工具'}`。
- L31：`policy`。
- L34：`validated`。
- L40：`{'ok': False, 'error': '未知当前进程任务 ID'}`。
- L44：`hooks`。
- L47：`approved`。
- L48：`spec['handler'](**normalized)`。
- L54：`hook_result`。
- L59：`authorization`。
- L60：`spec['handler'](normalized)`。
- L62：`{'ok': False, 'error': '当前执行器要求声明 path 参数'}`。
- L66：`checked`。
- L73：`hook_result`。
- L80：`boundary`。
- L87：`{'ok': False, 'error': '工具准备结果格式错误'}`。
- L89：`prepared`。
- L91：`{'ok': True, 'changed': False, 'message': '文件内容没有变化'}`。
- L102：`authorized`。
- L104：`{'ok': False, 'error': '工具准备期间路径目标已变化，请重新提交'}`。
- L107：`spec['handler'](prepared)`。
- L108：`spec['handler'](**normalized)`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="-execute-and-normalize"></a>
## _execute_and_normalize

处理异常与取消，检查结果布尔ok，运行after Hook。

```python
def _execute_and_normalize(name, arguments, source='model')
```

位置：[111行](../../../tool_runtime.py#L111) 至快照 138 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| `arguments` | `未显式注解` | 外部或模型提交的工具参数，必须经schema检查。 |
| `source` | `未显式注解` | 可信调用方指定的来源，model或user；不能从模型参数中采纳。 |

**调用表达式（静态提取，不含内层独立函数体）**：`TOOL_REGISTRY.get`、`_execute_tool`、`dict`、`emit`、`isinstance`、`result.get`、`run_hooks`、`short_text`、`spec.get`、`tool_started`、`type`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 115 | `result` | `_execute_tool(name, arguments, source)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 117 | `result` | `{'ok': False, 'cancelled': True, 'error': '工具已取消；已完成的操作不会回滚，写入或外部操作请检查实际状态'}` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 120 | `error_type` | `type(error).__name__` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 122 | `result` | `{'ok': False, 'error': '工具执行异常: ' + error_type}` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 124 | `result` | `{'ok': False, 'error': '工具返回结果必须包含布尔类型的 ok'}` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 125 | `spec` | `TOOL_REGISTRY.get(name) if isinstance(name, str) else None` | 注册项或服务配置；包括schema、handler或启动说明。 |
| 128 | `hook_result` | `run_hooks('after_tool', {'name': name, 'operation': spec.get('operation'), 'source': source, 'arguments': arguments, 'result': res…（见完整源码）` | 回调检查结果；before失败拒绝，after失败仅警告。 |
| 133 | `result` | `{**result, 'cancelled': True}` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 134 | `hook_result` | `{'ok': False, 'error': '执行后 Hook 已取消；工具结果保留'}` | 回调检查结果；before失败拒绝，after失败仅警告。 |
| 136 | `result` | `dict(result)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 137 | `result['hook_warning']` | `hook_result['error']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 112 | 函数体 | 文档字符串：说明职责，不作为普通语句动作执行。 |
| 113 | 函数体 | 计算表达式/调用产生动作：`tool_started(name, arguments)`。 |
| 114 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 115 | 函数体 / try | 将 `_execute_tool(name, arguments, source)` 赋给 `result`。 |
| 116 | 函数体 | except KeyboardInterrupt：只处理匹配类型的异常。 |
| 117 | 函数体 / except KeyboardInterrupt | 将 `{'ok': False, 'cancelled': True, 'error': '工具已取消；已完成的操作不会回滚，写入或外部操作请检查实际状态'}` 赋给 `result`。 |
| 119 | 函数体 | except Exception as error：只处理匹配类型的异常。 |
| 120 | 函数体 / except Exception as error | 将 `type(error).__name__` 赋给 `error_type`。 |
| 121 | 函数体 / except Exception as error | 计算表达式/调用产生动作：`emit('工具执行异常: ' + error_type + ' ' + short_text(error), 'ansired')`。 |
| 122 | 函数体 / except Exception as error | 将 `{'ok': False, 'error': '工具执行异常: ' + error_type}` 赋给 `result`。 |
| 123 | 函数体 | 条件 `not isinstance(result, dict) or type(result.get('ok')) is not bool`：真时执行body，假时进入else/后续。 |
| 124 | 函数体 / 条件为真 | 将 `{'ok': False, 'error': '工具返回结果必须包含布尔类型的 ok'}` 赋给 `result`。 |
| 125 | 函数体 | 将 `TOOL_REGISTRY.get(name) if isinstance(name, str) else None` 赋给 `spec`。 |
| 126 | 函数体 | 条件 `spec is not None`：真时执行body，假时进入else/后续。 |
| 127 | 函数体 / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 128 | 函数体 / 条件为真 / try | 将 `run_hooks('after_tool', {'name': name, 'operation': spec.get('operation'), 'source': source, 'arguments': arguments, 'result': result})` 赋给 `hook_result`。 |
| 132 | 函数体 / 条件为真 | except KeyboardInterrupt：只处理匹配类型的异常。 |
| 133 | 函数体 / 条件为真 / except KeyboardInterrupt | 将 `{**result, 'cancelled': True}` 赋给 `result`。 |
| 134 | 函数体 / 条件为真 / except KeyboardInterrupt | 将 `{'ok': False, 'error': '执行后 Hook 已取消；工具结果保留'}` 赋给 `hook_result`。 |
| 135 | 函数体 / 条件为真 | 条件 `not hook_result['ok']`：真时执行body，假时进入else/后续。 |
| 136 | 函数体 / 条件为真 / 条件为真 | 将 `dict(result)` 赋给 `result`。 |
| 137 | 函数体 / 条件为真 / 条件为真 | 将 `hook_result['error']` 赋给 `result['hook_warning']`。 |
| 138 | 函数体 | 返回 `result`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L138：`result`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="execute-tool"></a>
## execute_tool

收集决策，执行，附审批证据，写审计并显示结果。

```python
def execute_tool(name, arguments, source='model')
```

位置：[141行](../../../tool_runtime.py#L141) 至快照 149 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| `arguments` | `未显式注解` | 外部或模型提交的工具参数，必须经schema检查。 |
| `source` | `未显式注解` | 可信调用方指定的来源，model或user；不能从模型参数中采纳。 |

**调用表达式（静态提取，不含内层独立函数体）**：`_execute_and_normalize`、`decision_scope`、`isinstance`、`list`、`record_tool_event`、`tool_finished`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 144 | `result` | `_execute_and_normalize(name, arguments, source)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 146 | `result` | `{**result, 'approval': list(decisions)}` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 142 | 函数体 | 在此处导入依赖：`from approval import decision_scope`；局部导入可延迟加载或避免循环。 |
| 143 | 函数体 | 进入资源/状态范围：`decision_scope()` 绑定 `decisions`；退出执行清理。 |
| 144 | 函数体 / with范围 | 将 `_execute_and_normalize(name, arguments, source)` 赋给 `result`。 |
| 145 | 函数体 / with范围 | 条件 `decisions`：真时执行body，假时进入else/后续。 |
| 146 | 函数体 / with范围 / 条件为真 | 将 `{**result, 'approval': list(decisions)}` 赋给 `result`。 |
| 147 | 函数体 / with范围 | 计算表达式/调用产生动作：`record_tool_event(name if isinstance(name, str) else 'invalid_tool', result)`。 |
| 148 | 函数体 / with范围 | 计算表达式/调用产生动作：`tool_finished(name, result)`。 |
| 149 | 函数体 / with范围 | 返回 `result`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L149：`result`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L114, L127。
- with/yield：资源/状态生命周期或逐个生成：L143。
- 推导式/生成器表达式：循环建容器或逐个产生：L19。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """所有模型工具的共享执行入口：验证、授权、执行、规范结果和记录。"""
0002 | from audit import record_tool_event
0003 | import json
0004 | from jsonschema import Draft202012Validator
0005 | from permissions import authorize_external_tool, authorize_tool, check_tool_policy, resolve_project_path
0006 | from tool_registry import TOOL_REGISTRY
0007 | from hooks import run_hooks
0008 | from tool_display import tool_started, tool_finished, show_diff, emit, short_text
0009 | 
0010 | 
0011 | def validate_arguments(spec, arguments):
0012 |     if not isinstance(arguments, dict):
0013 |         return {"ok": False, "error": "工具参数必须是字典"}
0014 |     schema = spec["parameters"]
0015 |     normalized = dict(spec.get("defaults", {}))
0016 |     normalized.update(arguments)
0017 |     error = next(Draft202012Validator(schema).iter_errors(normalized), None)
0018 |     if error is not None:
0019 |         location = ".".join(str(part) for part in error.path) or "参数"
0020 |         return {"ok": False, "error": "工具参数不符合声明: " + location}
0021 |     return {"ok": True, "arguments": normalized}
0022 | 
0023 | 
0024 | def _execute_tool(name, arguments, source):
0025 |     if not isinstance(name, str) or name not in TOOL_REGISTRY:
0026 |         return {"ok": False, "error": "未知工具"}
0027 |     spec = TOOL_REGISTRY[name]
0028 |     operation = spec.get("operation")
0029 |     policy = check_tool_policy(operation, source)
0030 |     if not policy["ok"]:
0031 |         return policy
0032 |     validated = validate_arguments(spec, arguments)
0033 |     if not validated["ok"]:
0034 |         return validated
0035 |     normalized = validated["arguments"]
0036 |     if spec.get('kind') == 'task':
0037 |         from process_tasks import JOBS
0038 |         from approval import authorize_action
0039 |         if normalized['task_id'] not in JOBS:
0040 |             return {'ok': False, 'error': '未知当前进程任务 ID'}
0041 |         hooks = run_hooks('before_tool', {
0042 |             'name': name, 'operation': operation, 'source': source, 'arguments': normalized})
0043 |         if not hooks['ok']:
0044 |             return hooks
0045 |         approved = authorize_action(name, operation, normalized['task_id'], source, json.dumps(normalized, ensure_ascii=False))
0046 |         if not approved['ok']:
0047 |             return approved
0048 |         return spec['handler'](**normalized)
0049 |     if spec.get("kind") == "mcp":
0050 |         hook_result = run_hooks("before_tool", {
0051 |             "name": name, "operation": operation, "source": source, "arguments": normalized
0052 |         })
0053 |         if not hook_result["ok"]:
0054 |             return hook_result
0055 |         details = spec["connection"]["details"]
0056 |         details += "\n工具参数: " + json.dumps(normalized, ensure_ascii=False)
0057 |         authorization = authorize_external_tool(name, spec["server_name"], source, details)
0058 |         if not authorization["ok"]:
0059 |             return authorization
0060 |         return spec["handler"](normalized)
0061 |     if "path" not in normalized:
0062 |         return {"ok": False, "error": "当前执行器要求声明 path 参数"}
0063 |     original_path = normalized["path"]
0064 |     checked = resolve_project_path(original_path)
0065 |     if not checked["ok"]:
0066 |         return checked
0067 |     normalized["path"] = checked["path"]
0068 | 
0069 |     hook_result = run_hooks("before_tool", {
0070 |         "name": name, "operation": operation, "source": source, "arguments": normalized
0071 |     })
0072 |     if not hook_result["ok"]:
0073 |         return hook_result
0074 | 
0075 |     if operation == 'write':
0076 |         from approval import write_boundary, record_decision
0077 |         boundary = write_boundary(normalized['path'])
0078 |         if not boundary['ok']:
0079 |             record_decision(name, 'rule', 'deny', 'client_control')
0080 |             return boundary
0081 | 
0082 |     prepared = None
0083 |     if spec.get("prepare") is not None:
0084 |         # 准备阶段保留原始路径，让新建工具也能检查其中的符号链接。
0085 |         prepared = spec["prepare"](**{**normalized, "path": original_path})
0086 |         if not isinstance(prepared, dict) or type(prepared.get("ok")) is not bool:
0087 |             return {"ok": False, "error": "工具准备结果格式错误"}
0088 |         if not prepared["ok"]:
0089 |             return prepared
0090 |         if operation == "write" and prepared.get("changed") is False:
0091 |             return {"ok": True, "changed": False, "message": "文件内容没有变化"}
0092 |         if "diff" in prepared:
0093 |             show_diff(prepared["diff"])
0094 | 
0095 |     details = spec.get("details", "")
0096 |     if "keyword" in normalized:
0097 |         details = "关键词: " + normalized["keyword"]
0098 |     if prepared is not None:
0099 |         details = prepared.get("details", details)
0100 |     authorized = authorize_tool(name, operation, original_path, source, details, prepared=prepared)
0101 |     if not authorized["ok"]:
0102 |         return authorized
0103 |     if authorized["path"] != normalized["path"]:
0104 |         return {"ok": False, "error": "工具准备期间路径目标已变化，请重新提交"}
0105 | 
0106 |     if prepared is not None:
0107 |         return spec["handler"](prepared)
0108 |     return spec["handler"](**normalized)
0109 | 
0110 | 
0111 | def _execute_and_normalize(name, arguments, source="model"):
0112 |     """source 由可信调用方指定，不从模型 arguments 中读取。"""
0113 |     tool_started(name, arguments)
0114 |     try:
0115 |         result = _execute_tool(name, arguments, source)
0116 |     except KeyboardInterrupt:
0117 |         result = {'ok': False, 'cancelled': True,
0118 |                   'error': '工具已取消；已完成的操作不会回滚，写入或外部操作请检查实际状态'}
0119 |     except Exception as error:
0120 |         error_type = type(error).__name__
0121 |         emit("工具执行异常: " + error_type + " " + short_text(error), "ansired")
0122 |         result = {"ok": False, "error": "工具执行异常: " + error_type}
0123 |     if not isinstance(result, dict) or type(result.get("ok")) is not bool:
0124 |         result = {"ok": False, "error": "工具返回结果必须包含布尔类型的 ok"}
0125 |     spec = TOOL_REGISTRY.get(name) if isinstance(name, str) else None
0126 |     if spec is not None:
0127 |         try:
0128 |             hook_result = run_hooks("after_tool", {
0129 |                 "name": name, "operation": spec.get("operation"), "source": source,
0130 |                 "arguments": arguments, "result": result
0131 |             })
0132 |         except KeyboardInterrupt:
0133 |             result = {**result, 'cancelled': True}
0134 |             hook_result = {'ok': False, 'error': '执行后 Hook 已取消；工具结果保留'}
0135 |         if not hook_result["ok"]:
0136 |             result = dict(result)
0137 |             result["hook_warning"] = hook_result["error"]
0138 |     return result
0139 | 
0140 | 
0141 | def execute_tool(name, arguments, source="model"):
0142 |     from approval import decision_scope
0143 |     with decision_scope() as decisions:
0144 |         result = _execute_and_normalize(name, arguments, source)
0145 |         if decisions:
0146 |             result = {**result, 'approval': list(decisions)}
0147 |         record_tool_event(name if isinstance(name, str) else "invalid_tool", result)
0148 |         tool_finished(name, result)
0149 |         return result
```
