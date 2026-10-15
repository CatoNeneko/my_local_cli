# permissions.py：源码导读

共享项目真实路径边界、确认策略与外部工具授权。

先读专题：[03-tools.md](../03-tools.md)。

实际源码：[permissions.py](../../../permissions.py)。

快照 SHA256：`937083dbb34569d8f64da8faea70f4b0107811fbfb4f508a412332a1d2aec205`；98 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import os` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `from config import permission_config` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `from tool_display import safe_text` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 9 | `PROJECT_ROOT = Path(__file__).resolve().parent` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [resolve_project_path](#resolve-project-path) | [12](../../../permissions.py#L12) | 解析真实路径并检查项目边界与受保护名字。 |
| [confirm_tool](#confirm-tool) | [31](../../../permissions.py#L31) | 生成安全显示的工具请求提示，再通过当前确认界面获取选择。 |
| [authorize_tool](#authorize-tool) | [39](../../../permissions.py#L39) | 合法路径→审批→复查真实目标未变化。 |
| [check_tool_policy](#check-tool-policy) | [59](../../../permissions.py#L59) | 读取来源/动作策略，缺失或非布尔配置拒绝。 |
| [authorize_external_tool](#authorize-external-tool) | [68](../../../permissions.py#L68) | 外部execute策略确认，不制造本地路径隔离假象。 |
| [protected_project_paths](#protected-project-paths) | [80](../../../permissions.py#L80) | 遍历项目私有路径，供沙箱遮蔽；跳链接与受保护目录的下探。 |
| [protected_project_paths.fail](#protected-project-paths-fail) | [84](../../../permissions.py#L84) | os.walk访问错误时重新抛出，避免静默遗漏私有遮蔽目标。 |

<a id="resolve-project-path"></a>
## resolve_project_path

解析真实路径并检查项目边界与受保护名字。

```python
def resolve_project_path(path)
```

位置：[12行](../../../permissions.py#L12) 至快照 28 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`any`、`candidate.is_absolute`、`candidate.resolve`、`isinstance`、`resolved_path.is_relative_to`、`resolved_path.relative_to`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 16 | `candidate` | `Path(path)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 18 | `candidate` | `PROJECT_ROOT / candidate` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 19 | `resolved_path` | `candidate.resolve()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 23 | `relative` | `resolved_path.relative_to(PROJECT_ROOT)` | 相对项目路径，供显示或范围检查。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 13 | 函数体 | 条件 `not isinstance(path, str) or not path or '\x00' in path`：真时执行body，假时进入else/后续。 |
| 14 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '路径必须是非空字符串，且不能包含空字符'}`，结束当前函数；具体分支见完整源码。 |
| 15 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 16 | 函数体 / try | 将 `Path(path)` 赋给 `candidate`。 |
| 17 | 函数体 / try | 条件 `not candidate.is_absolute()`：真时执行body，假时进入else/后续。 |
| 18 | 函数体 / try / 条件为真 | 将 `PROJECT_ROOT / candidate` 赋给 `candidate`。 |
| 19 | 函数体 / try | 将 `candidate.resolve()` 赋给 `resolved_path`。 |
| 20 | 函数体 / try | 条件 `not resolved_path.is_relative_to(PROJECT_ROOT)`：真时执行body，假时进入else/后续。 |
| 21 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': '禁止访问项目目录之外的文件'}`，结束当前函数；具体分支见完整源码。 |
| 23 | 函数体 / try | 将 `resolved_path.relative_to(PROJECT_ROOT)` 赋给 `relative`。 |
| 24 | 函数体 / try | 条件 `any((part in permission_config['blocked_names'] for part in relative.parts))`：真时执行body，假时进入else/后续。 |
| 25 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': '禁止访问项目内部环境、控制配置或私有记录'}`，结束当前函数；具体分支见完整源码。 |
| 26 | 函数体 / try | 返回 `{'ok': True, 'path': str(resolved_path)}`，结束当前函数；具体分支见完整源码。 |
| 27 | 函数体 | except (OSError, ValueError, RuntimeError)：只处理匹配类型的异常。 |
| 28 | 函数体 / except (OSError, ValueError, RuntimeError) | 返回 `{'ok': False, 'error': '无法解析文件路径'}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L14：`{'ok': False, 'error': '路径必须是非空字符串，且不能包含空字符'}`。
- L21：`{'ok': False, 'error': '禁止访问项目目录之外的文件'}`。
- L25：`{'ok': False, 'error': '禁止访问项目内部环境、控制配置或私有记录'}`。
- L26：`{'ok': True, 'path': str(resolved_path)}`。
- L28：`{'ok': False, 'error': '无法解析文件路径'}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="confirm-tool"></a>
## confirm_tool

