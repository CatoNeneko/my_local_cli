# scripts/compaction_acceptance.py：源码导读

手动/自动摘要与重启回忆固定事实；种子历史是构造的，模型回复是真的。

先读专题：[08-verification.md](../08-verification.md)。

实际源码：[scripts/compaction_acceptance.py](../../../scripts/compaction_acceptance.py)。

快照 SHA256：`f0496454688e8ae0a36d0282a9e091a288677e884fa888ebee83b3b1864512a7`；80 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `import sys` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `import tempfile` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `ROOT = Path(__file__).resolve().parents[1]` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 9 | `from compaction import compact_messages, context_view` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 10 | `from config import context_config` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 11 | `import history` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 12 | `from model_client import request_message` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 13 | `from sessions import SessionManager` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 14 | `from workspace import use_workspace` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 16 | `MARKER = 'COMPACT_CEDAR_739'` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [seed](#seed) | [19](../../../scripts/compaction_acceptance.py#L19) | 构造固定多轮示例历史，首轮植入记忆暗号与不能改测试的约束。 |
| [ask](#ask) | [28](../../../scripts/compaction_acceptance.py#L28) | 追加回忆问题，请求真实模型无工具回答，保存并返回回复。 |
| [main](#main) | [40](../../../scripts/compaction_acceptance.py#L40) | 固定种子分别验证手动摘要、重命名重启、自动触发及旧事实回忆，保存真实报告。 |

<a id="seed"></a>
## seed

构造固定多轮示例历史，首轮植入记忆暗号与不能改测试的约束。

```python
def seed()
```

位置：[19行](../../../scripts/compaction_acceptance.py#L19) 至快照 25 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`range`、`result.extend`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 20 | `result` | `[]` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 22 | `text` | `'项目记忆暗号是 ' + MARKER + '。用户要求始终不能修改 test_calc.py。' if number == 0 else f'继续讨论项目第 {number} 阶段；暂不执行操作。'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 20 | 函数体 | 将 `[]` 赋给 `result`。 |
| 21 | 函数体 | 遍历 `range(5)`，每次绑定 `number`。 |
| 22 | 函数体 / 循环每次 | 将 `'项目记忆暗号是 ' + MARKER + '。用户要求始终不能修改 test_calc.py。' if number == 0 else f'继续讨论项目第 {number} 阶段；暂不执行操作。'` 赋给 `text`。 |
| 24 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`result.extend([{'role': 'user', 'content': text}, {'role': 'assistant', 'content': '已记录讨论。'}])`。 |
| 25 | 函数体 | 返回 `result`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L25：`result`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="ask"></a>
## ask

追加回忆问题，请求真实模型无工具回答，保存并返回回复。

```python
def ask(messages)
```

位置：[28行](../../../scripts/compaction_acceptance.py#L28) 至快照 37 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `messages` | `未显式注解` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ValueError`、`history.append_message`、`messages.append`、`reply.get`、`request_message`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 29 | `question` | `{'role': 'user', 'content': '只用一句话回答：最早的项目记忆暗号是什么，用户要求不能修改哪个文件？不要调用工具。'}` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 32 | `reply` | `request_message(messages)` | 模型最终文字或明确终止说明。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 29 | 函数体 | 将 `{'role': 'user', 'content': '只用一句话回答：最早的项目记忆暗号是什么，用户要求不能修改哪个文件？不要调用工具。'}` 赋给 `question`。 |
| 30 | 函数体 | 计算表达式/调用产生动作：`history.append_message(question)`。 |
| 31 | 函数体 | 计算表达式/调用产生动作：`messages.append(question)`。 |
| 32 | 函数体 | 将 `request_message(messages)` 赋给 `reply`。 |
| 33 | 函数体 | 条件 `reply.get('tool_calls')`：真时执行body，假时进入else/后续。 |
| 34 | 函数体 / 条件为真 | 抛出 `ValueError('验证要求仅返回回答，不能调用工具')`。 |
| 35 | 函数体 | 计算表达式/调用产生动作：`history.append_message({'role': 'assistant', 'content': reply['content']})`。 |
| 36 | 函数体 | 计算表达式/调用产生动作：`messages.append({'role': 'assistant', 'content': reply['content']})`。 |
| 37 | 函数体 | 返回 `reply['content']`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L37：`reply['content']`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="main"></a>
## main

固定种子分别验证手动摘要、重命名重启、自动触发及旧事实回忆，保存真实报告。

```python
def main()
```

位置：[40行](../../../scripts/compaction_acceptance.py#L40) 至快照 76 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`SessionManager`、`SystemExit`、`all`、`ask`、`bool`、`checks.values`、`compact_messages`、`context_view`、`history.HISTORY_PATH.read_bytes`、`history.HISTORY_PATH.read_bytes().startswith`、`history.append_messages`、`json.dumps`、`manager.rename`、`manager.switch`、`path.parent.mkdir`、`path.write_text`、`print`、`restarted.switch`、`seed`、`str`、`tempfile.mkdtemp`、`use_workspace`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 41 | `workspace` | `Path(tempfile.mkdtemp(prefix='cli-compaction-acceptance-'))` | 目标项目目录，不是助手安装环境。 |
| 42 | `(checks, replies)` | `({}, {})` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 44 | `manager` | `SessionManager()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 46 | `messages` | `seed()` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |
| 48 | `original_bytes` | `history.HISTORY_PATH.read_bytes()` | 审批前旧文件字节，用于写前冲突检查。 |
| 49 | `result` | `compact_messages(messages)` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 50 | `checks['manual_saved']` | `result['ok'] and result['changed']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 51 | `checks['raw_history_preserved']` | `history.HISTORY_PATH.read_bytes().startswith(original_bytes)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 52 | `replies['manual']` | `ask(messages)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 53 | `checks['manual_recalls_old_fact']` | `MARKER in replies['manual'] and 'test_calc.py' in replies['manual']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 56 | `restarted` | `SessionManager()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 57 | `restored` | `restarted.switch('renamed')['messages']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 58 | `checks['restart_summary_restored']` | `bool(context_view(restored)['summary'])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 59 | `replies['restart']` | `ask(restored)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 60 | `checks['restart_recalls_old_fact']` | `MARKER in replies['restart'] and 'test_calc.py' in replies['restart']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 62 | `messages` | `seed()` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |
| 64 | `context_config['auto_compact']` | `True` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 65 | `context_config['max_history_turns']` | `3` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 66 | `replies['automatic']` | `ask(messages)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 67 | `checks['automatic_saved']` | `bool(context_view(messages)['summary'])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 68 | `checks['automatic_recalls_old_fact']` | `MARKER in replies['automatic'] and 'test_calc.py' in replies['automatic']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 69 | `report` | `{'workspace': str(workspace), 'checks': checks, 'replies': replies, 'note': '原历史由固定示例构造；摘要及后续回答由真实模型生成。'}` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 71 | `path` | `ROOT / 'artifacts/compaction/real_acceptance.json'` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 41 | 函数体 | 将 `Path(tempfile.mkdtemp(prefix='cli-compaction-acceptance-'))` 赋给 `workspace`。 |
| 42 | 函数体 | 将 `({}, {})` 赋给 `(checks, replies)`。 |
| 43 | 函数体 | 进入资源/状态范围：`use_workspace(workspace)`；退出执行清理。 |
| 44 | 函数体 / with范围 | 将 `SessionManager()` 赋给 `manager`。 |
| 45 | 函数体 / with范围 | 计算表达式/调用产生动作：`manager.switch('manual')`。 |
| 46 | 函数体 / with范围 | 将 `seed()` 赋给 `messages`。 |
| 47 | 函数体 / with范围 | 计算表达式/调用产生动作：`history.append_messages(messages)`。 |
| 48 | 函数体 / with范围 | 将 `history.HISTORY_PATH.read_bytes()` 赋给 `original_bytes`。 |
| 49 | 函数体 / with范围 | 将 `compact_messages(messages)` 赋给 `result`。 |
| 50 | 函数体 / with范围 | 将 `result['ok'] and result['changed']` 赋给 `checks['manual_saved']`。 |
| 51 | 函数体 / with范围 | 将 `history.HISTORY_PATH.read_bytes().startswith(original_bytes)` 赋给 `checks['raw_history_preserved']`。 |
| 52 | 函数体 / with范围 | 将 `ask(messages)` 赋给 `replies['manual']`。 |
| 53 | 函数体 / with范围 | 将 `MARKER in replies['manual'] and 'test_calc.py' in replies['manual']` 赋给 `checks['manual_recalls_old_fact']`。 |
| 54 | 函数体 / with范围 | 断言条件必须为真，否则测试/验证失败：`manager.rename('renamed')['ok']`。 |
| 55 | 函数体 | 进入资源/状态范围：`use_workspace(workspace)`；退出执行清理。 |
| 56 | 函数体 / with范围 | 将 `SessionManager()` 赋给 `restarted`。 |
| 57 | 函数体 / with范围 | 将 `restarted.switch('renamed')['messages']` 赋给 `restored`。 |
| 58 | 函数体 / with范围 | 将 `bool(context_view(restored)['summary'])` 赋给 `checks['restart_summary_restored']`。 |
| 59 | 函数体 / with范围 | 将 `ask(restored)` 赋给 `replies['restart']`。 |
| 60 | 函数体 / with范围 | 将 `MARKER in replies['restart'] and 'test_calc.py' in replies['restart']` 赋给 `checks['restart_recalls_old_fact']`。 |
| 61 | 函数体 / with范围 | 断言条件必须为真，否则测试/验证失败：`restarted.switch('automatic')['ok']`。 |
| 62 | 函数体 / with范围 | 将 `seed()` 赋给 `messages`。 |
| 63 | 函数体 / with范围 | 计算表达式/调用产生动作：`history.append_messages(messages)`。 |
| 64 | 函数体 / with范围 | 将 `True` 赋给 `context_config['auto_compact']`。 |
| 65 | 函数体 / with范围 | 将 `3` 赋给 `context_config['max_history_turns']`。 |
| 66 | 函数体 / with范围 | 将 `ask(messages)` 赋给 `replies['automatic']`。 |
| 67 | 函数体 / with范围 | 将 `bool(context_view(messages)['summary'])` 赋给 `checks['automatic_saved']`。 |
| 68 | 函数体 / with范围 | 将 `MARKER in replies['automatic'] and 'test_calc.py' in replies['automatic']` 赋给 `checks['automatic_recalls_old_fact']`。 |
| 69 | 函数体 | 将 `{'workspace': str(workspace), 'checks': checks, 'replies': replies, 'note': '原历史由固定示例构造；摘要及后续回答由真实模型生成。'}` 赋给 `report`。 |
| 71 | 函数体 | 将 `ROOT / 'artifacts/compaction/real_acceptance.json'` 赋给 `path`。 |
| 72 | 函数体 | 计算表达式/调用产生动作：`path.parent.mkdir(parents=True, exist_ok=True)`。 |
| 73 | 函数体 | 计算表达式/调用产生动作：`path.write_text(json.dumps(report, ensure_ascii=False, indent=2))`。 |
| 74 | 函数体 | 计算表达式/调用产生动作：`print(json.dumps(report, ensure_ascii=False, indent=2))`。 |
| 75 | 函数体 | 条件 `not all(checks.values())`：真时执行body，假时进入else/后续。 |
| 76 | 函数体 / 条件为真 | 抛出 `SystemExit(1)`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- with/yield：资源/状态生命周期或逐个生成：L43, L55。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """固定示例历史的真实模型摘要、恢复与自动触发验证；不会调用文件修改工具。"""
0002 | import json
0003 | from pathlib import Path
0004 | import sys
0005 | import tempfile
0006 | 
0007 | ROOT = Path(__file__).resolve().parents[1]
0008 | sys.path.insert(0, str(ROOT))
0009 | from compaction import compact_messages, context_view
0010 | from config import context_config
0011 | import history
0012 | from model_client import request_message
0013 | from sessions import SessionManager
0014 | from workspace import use_workspace
0015 | 
0016 | MARKER = 'COMPACT_CEDAR_739'
0017 | 
0018 | 
0019 | def seed():
0020 |     result = []
0021 |     for number in range(5):
0022 |         text = ('项目记忆暗号是 ' + MARKER + '。用户要求始终不能修改 test_calc.py。' if number == 0
0023 |                 else f'继续讨论项目第 {number} 阶段；暂不执行操作。')
0024 |         result.extend([{'role': 'user', 'content': text}, {'role': 'assistant', 'content': '已记录讨论。'}])
0025 |     return result
0026 | 
0027 | 
0028 | def ask(messages):
0029 |     question = {'role': 'user', 'content': '只用一句话回答：最早的项目记忆暗号是什么，用户要求不能修改哪个文件？不要调用工具。'}
0030 |     history.append_message(question)
0031 |     messages.append(question)
0032 |     reply = request_message(messages)
0033 |     if reply.get('tool_calls'):
0034 |         raise ValueError('验证要求仅返回回答，不能调用工具')
0035 |     history.append_message({'role': 'assistant', 'content': reply['content']})
0036 |     messages.append({'role': 'assistant', 'content': reply['content']})
0037 |     return reply['content']
0038 | 
0039 | 
0040 | def main():
0041 |     workspace = Path(tempfile.mkdtemp(prefix='cli-compaction-acceptance-'))
0042 |     checks, replies = {}, {}
0043 |     with use_workspace(workspace):
0044 |         manager = SessionManager()
0045 |         manager.switch('manual')
0046 |         messages = seed()
0047 |         history.append_messages(messages)
0048 |         original_bytes = history.HISTORY_PATH.read_bytes()
0049 |         result = compact_messages(messages)
0050 |         checks['manual_saved'] = result['ok'] and result['changed']
0051 |         checks['raw_history_preserved'] = history.HISTORY_PATH.read_bytes().startswith(original_bytes)
0052 |         replies['manual'] = ask(messages)
0053 |         checks['manual_recalls_old_fact'] = MARKER in replies['manual'] and 'test_calc.py' in replies['manual']
0054 |         assert manager.rename('renamed')['ok']
0055 |     with use_workspace(workspace):
0056 |         restarted = SessionManager()
0057 |         restored = restarted.switch('renamed')['messages']
0058 |         checks['restart_summary_restored'] = bool(context_view(restored)['summary'])
0059 |         replies['restart'] = ask(restored)
0060 |         checks['restart_recalls_old_fact'] = MARKER in replies['restart'] and 'test_calc.py' in replies['restart']
0061 |         assert restarted.switch('automatic')['ok']
0062 |         messages = seed()
0063 |         history.append_messages(messages)
0064 |         context_config['auto_compact'] = True
0065 |         context_config['max_history_turns'] = 3
0066 |         replies['automatic'] = ask(messages)
0067 |         checks['automatic_saved'] = bool(context_view(messages)['summary'])
0068 |         checks['automatic_recalls_old_fact'] = MARKER in replies['automatic'] and 'test_calc.py' in replies['automatic']
0069 |     report = {'workspace': str(workspace), 'checks': checks, 'replies': replies,
0070 |               'note': '原历史由固定示例构造；摘要及后续回答由真实模型生成。'}
0071 |     path = ROOT / 'artifacts/compaction/real_acceptance.json'
0072 |     path.parent.mkdir(parents=True, exist_ok=True)
0073 |     path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
0074 |     print(json.dumps(report, ensure_ascii=False, indent=2))
0075 |     if not all(checks.values()):
0076 |         raise SystemExit(1)
0077 | 
0078 | 
0079 | if __name__ == '__main__':
0080 |     main()
```
