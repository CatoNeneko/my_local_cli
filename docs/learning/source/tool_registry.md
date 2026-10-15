# tool_registry.py：源码导读

工具声明与handler/prepare绑定的唯一内置注册位置，支持动态MCP登记。

先读专题：[03-tools.md](../03-tools.md)。

实际源码：[tool_registry.py](../../../tool_registry.py)。

快照 SHA256：`e78771edcf02ec151837555a6f6c44aafdaaca5387f138ea8938b24cbf28dc34`；120 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `from copy import deepcopy` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `from file_tools import list_files, read_file, search_file` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `from patches import apply_prepared_edit, prepare_edit` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `from sandbox import execute_prepared_tests, prepare_tests` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `from skill_files import apply_prepared_skill, prepare_create_skill` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `from project_search import search_project` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 9 | `from new_files import apply_prepared_file, prepare_create_file` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 31 | `TOOL_REGISTRY = {'create_file': tool_spec('新建项目内普通 UTF-8 文件，提供完整内容。展示 diff 并确认后创建父目录和文件；拒绝覆盖已有目标。', 'write', {'path': string_parameter('新文件路径', 1), 'new_content': string_…（见完整源码）` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 87 | `from process_tasks import prepare_pty, start_pty, start_agent, inspect_task, send_input, cancel_task` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 110 | `from process_tasks import wait_task` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 111 | `TOOL_REGISTRY['task_wait'] = tool_spec('等待任务完成，最多等待 30 秒，未结束时返回当前状态。', 'read', {'task_id': string_parameter('任务 ID', 1), 'seconds': {'type': 'integer', 'minimum': 1, 'max…（见完整源码）` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 114 | `TOOL_REGISTRY['task_wait']['kind'] = 'task'` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 116 | `from agent_proposals import apply_proposal` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 117 | `TOOL_REGISTRY['apply_agent_proposal'] = tool_spec('申请应用已完成子代理的文件建议。内层执行器会重新检查路径、展示 diff、独立审批并验证冲突；不是直接写入。', 'read', {'task_id': string_parameter('子代理任务 ID', 1), 'proposal…（见完整源码）` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 120 | `TOOL_REGISTRY['apply_agent_proposal']['kind'] = 'task'` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [string_parameter](#string-parameter) | [12](../../../tool_registry.py#L12) | 生成字符串字段schema。 |
| [tool_spec](#tool-spec) | [16](../../../tool_registry.py#L16) | 集中构造内置工具注册项。 |
| [get_tool_definitions](#get-tool-definitions) | [77](../../../tool_registry.py#L77) | 返回可发送给模型的声明深拷贝，不带Python函数对象。 |

<a id="string-parameter"></a>
## string_parameter

生成字符串字段schema。

```python
def string_parameter(description='', min_length=0)
```

位置：[12行](../../../tool_registry.py#L12) 至快照 13 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `description` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `min_length` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：无直接调用。

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 13 | 函数体 | 返回 `{'type': 'string', 'description': description, 'minLength': min_length}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L13：`{'type': 'string', 'description': description, 'minLength': min_length}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="tool-spec"></a>
## tool_spec

集中构造内置工具注册项。

```python
def tool_spec(description, operation, properties, required, handler, prepare=None, defaults=None, details='')
```

位置：[16行](../../../tool_registry.py#L16) 至快照 28 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `description` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `operation` | `未显式注解` | read/write/execute操作分类，用于权限与Hook。 |
| `properties` | `未显式注解` | JSON Schema的字段定义字典。 |
| `required` | `未显式注解` | 必须给出的参数名称列表。 |
| `handler` | `未显式注解` | 通过验证与授权后实际调用的函数对象。 |
| `prepare` | `未显式注解` | 可选准备函数引用；不直接提交副作用。 |
| `defaults` | `未显式注解` | 注册项在schema验证前补的缺省参数。 |
| `details` | `未显式注解` | 用户确认/审批展示的动作说明。 |

**调用表达式（静态提取，不含内层独立函数体）**：无直接调用。

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 17 | 函数体 | 返回 `{'description': description, 'operation': operation, 'parameters': {'type': 'object', 'properties': properties, 'required': required, 'additionalProperties': False}, 'def…（见完整源码）`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L17：`{'description': description, 'operation': operation, 'parameters': {'type': 'object', 'properties': properties, 'required': required, 'additionalProperties': False}, 'defaults': defaults or {}, 'handler': handl…（见完整源码）`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="get-tool-definitions"></a>
## get_tool_definitions

返回可发送给模型的声明深拷贝，不带Python函数对象。

```python
def get_tool_definitions()
```

位置：[77行](../../../tool_registry.py#L77) 至快照 84 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`TOOL_REGISTRY.items`、`deepcopy`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 78 | 函数体 | 返回 `[{'type': 'function', 'function': {'name': name, 'description': spec['description'], 'parameters': deepcopy(spec['parameters'])}} for name, spec in TOOL_REGISTRY.items()]`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L78：`[{'type': 'function', 'function': {'name': name, 'description': spec['description'], 'parameters': deepcopy(spec['parameters'])}} for name, spec in TOOL_REGISTRY.items()]`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- 推导式/生成器表达式：循环建容器或逐个产生：L78。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """工具参数、权限类型、准备函数和实现的唯一注册位置。"""
0002 | from copy import deepcopy
0003 | 
0004 | from file_tools import list_files, read_file, search_file
0005 | from patches import apply_prepared_edit, prepare_edit
0006 | from sandbox import execute_prepared_tests, prepare_tests
0007 | from skill_files import apply_prepared_skill, prepare_create_skill
0008 | from project_search import search_project
0009 | from new_files import apply_prepared_file, prepare_create_file
0010 | 
0011 | 
0012 | def string_parameter(description="", min_length=0):
0013 |     return {"type": "string", "description": description, "minLength": min_length}
0014 | 
0015 | 
0016 | def tool_spec(description, operation, properties, required, handler, prepare=None, defaults=None, details=""):
0017 |     return {
0018 |         "description": description,
0019 |         "operation": operation,
0020 |         "parameters": {
0021 |             "type": "object", "properties": properties,
0022 |             "required": required, "additionalProperties": False
0023 |         },
0024 |         "defaults": defaults or {},
0025 |         "handler": handler,
0026 |         "prepare": prepare,
0027 |         "details": details
0028 |     }
0029 | 
0030 | 
0031 | TOOL_REGISTRY = {
0032 |     "create_file": tool_spec(
0033 |         "新建项目内普通 UTF-8 文件，提供完整内容。展示 diff 并确认后创建父目录和文件；拒绝覆盖已有目标。",
0034 |         "write", {"path": string_parameter("新文件路径", 1), "new_content": string_parameter("完整 UTF-8 文字，允许空文件")},
0035 |         ["path", "new_content"], apply_prepared_file, prepare_create_file
0036 |     ),
0037 |     "search_project": tool_spec(
0038 |         "递归搜索项目 UTF-8 文本中的字面关键词，返回项目相对路径、行号和片段。"
0039 |         "可用 glob 如 '*.py' 筛选，跳过私有目录、依赖和符号链接；达到限制时返回部分结果和原因。",
0040 |         "read", {"path": string_parameter("搜索目录，默认 '.'", 1),
0041 |                  "keyword": string_parameter("区分大小写的字面关键词，不是正则表达式", 1),
0042 |                  "glob": string_parameter("文件匹配模式，默认 '*'", 1)},
0043 |         ["keyword"], search_project, defaults={"path": ".", "glob": "*"}
0044 |     ),
0045 |     "create_skill": tool_spec(
0046 |         "新建 skills/<名称>/SKILL.md。内容是任务流程说明，展示 diff 并确认后保存，不覆盖、不自动启用。",
0047 |         "write", {"path": string_parameter("skills/<名称>/SKILL.md", 1), "new_content": string_parameter("完整 Markdown 内容", 1)},
0048 |         ["path", "new_content"], apply_prepared_skill, prepare_create_skill
0049 |     ),
0050 |     "read_file": tool_spec(
0051 |         "读取项目内的 UTF-8 文本文件，返回内容或错误。", "read",
0052 |         {"path": string_parameter("文件路径", 1)}, ["path"], read_file
0053 |     ),
0054 |     "search_file": tool_spec(
0055 |         "在项目内文件中搜索关键词，返回匹配行及行号。", "read",
0056 |         {"path": string_parameter("文件路径", 1), "keyword": string_parameter("非空关键词", 1)},
0057 |         ["path", "keyword"], search_file
0058 |     ),
0059 |     "list_files": tool_spec(
0060 |         "列出项目目录的直接子项；根目录使用 '.'。受保护项目数据不展示。", "read",
0061 |         {"path": string_parameter("目录路径", 1)}, ["path"], list_files
0062 |     ),
0063 |     "edit_file": tool_spec(
0064 |         "修改已有 UTF-8 文件。先读取，再提供完整新内容。展示 diff 并由用户确认后写入；冲突时拒绝。",
0065 |         "write", {"path": string_parameter("文件路径", 1), "new_content": string_parameter("替换后的完整文字，不是 diff")},
0066 |         ["path", "new_content"], apply_prepared_edit, prepare_edit,
0067 |         details="确认后替换已有文件的完整内容"
0068 |     ),
0069 |     "run_tests": tool_spec(
0070 |         "在项目只读、默认禁网的 Linux 沙箱中运行 pytest；需要确认，返回退出码、输出和超时状态。",
0071 |         "execute", {"path": string_parameter("目录或 Python 测试文件，默认 '.'", 1)},
0072 |         [], execute_prepared_tests, prepare_tests, defaults={"path": "."}
0073 |     )
0074 | }
0075 | 
0076 | 
0077 | def get_tool_definitions():
0078 |     return [
0079 |         {"type": "function", "function": {
0080 |             "name": name, "description": spec["description"],
0081 |             "parameters": deepcopy(spec["parameters"])
0082 |         }}
0083 |         for name, spec in TOOL_REGISTRY.items()
0084 |     ]
0085 | 
0086 | 
0087 | from process_tasks import prepare_pty, start_pty, start_agent, inspect_task, send_input, cancel_task
0088 | 
0089 | TOOL_REGISTRY.update({
0090 |     'start_pty': tool_spec('启动只读、禁网 Linux 沙箱 PTY 命令，返回任务 ID；支持交互输入，退出 CLI 自动清理。',
0091 |         'execute', {'path': string_parameter('工作目录', 1),
0092 |                     'argv': {'type': 'array', 'items': {'type': 'string', 'minLength': 1, 'maxLength': 4096}, 'minItems': 1, 'maxItems': 64},
0093 |                     'timeout': {'type': 'integer', 'minimum': 1, 'maximum': 300}},
0094 |         ['argv'], start_pty, prepare_pty, defaults={'path': '.', 'timeout': 120}),
0095 |     'spawn_agent': tool_spec('启动独立只读子代理分析任务；可并行多个任务，使用 task_status 获取结果。不会共享聊天或修改文件。',
0096 |         'execute', {'path': string_parameter('关注目录', 1), 'task': {'type': 'string', 'minLength': 1, 'maxLength': 16000}},
0097 |         ['task'], start_agent, defaults={'path': '.'}),
0098 |     'task_status': tool_spec('查看当前 CLI 任务状态、结果及新增输出；offset 是字节偏移。',
0099 |         'read', {'task_id': string_parameter('任务 ID', 1), 'offset': {'type': 'integer', 'minimum': 0}},
0100 |         ['task_id'], inspect_task, defaults={'offset': 0}),
0101 |     'task_input': tool_spec('向 PTY 任务发送文字；换行需要包含在 text 中。需要确认。',
0102 |         'execute', {'task_id': string_parameter('任务 ID', 1), 'text': {'type': 'string', 'maxLength': 4096}},
0103 |         ['task_id', 'text'], send_input),
0104 |     'task_cancel': tool_spec('终止任务进程组并清理后代，需要确认。',
0105 |         'execute', {'task_id': string_parameter('任务 ID', 1)}, ['task_id'], cancel_task)
0106 | })
0107 | for _name in ('task_status', 'task_input', 'task_cancel'):
0108 |     TOOL_REGISTRY[_name]['kind'] = 'task'
0109 | 
0110 | from process_tasks import wait_task
0111 | TOOL_REGISTRY['task_wait'] = tool_spec('等待任务完成，最多等待 30 秒，未结束时返回当前状态。',
0112 |     'read', {'task_id': string_parameter('任务 ID', 1), 'seconds': {'type': 'integer', 'minimum': 1, 'maximum': 30}},
0113 |     ['task_id'], wait_task, defaults={'seconds': 10})
0114 | TOOL_REGISTRY['task_wait']['kind'] = 'task'
0115 | 
0116 | from agent_proposals import apply_proposal
0117 | TOOL_REGISTRY['apply_agent_proposal'] = tool_spec('申请应用已完成子代理的文件建议。内层执行器会重新检查路径、展示 diff、独立审批并验证冲突；不是直接写入。',
0118 |     'read', {'task_id': string_parameter('子代理任务 ID', 1), 'proposal_id': string_parameter('建议 ID', 1)},
0119 |     ['task_id', 'proposal_id'], apply_proposal)
0120 | TOOL_REGISTRY['apply_agent_proposal']['kind'] = 'task'
```