生成安全显示的工具请求提示，再通过当前确认界面获取选择。

```python
def confirm_tool(name, path, details='')
```

位置：[31行](../../../permissions.py#L31) 至快照 36 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| `details` | `未显式注解` | 用户确认/审批展示的动作说明。 |

**调用表达式（静态提取，不含内层独立函数体）**：`request_confirmation`、`safe_text`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 33 | `prompt` | `'请求调用 ' + name + '\n目标: ' + path` | 发给用户或模型的说明文字；看请求接口区分。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 32 | 函数体 | 在此处导入依赖：`from terminal_input import request_confirmation`；局部导入可延迟加载或避免循环。 |
| 33 | 函数体 | 将 `'请求调用 ' + name + '\n目标: ' + path` 赋给 `prompt`。 |
| 34 | 函数体 | 条件 `details`：真时执行body，假时进入else/后续。 |
| 35 | 函数体 / 条件为真 | 更新已有变量：`prompt += '\n参数: ' + details`。 |
| 36 | 函数体 | 返回 `request_confirmation(safe_text(prompt))`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L36：`request_confirmation(safe_text(prompt))`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="authorize-tool"></a>
## authorize_tool

合法路径→审批→复查真实目标未变化。

```python
def authorize_tool(name, operation, path, source='model', details='', *, prepared=None)
```

位置：[39行](../../../permissions.py#L39) 至快照 56 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| `operation` | `未显式注解` | read/write/execute操作分类，用于权限与Hook。 |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| `source` | `未显式注解` | 可信调用方指定的来源，model或user；不能从模型参数中采纳。 |
| `details` | `未显式注解` | 用户确认/审批展示的动作说明。 |
| `prepared` | `未显式注解` | prepare形成的待审快照：diff/字节或沙箱命令参数。 |

**调用表达式（静态提取，不含内层独立函数体）**：`authorize_action`、`check_tool_policy`、`resolve_project_path`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 41 | `policy_result` | `check_tool_policy(operation, source)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 44 | `checked` | `resolve_project_path(path)` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 48 | `approved` | `authorize_action(name, operation, checked['path'], source, details, prepared=prepared)` | 审批器结果；不等于已经执行。 |
| 51 | `rechecked` | `resolve_project_path(path)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 41 | 函数体 | 将 `check_tool_policy(operation, source)` 赋给 `policy_result`。 |
| 42 | 函数体 | 条件 `not policy_result['ok']`：真时执行body，假时进入else/后续。 |
| 43 | 函数体 / 条件为真 | 返回 `policy_result`，结束当前函数；具体分支见完整源码。 |
| 44 | 函数体 | 将 `resolve_project_path(path)` 赋给 `checked`。 |
| 45 | 函数体 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 46 | 函数体 / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 47 | 函数体 | 在此处导入依赖：`from approval import authorize_action`；局部导入可延迟加载或避免循环。 |
| 48 | 函数体 | 将 `authorize_action(name, operation, checked['path'], source, details, prepared=prepared)` 赋给 `approved`。 |
| 49 | 函数体 | 条件 `not approved['ok']`：真时执行body，假时进入else/后续。 |
| 50 | 函数体 / 条件为真 | 返回 `approved`，结束当前函数；具体分支见完整源码。 |
| 51 | 函数体 | 将 `resolve_project_path(path)` 赋给 `rechecked`。 |
| 52 | 函数体 | 条件 `not rechecked['ok']`：真时执行body，假时进入else/后续。 |
| 53 | 函数体 / 条件为真 | 返回 `rechecked`，结束当前函数；具体分支见完整源码。 |
| 54 | 函数体 | 条件 `rechecked['path'] != checked['path']`：真时执行body，假时进入else/后续。 |
| 55 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '确认期间路径目标已变化，请重新提交'}`，结束当前函数；具体分支见完整源码。 |
| 56 | 函数体 | 返回 `rechecked`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L43：`policy_result`。
- L46：`checked`。
- L50：`approved`。
- L53：`rechecked`。
- L55：`{'ok': False, 'error': '确认期间路径目标已变化，请重新提交'}`。
- L56：`rechecked`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="check-tool-policy"></a>
## check_tool_policy

读取来源/动作策略，缺失或非布尔配置拒绝。

```python
def check_tool_policy(operation, source)
```

位置：[59行](../../../permissions.py#L59) 至快照 65 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `operation` | `未显式注解` | read/write/execute操作分类，用于权限与Hook。 |
| `source` | `未显式注解` | 可信调用方指定的来源，model或user；不能从模型参数中采纳。 |

**调用表达式（静态提取，不含内层独立函数体）**：`isinstance`、`permission_config['confirmation'].get`、`type`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 60 | `policy` | `permission_config['confirmation'].get(source)` | 来源与操作的权限配置/检查结果。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 60 | 函数体 | 将 `permission_config['confirmation'].get(source)` 赋给 `policy`。 |
| 61 | 函数体 | 条件 `not isinstance(policy, dict) or operation not in policy`：真时执行body，假时进入else/后续。 |
| 62 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '缺少有效的工具权限策略'}`，结束当前函数；具体分支见完整源码。 |
| 63 | 函数体 | 条件 `type(policy[operation]) is not bool`：真时执行body，假时进入else/后续。 |
| 64 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '确认策略必须是布尔值'}`，结束当前函数；具体分支见完整源码。 |
| 65 | 函数体 | 返回 `{'ok': True, 'requires_confirmation': policy[operation]}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L62：`{'ok': False, 'error': '缺少有效的工具权限策略'}`。
- L64：`{'ok': False, 'error': '确认策略必须是布尔值'}`。
- L65：`{'ok': True, 'requires_confirmation': policy[operation]}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="authorize-external-tool"></a>
## authorize_external_tool

外部execute策略确认，不制造本地路径隔离假象。

```python
def authorize_external_tool(name, target, source='model', details='')
```

位置：[68行](../../../permissions.py#L68) 至快照 77 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| `target` | `未显式注解` | 已选定的文件/目录或操作目标，提交前可能需要再次验证。 |
| `source` | `未显式注解` | 可信调用方指定的来源，model或user；不能从模型参数中采纳。 |
| `details` | `未显式注解` | 用户确认/审批展示的动作说明。 |

**调用表达式（静态提取，不含内层独立函数体）**：`check_tool_policy`、`confirm_tool`、`record_decision`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 70 | `policy` | `check_tool_policy('execute', source)` | 来源与操作的权限配置/检查结果。 |
| 74 | `accepted` | `not policy['requires_confirmation'] or confirm_tool(name, target, details)` | 人工选择是否允许或UI是否接受。 |
| 75 | `decision` | `record_decision(name, 'human' if policy['requires_confirmation'] else 'rule', 'allow' if accepted else 'deny', 'external_service')` | allow/ask/deny等受限决策值。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 69 | 函数体 | 文档字符串：说明职责，不作为普通语句动作执行。 |
| 70 | 函数体 | 将 `check_tool_policy('execute', source)` 赋给 `policy`。 |
| 71 | 函数体 | 条件 `not policy['ok']`：真时执行body，假时进入else/后续。 |
| 72 | 函数体 / 条件为真 | 返回 `policy`，结束当前函数；具体分支见完整源码。 |
| 73 | 函数体 | 在此处导入依赖：`from approval import record_decision`；局部导入可延迟加载或避免循环。 |
| 74 | 函数体 | 将 `not policy['requires_confirmation'] or confirm_tool(name, target, details)` 赋给 `accepted`。 |
| 75 | 函数体 | 将 `record_decision(name, 'human' if policy['requires_confirmation'] else 'rule', 'allow' if accepted else 'deny', 'external_service')` 赋给 `decision`。 |
| 77 | 函数体 | 返回 `{'ok': accepted, 'approval': [decision], **({} if accepted else {'error': '用户拒绝执行外部服务'})}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L72：`policy`。
- L77：`{'ok': accepted, 'approval': [decision], **({} if accepted else {'error': '用户拒绝执行外部服务'})}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="protected-project-paths"></a>
## protected_project_paths

遍历项目私有路径，供沙箱遮蔽；跳链接与受保护目录的下探。

```python
def protected_project_paths(root)
```

位置：[80行](../../../permissions.py#L80) 至快照 98 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `root` | `未显式注解` | 本次目录扫描/工作项目根。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`directories.remove`、`found.append`、`item.is_symlink`、`item.relative_to`、`list`、`os.walk`、`set`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 82 | `blocked` | `set(permission_config['blocked_names'])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 83 | `found` | `[]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 88 | `item` | `Path(directory) / name` | 遍历中的一项：字段、文件、消息或工具定义，类型取决于iter。 |
| 96 | `item` | `Path(directory) / name` | 遍历中的一项：字段、文件、消息或工具定义，类型取决于iter。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 81 | 函数体 | 文档字符串：说明职责，不作为普通语句动作执行。 |
| 82 | 函数体 | 将 `set(permission_config['blocked_names'])` 赋给 `blocked`。 |
| 83 | 函数体 | 将 `[]` 赋给 `found`。 |
| 84 | 函数体 | 定义嵌套函数 `fail`；定义本身不执行函数体。 |
| 86 | 函数体 | 遍历 `os.walk(root, followlinks=False, onerror=fail)`，每次绑定 `(directory, directories, files)`。 |
| 87 | 函数体 / 循环每次 | 遍历 `list(directories)`，每次绑定 `name`。 |
| 88 | 函数体 / 循环每次 / 循环每次 | 将 `Path(directory) / name` 赋给 `item`。 |
| 89 | 函数体 / 循环每次 / 循环每次 | 条件 `name in blocked`：真时执行body，假时进入else/后续。 |
| 90 | 函数体 / 循环每次 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`directories.remove(name)`。 |
| 91 | 函数体 / 循环每次 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`found.append((item.relative_to(root), True))`。 |
| 92 | 函数体 / 循环每次 / 循环每次 / 条件为假/elif | 条件 `item.is_symlink()`：真时执行body，假时进入else/后续。 |
| 93 | 函数体 / 循环每次 / 循环每次 / 条件为假/elif / 条件为真 | 计算表达式/调用产生动作：`directories.remove(name)`。 |
| 94 | 函数体 / 循环每次 | 遍历 `files`，每次绑定 `name`。 |
| 95 | 函数体 / 循环每次 / 循环每次 | 条件 `name in blocked`：真时执行body，假时进入else/后续。 |
| 96 | 函数体 / 循环每次 / 循环每次 / 条件为真 | 将 `Path(directory) / name` 赋给 `item`。 |
| 97 | 函数体 / 循环每次 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`found.append((item.relative_to(root), False))`。 |
| 98 | 函数体 | 返回 `found`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L98：`found`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="protected-project-paths-fail"></a>
## protected_project_paths.fail

os.walk访问错误时重新抛出，避免静默遗漏私有遮蔽目标。

```python
def fail(error)
```

位置：[84行](../../../permissions.py#L84) 至快照 85 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `error` | `未显式注解` | 捕获的异常或错误字段，返回前可只保留类型以避免泄露。 |

**调用表达式（静态提取，不含内层独立函数体）**：无直接调用。

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 85 | 函数体 | 抛出 `error`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L15。
- 推导式/生成器表达式：循环建容器或逐个产生：L24。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """共享路径边界与授权策略；模型参数不能改变策略或调用来源。"""
0002 | import os
0003 | from pathlib import Path
0004 | 
0005 | from config import permission_config
0006 | from tool_display import safe_text
0007 | 
0008 | 
0009 | PROJECT_ROOT = Path(__file__).resolve().parent
0010 | 
0011 | 
0012 | def resolve_project_path(path):
0013 |     if not isinstance(path, str) or not path or "\x00" in path:
0014 |         return {"ok": False, "error": "路径必须是非空字符串，且不能包含空字符"}
0015 |     try:
0016 |         candidate = Path(path)
0017 |         if not candidate.is_absolute():
0018 |             candidate = PROJECT_ROOT / candidate
0019 |         resolved_path = candidate.resolve()
0020 |         if not resolved_path.is_relative_to(PROJECT_ROOT):
0021 |             return {"ok": False, "error": "禁止访问项目目录之外的文件"}
0022 |         # 对真实目标检查，避免通过项目内符号链接读取受保护内容。
0023 |         relative = resolved_path.relative_to(PROJECT_ROOT)
0024 |         if any(part in permission_config["blocked_names"] for part in relative.parts):
0025 |             return {"ok": False, "error": "禁止访问项目内部环境、控制配置或私有记录"}
0026 |         return {"ok": True, "path": str(resolved_path)}
0027 |     except (OSError, ValueError, RuntimeError):
0028 |         return {"ok": False, "error": "无法解析文件路径"}
0029 | 
0030 | 
0031 | def confirm_tool(name, path, details=""):
0032 |     from terminal_input import request_confirmation
0033 |     prompt = "请求调用 " + name + "\n目标: " + path
0034 |     if details:
0035 |         prompt += "\n参数: " + details
0036 |     return request_confirmation(safe_text(prompt))
0037 | 
0038 | 
0039 | def authorize_tool(name, operation, path, source="model", details="", *, prepared=None):
0040 |     # 缺少策略或未知来源一律拒绝，不默认放行新工具。
0041 |     policy_result = check_tool_policy(operation, source)
0042 |     if not policy_result["ok"]:
0043 |         return policy_result
0044 |     checked = resolve_project_path(path)
0045 |     if not checked["ok"]:
0046 |         return checked
0047 |     from approval import authorize_action
0048 |     approved = authorize_action(name, operation, checked['path'], source, details, prepared=prepared)
0049 |     if not approved['ok']:
0050 |         return approved
0051 |     rechecked = resolve_project_path(path)
0052 |     if not rechecked["ok"]:
0053 |         return rechecked
0054 |     if rechecked["path"] != checked["path"]:
0055 |         return {"ok": False, "error": "确认期间路径目标已变化，请重新提交"}
0056 |     return rechecked
0057 | 
0058 | 
0059 | def check_tool_policy(operation, source):
0060 |     policy = permission_config["confirmation"].get(source)
0061 |     if not isinstance(policy, dict) or operation not in policy:
0062 |         return {"ok": False, "error": "缺少有效的工具权限策略"}
0063 |     if type(policy[operation]) is not bool:
0064 |         return {"ok": False, "error": "确认策略必须是布尔值"}
0065 |     return {"ok": True, "requires_confirmation": policy[operation]}
0066 | 
0067 | 
0068 | def authorize_external_tool(name, target, source="model", details=""):
0069 |     """外部服务采用 execute 策略；其路径参数不能假装受本地文件边界保护。"""
0070 |     policy = check_tool_policy("execute", source)
0071 |     if not policy["ok"]:
0072 |         return policy
0073 |     from approval import record_decision
0074 |     accepted = not policy['requires_confirmation'] or confirm_tool(name, target, details)
0075 |     decision = record_decision(name, 'human' if policy['requires_confirmation'] else 'rule',
0076 |                               'allow' if accepted else 'deny', 'external_service')
0077 |     return {'ok': accepted, 'approval': [decision], **({} if accepted else {'error': '用户拒绝执行外部服务'})}
0078 | 
0079 | 
0080 | def protected_project_paths(root):
0081 |     """找到需要在沙箱中遮蔽的路径，使用同一拒绝名单并跳过受保护目录。"""
0082 |     blocked = set(permission_config["blocked_names"])
0083 |     found = []
0084 |     def fail(error):
0085 |         raise error
0086 |     for directory, directories, files in os.walk(root, followlinks=False, onerror=fail):
0087 |         for name in list(directories):
0088 |             item = Path(directory) / name
0089 |             if name in blocked:
0090 |                 directories.remove(name)
0091 |                 found.append((item.relative_to(root), True))
0092 |             elif item.is_symlink():
0093 |                 directories.remove(name)
0094 |         for name in files:
0095 |             if name in blocked:
0096 |                 item = Path(directory) / name
0097 |                 found.append((item.relative_to(root), False))
0098 |     return found
```
