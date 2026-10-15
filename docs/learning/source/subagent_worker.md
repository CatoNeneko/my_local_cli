# subagent_worker.py：源码导读

独立Python子进程入口，四种只读工具加两种暂存建议，无父聊天/MCP/再次派生。

先读专题：[06-processes.md](../06-processes.md)。

实际源码：[subagent_worker.py](../../../subagent_worker.py)。

快照 SHA256：`4ceacc00eaee4de2e44716726a78a8b53e7ae2de3e6340b5f79cb62d21a2116e`；54 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import contextlib` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `import sys` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [main](#main) | [7](../../../subagent_worker.py#L7) | 读stdin payload，限制工具集合，独立消息循环，返回reply与暂存建议。 |

<a id="main"></a>
## main

读stdin payload，限制工具集合，独立消息循环，返回reply与暂存建议。

```python
def main()
```

位置：[7行](../../../subagent_worker.py#L7) 至快照 46 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`call.get`、`contextlib.redirect_stdout`、`execute_tool`、`function.get`、`json.dumps`、`json.loads`、`len`、`list`、`message.get`、`messages.append`、`min`、`model_config.update`、`range`、`request_message`、`string_parameter`、`sys.stdin.buffer.read`、`tool_spec`、`use_workspace`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 8 | `payload` | `json.loads(sys.stdin.buffer.read(262145))` | 传给子进程/独立审查/摘要请求的结构化数据快照。 |
| 14 | `allowed` | `{'read_file', 'list_files', 'search_file', 'search_project'}` | 通过边界校验的子目录集合，或是否许可的布尔值。 |
| 21 | `TOOL_REGISTRY[name]` | `tool_spec('暂存文件修改建议，不写入；必须提供完整文件内容，由父代理审批后应用。', 'read', {'path': string_parameter('项目文件路径', 1), 'new_content': {'type': 'string', …（见完整源码）` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 25 | `messages` | `list(payload['instructions']) + [{'role': 'system', 'content': '你是只读子代理。独立完成指定分析并提供文件路径和证据；你不能直接修改文件或启动其他代理；需要修改时使用 propose_edit /…（见完整源码）` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |
| 28 | `calls` | `0` | 工具调用计数或按index缓存的调用集合；来源表达式决定类型。 |
| 32 | `message` | `request_message(messages, include_context=False)` | 单条聊天/协议消息字典；角色和字段随当前分支而定。 |
| 40 | `function` | `call['function']` | 模型工具调用的function子字典，含name和arguments。 |
| 41 | `result` | `execute_tool(function['name'], function.get('arguments', {}))` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 42 | `item` | `{'role': 'tool', 'tool_name': function['name'], 'content': json.dumps(result, ensure_ascii=False)}` | 遍历中的一项：字段、文件、消息或工具定义，类型取决于iter。 |
| 44 | `item['tool_call_id']` | `call['id']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 8 | 函数体 | 将 `json.loads(sys.stdin.buffer.read(262145))` 赋给 `payload`。 |
| 9 | 函数体 | 在此处导入依赖：`from config import model_config, agent_config`；局部导入可延迟加载或避免循环。 |
| 10 | 函数体 | 在此处导入依赖：`from workspace import use_workspace`；局部导入可延迟加载或避免循环。 |
| 11 | 函数体 | 在此处导入依赖：`from tool_registry import TOOL_REGISTRY`；局部导入可延迟加载或避免循环。 |
| 12 | 函数体 | 在此处导入依赖：`from model_client import request_message`；局部导入可延迟加载或避免循环。 |
| 13 | 函数体 | 在此处导入依赖：`from tool_runtime import execute_tool`；局部导入可延迟加载或避免循环。 |
| 14 | 函数体 | 将 `{'read_file', 'list_files', 'search_file', 'search_project'}` 赋给 `allowed`。 |
| 15 | 函数体 | 遍历 `list(TOOL_REGISTRY)`，每次绑定 `name`。 |
| 16 | 函数体 / 循环每次 | 条件 `name not in allowed`：真时执行body，假时进入else/后续。 |
| 17 | 函数体 / 循环每次 / 条件为真 | 删除目标引用/容器项：`del TOOL_REGISTRY[name]`。 |
| 18 | 函数体 | 在此处导入依赖：`from agent_proposals import PROPOSALS, propose_edit, propose_file`；局部导入可延迟加载或避免循环。 |
| 19 | 函数体 | 在此处导入依赖：`from tool_registry import tool_spec, string_parameter`；局部导入可延迟加载或避免循环。 |
| 20 | 函数体 | 遍历 `(('propose_edit', propose_edit), ('propose_file', propose_file))`，每次绑定 `(name, handler)`。 |
| 21 | 函数体 / 循环每次 | 将 `tool_spec('暂存文件修改建议，不写入；必须提供完整文件内容，由父代理审批后应用。', 'read', {'path': string_parameter('项目文件路径', 1), 'new_content': {'type': 'string', 'maxLength': 16000}}, ['path', 'new_cont…（见完整源码）` 赋给 `TOOL_REGISTRY[name]`。 |
| 24 | 函数体 | 计算表达式/调用产生动作：`model_config.update(payload['model_config'])`。 |
| 25 | 函数体 | 将 `list(payload['instructions']) + [{'role': 'system', 'content': '你是只读子代理。独立完成指定分析并提供文件路径和证据；你不能直接修改文件或启动其他代理；需要修改时使用 propose_edit / propose_file 提出建议。'}, {'role': 'user', …（见完整源码）` 赋给 `messages`。 |
| 28 | 函数体 | 将 `0` 赋给 `calls`。 |
| 29 | 函数体 | 进入资源/状态范围：`use_workspace(payload['workspace'])`, `contextlib.redirect_stdout(sys.stderr)`；退出执行清理。 |
| 31 | 函数体 / with范围 | 遍历 `range(min(8, payload['agent_config']['max_rounds']))`，每次绑定 `_`。 |
| 32 | 函数体 / with范围 / 循环每次 | 将 `request_message(messages, include_context=False)` 赋给 `message`。 |
| 33 | 函数体 / with范围 / 循环每次 | 条件 `not message.get('tool_calls')`：真时执行body，假时进入else/后续。 |
| 34 | 函数体 / with范围 / 循环每次 / 条件为真 | 返回 `{'ok': True, 'reply': message['content'][:4000], 'reply_truncated': len(message['content']) > 4000, 'tool_calls': calls, 'proposals': list(PROPOSALS)}`，结束当前函数；具体分支见完整源码。 |
| 35 | 函数体 / with范围 / 循环每次 | 计算表达式/调用产生动作：`messages.append(message)`。 |
| 36 | 函数体 / with范围 / 循环每次 | 遍历 `message['tool_calls']`，每次绑定 `call`。 |
| 37 | 函数体 / with范围 / 循环每次 / 循环每次 | 更新已有变量：`calls += 1`。 |
| 38 | 函数体 / with范围 / 循环每次 / 循环每次 | 条件 `calls > min(12, payload['agent_config']['max_tool_calls'])`：真时执行body，假时进入else/后续。 |
| 39 | 函数体 / with范围 / 循环每次 / 循环每次 / 条件为真 | 返回 `{'ok': False, 'error': '子代理工具预算耗尽'}`，结束当前函数；具体分支见完整源码。 |
| 40 | 函数体 / with范围 / 循环每次 / 循环每次 | 将 `call['function']` 赋给 `function`。 |
| 41 | 函数体 / with范围 / 循环每次 / 循环每次 | 将 `execute_tool(function['name'], function.get('arguments', {}))` 赋给 `result`。 |
| 42 | 函数体 / with范围 / 循环每次 / 循环每次 | 将 `{'role': 'tool', 'tool_name': function['name'], 'content': json.dumps(result, ensure_ascii=False)}` 赋给 `item`。 |
| 43 | 函数体 / with范围 / 循环每次 / 循环每次 | 条件 `call.get('id')`：真时执行body，假时进入else/后续。 |
| 44 | 函数体 / with范围 / 循环每次 / 循环每次 / 条件为真 | 将 `call['id']` 赋给 `item['tool_call_id']`。 |
| 45 | 函数体 / with范围 / 循环每次 / 循环每次 | 计算表达式/调用产生动作：`messages.append(item)`。 |
| 46 | 函数体 | 返回 `{'ok': False, 'error': '子代理轮次预算耗尽'}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L34：`{'ok': True, 'reply': message['content'][:4000], 'reply_truncated': len(message['content']) > 4000, 'tool_calls': calls, 'proposals': list(PROPOSALS)}`。
- L39：`{'ok': False, 'error': '子代理工具预算耗尽'}`。
- L46：`{'ok': False, 'error': '子代理轮次预算耗尽'}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- with/yield：资源/状态生命周期或逐个生成：L29。
- try/except/finally：异常与保证清理：L50。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """可信子代理入口：独立配置、独立上下文，仅允许四种只读项目工具。"""
0002 | import contextlib
0003 | import json
0004 | import sys
0005 | 
0006 | 
0007 | def main():
0008 |     payload = json.loads(sys.stdin.buffer.read(262145))
0009 |     from config import model_config, agent_config
0010 |     from workspace import use_workspace
0011 |     from tool_registry import TOOL_REGISTRY
0012 |     from model_client import request_message
0013 |     from tool_runtime import execute_tool
0014 |     allowed = {'read_file', 'list_files', 'search_file', 'search_project'}
0015 |     for name in list(TOOL_REGISTRY):
0016 |         if name not in allowed:
0017 |             del TOOL_REGISTRY[name]
0018 |     from agent_proposals import PROPOSALS, propose_edit, propose_file
0019 |     from tool_registry import tool_spec, string_parameter
0020 |     for name, handler in (('propose_edit', propose_edit), ('propose_file', propose_file)):
0021 |         TOOL_REGISTRY[name] = tool_spec('暂存文件修改建议，不写入；必须提供完整文件内容，由父代理审批后应用。',
0022 |             'read', {'path': string_parameter('项目文件路径', 1), 'new_content': {'type': 'string', 'maxLength': 16000}},
0023 |             ['path', 'new_content'], handler)
0024 |     model_config.update(payload['model_config'])
0025 |     messages = list(payload['instructions']) + [
0026 |         {'role': 'system', 'content': '你是只读子代理。独立完成指定分析并提供文件路径和证据；你不能直接修改文件或启动其他代理；需要修改时使用 propose_edit / propose_file 提出建议。'},
0027 |         {'role': 'user', 'content': '关注目录: ' + payload['path'] + '\n任务: ' + payload['task']}]
0028 |     calls = 0
0029 |     with use_workspace(payload['workspace']), contextlib.redirect_stdout(sys.stderr):
0030 |         # 子代理不访问父会话，审计仍通过共享执行入口记录。
0031 |         for _ in range(min(8, payload['agent_config']['max_rounds'])):
0032 |             message = request_message(messages, include_context=False)
0033 |             if not message.get('tool_calls'):
0034 |                 return {'ok': True, 'reply': message['content'][:4000], 'reply_truncated': len(message['content']) > 4000, 'tool_calls': calls, 'proposals': list(PROPOSALS)}
0035 |             messages.append(message)
0036 |             for call in message['tool_calls']:
0037 |                 calls += 1
0038 |                 if calls > min(12, payload['agent_config']['max_tool_calls']):
0039 |                     return {'ok': False, 'error': '子代理工具预算耗尽'}
0040 |                 function = call['function']
0041 |                 result = execute_tool(function['name'], function.get('arguments', {}))
0042 |                 item = {'role': 'tool', 'tool_name': function['name'], 'content': json.dumps(result, ensure_ascii=False)}
0043 |                 if call.get('id'):
0044 |                     item['tool_call_id'] = call['id']
0045 |                 messages.append(item)
0046 |     return {'ok': False, 'error': '子代理轮次预算耗尽'}
0047 | 
0048 | 
0049 | if __name__ == '__main__':
0050 |     try:
0051 |         result = main()
0052 |     except Exception as error:
0053 |         result = {'ok': False, 'error': '子代理失败: ' + type(error).__name__}
0054 |     print(json.dumps(result, ensure_ascii=False))
```
