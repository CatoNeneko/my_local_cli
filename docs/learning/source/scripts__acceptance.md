# scripts/acceptance.py：源码导读

固定项目的真实模型任务证据准备、工具链检查、重启、独立测试与报告。

先读专题：[08-verification.md](../08-verification.md)。

实际源码：[scripts/acceptance.py](../../../scripts/acceptance.py)。

快照 SHA256：`a6d175fbcce42aa1854a59cb8a71ac77b4cc54474de60472b90763b8b3359135`；193 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import argparse` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import hashlib` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `import sys` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `import tempfile` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `from datetime import datetime, timezone` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 10 | `APP_ROOT = Path(__file__).resolve().parents[1]` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 13 | `PROMPT = '请完成这个折扣函数修复项目。先读取 README.md、discount.py 和 test_discount.py，在任何写入之前调用 run_tests 运行现有测试并观察失败。然后按说明修复 discount.py，使用 create_file 新建 test_discount_edges.py，覆盖 0%、10…（见完整源码）` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 20 | `RESTART_PROMPT = '请只根据本会话已有历史回答：刚才修复了哪个文件、新建了哪个测试文件、最后测试是否通过？不要重新调用工具。'` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [sha256](#sha256) | [23](../../../scripts/acceptance.py#L23) | 对文件实际字节计算SHA256，核对固定测试未变化。 |
| [prepare](#prepare) | [27](../../../scripts/acceptance.py#L27) | 生成唯一验收目录与临时种子项目，保存预先冻结的标准和固定测试hash。 |
| [inspect_history](#inspect-history) | [51](../../../scripts/acceptance.py#L51) | 解析真实JSONL调用与结果，检查首次写前失败、改文件、新测试与最后成功。 |
| [snapshot](#snapshot) | [89](../../../scripts/acceptance.py#L89) | 独占保存首次会话快照，输出重启后的回忆问题。 |
| [verify_restart](#verify-restart) | [99](../../../scripts/acceptance.py#L99) | 检查原历史前缀不变、重启新增问题/回答与无需工具的回忆证据。 |
| [independent_verify](#independent-verify) | [121](../../../scripts/acceptance.py#L121) | 复制独立边界测试模板到临时项目，再经共享沙箱入口验证。 |
| [check](#check) | [140](../../../scripts/acceptance.py#L140) | 汇总真实文件、工具链、固定hash、重启和独立测试证据，失败返回非零。 |

<a id="sha256"></a>
## sha256

对文件实际字节计算SHA256，核对固定测试未变化。

```python
def sha256(path)
```

位置：[23行](../../../scripts/acceptance.py#L23) 至快照 24 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |

**调用表达式（静态提取，不含内层独立函数体）**：`hashlib.sha256`、`hashlib.sha256(path.read_bytes()).hexdigest`、`path.read_bytes`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 24 | 函数体 | 返回 `hashlib.sha256(path.read_bytes()).hexdigest()`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L24：`hashlib.sha256(path.read_bytes()).hexdigest()`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="prepare"></a>
## prepare

生成唯一验收目录与临时种子项目，保存预先冻结的标准和固定测试hash。

```python
def prepare()
```

位置：[27行](../../../scripts/acceptance.py#L27) 至快照 48 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`(evidence / 'manifest.json').write_text`、`(evidence / 'task.txt').write_text`、`(project / name).write_bytes`、`Path`、`datetime.now`、`datetime.now(timezone.utc).isoformat`、`datetime.now(timezone.utc).strftime`、`evidence.mkdir`、`json.dumps`、`print`、`seed.iterdir`、`sha256`、`source.is_file`、`source.name.removesuffix`、`source.read_bytes`、`str`、`tempfile.mkdtemp`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 29 | `run_id` | `datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 30 | `evidence` | `APP_ROOT / 'artifacts/acceptance' / run_id` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 32 | `project` | `Path(tempfile.mkdtemp(prefix='ai-cli-acceptance-', dir='/tmp'))` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 33 | `seed` | `APP_ROOT / 'examples/acceptance_seed'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 36 | `name` | `source.name.removesuffix('.txt')` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| 38 | `manifest` | `{'run_id': run_id, 'prepared_at': datetime.now(timezone.utc).isoformat(), 'workspace': str(project), 'session': 'acceptance', 'mod…（见完整源码）` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 28 | 函数体 | 在此处导入依赖：`from config import model_config`；局部导入可延迟加载或避免循环。 |
| 29 | 函数体 | 将 `datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')` 赋给 `run_id`。 |
| 30 | 函数体 | 将 `APP_ROOT / 'artifacts/acceptance' / run_id` 赋给 `evidence`。 |
| 31 | 函数体 | 计算表达式/调用产生动作：`evidence.mkdir(parents=True, exist_ok=False)`。 |
| 32 | 函数体 | 将 `Path(tempfile.mkdtemp(prefix='ai-cli-acceptance-', dir='/tmp'))` 赋给 `project`。 |
| 33 | 函数体 | 将 `APP_ROOT / 'examples/acceptance_seed'` 赋给 `seed`。 |
| 34 | 函数体 | 遍历 `seed.iterdir()`，每次绑定 `source`。 |
| 35 | 函数体 / 循环每次 | 条件 `source.is_file()`：真时执行body，假时进入else/后续。 |
| 36 | 函数体 / 循环每次 / 条件为真 | 将 `source.name.removesuffix('.txt')` 赋给 `name`。 |
| 37 | 函数体 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`(project / name).write_bytes(source.read_bytes())`。 |
| 38 | 函数体 | 将 `{'run_id': run_id, 'prepared_at': datetime.now(timezone.utc).isoformat(), 'workspace': str(project), 'session': 'acceptance', 'model': model_config['model'], 'base_url': …（见完整源码）` 赋给 `manifest`。 |
| 46 | 函数体 | 计算表达式/调用产生动作：`(evidence / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))`。 |
| 47 | 函数体 | 计算表达式/调用产生动作：`(evidence / 'task.txt').write_text(PROMPT)`。 |
| 48 | 函数体 | 计算表达式/调用产生动作：`print(json.dumps({'evidence': str(evidence), **manifest}, ensure_ascii=False, indent=2))`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="inspect-history"></a>
## inspect_history

解析真实JSONL调用与结果，检查首次写前失败、改文件、新测试与最后成功。

```python
def inspect_history(project, session='acceptance')
```

位置：[51行](../../../scripts/acceptance.py#L51) 至快照 86 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `project` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `session` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`ValueError`、`all`、`any`、`bool`、`call.get`、`enumerate`、`executions.append`、`item['arguments'].get`、`item['result'].get`、`json.loads`、`line.strip`、`max`、`message.get`、`min`、`path.read_text`、`path.read_text().splitlines`、`pending.extend`、`pending.pop`、`split_turns`、`valid_turn`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 53 | `path` | `project / '.ai-cli/sessions' / (session + '.jsonl')` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| 54 | `messages` | `[json.loads(line) for line in path.read_text().splitlines() if line.strip()]` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |
| 55 | `pending` | `[]` | 等待配对的工具结果/ID队列，或临时注册项映射。 |
| 56 | `executions` | `[]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 63 | `call` | `pending.pop(0)` | 一条工具调用/片段，最终执行须等完整模型结果。 |
| 66 | `writes` | `[i for i, item in enumerate(executions) if item['name'] in ('edit_file', 'create_file') and item['result'].get('ok') and item['res…（见完整源码）` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 69 | `failed` | `[i for i, item in enumerate(executions) if item['name'] == 'run_tests' and item['result'].get('exit_code') == 1 and ('failed' in i…（见完整源码）` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 72 | `passed` | `[i for i, item in enumerate(executions) if item['name'] == 'run_tests' and item['result'].get('ok') is True and ('passed' in item[…（见完整源码）` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 75 | `checks` | `{'failure_before_first_write': bool(writes and failed and (min(failed) < min(writes))), 'edit_executed': any((item['name'] == 'edi…（见完整源码）` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 52 | 函数体 | 在此处导入依赖：`from context_window import split_turns, valid_turn`；局部导入可延迟加载或避免循环。 |
| 53 | 函数体 | 将 `project / '.ai-cli/sessions' / (session + '.jsonl')` 赋给 `path`。 |
| 54 | 函数体 | 将 `[json.loads(line) for line in path.read_text().splitlines() if line.strip()]` 赋给 `messages`。 |
| 55 | 函数体 | 将 `[]` 赋给 `pending`。 |
| 56 | 函数体 | 将 `[]` 赋给 `executions`。 |
| 57 | 函数体 | 遍历 `messages`，每次绑定 `message`。 |
| 58 | 函数体 / 循环每次 | 条件 `message['role'] == 'assistant'`：真时执行body，假时进入else/后续。 |
| 59 | 函数体 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`pending.extend((call['function'] for call in message.get('tool_calls', [])))`。 |
| 60 | 函数体 / 循环每次 / 条件为假/elif | 条件 `message['role'] == 'tool'`：真时执行body，假时进入else/后续。 |
| 61 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 | 条件 `not pending`：真时执行body，假时进入else/后续。 |
| 62 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 / 条件为真 | 抛出 `ValueError('历史中存在孤立工具结果')`。 |
| 63 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 | 将 `pending.pop(0)` 赋给 `call`。 |
| 64 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 | 计算表达式/调用产生动作：`executions.append({'name': call['name'], 'arguments': call.get('arguments', {}), 'result': json.loads(message['content'])})`。 |
| 66 | 函数体 | 将 `[i for i, item in enumerate(executions) if item['name'] in ('edit_file', 'create_file') and item['result'].get('ok') and item['result'].get('changed')]` 赋给 `writes`。 |
| 69 | 函数体 | 将 `[i for i, item in enumerate(executions) if item['name'] == 'run_tests' and item['result'].get('exit_code') == 1 and ('failed' in item['result'].get('output', ''))]` 赋给 `failed`。 |
| 72 | 函数体 | 将 `[i for i, item in enumerate(executions) if item['name'] == 'run_tests' and item['result'].get('ok') is True and ('passed' in item['result'].get('output', ''))]` 赋给 `passed`。 |
| 75 | 函数体 | 将 `{'failure_before_first_write': bool(writes and failed and (min(failed) < min(writes))), 'edit_executed': any((item['name'] == 'edit_file' and item['result'].get('ok') is …（见完整源码）` 赋给 `checks`。 |
| 86 | 函数体 | 返回 `(messages, executions, checks)`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L86：`(messages, executions, checks)`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="snapshot"></a>
## snapshot

独占保存首次会话快照，输出重启后的回忆问题。

```python
def snapshot(evidence)
```

位置：[89行](../../../scripts/acceptance.py#L89) 至快照 96 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `evidence` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`(evidence / 'manifest.json').read_text`、`Path`、`ValueError`、`destination.exists`、`destination.write_bytes`、`json.loads`、`path.read_bytes`、`print`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 90 | `manifest` | `json.loads((evidence / 'manifest.json').read_text())` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 91 | `path` | `Path(manifest['workspace']) / '.ai-cli/sessions' / (manifest['session'] + '.jsonl')` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| 92 | `destination` | `evidence / 'initial_session.jsonl'` | 新名称/导出/复制发布的目标路径。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 90 | 函数体 | 将 `json.loads((evidence / 'manifest.json').read_text())` 赋给 `manifest`。 |
| 91 | 函数体 | 将 `Path(manifest['workspace']) / '.ai-cli/sessions' / (manifest['session'] + '.jsonl')` 赋给 `path`。 |
| 92 | 函数体 | 将 `evidence / 'initial_session.jsonl'` 赋给 `destination`。 |
| 93 | 函数体 | 条件 `destination.exists()`：真时执行body，假时进入else/后续。 |
| 94 | 函数体 / 条件为真 | 抛出 `ValueError('初始历史快照已存在，拒绝覆盖')`。 |
| 95 | 函数体 | 计算表达式/调用产生动作：`destination.write_bytes(path.read_bytes())`。 |
| 96 | 函数体 | 计算表达式/调用产生动作：`print('已保存初始历史；在新的 CLI 进程中输入：\n' + RESTART_PROMPT)`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="verify-restart"></a>
## verify_restart

检查原历史前缀不变、重启新增问题/回答与无需工具的回忆证据。

```python
def verify_restart(evidence)
```

位置：[99行](../../../scripts/acceptance.py#L99) 至快照 118 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `evidence` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`(evidence / 'initial_session.jsonl').read_bytes`、`(evidence / 'manifest.json').read_text`、`(evidence / 'restart_verified.json').write_text`、`(project / '.ai-cli/sessions' / (manifest['session'] + '.jsonl')).read_bytes`、`Path`、`all`、`bool`、`checks.values`、`current.decode`、`current.decode().splitlines`、`current.startswith`、`hashlib.sha256`、`hashlib.sha256(previous).hexdigest`、`json.dumps`、`json.loads`、`len`、`line.strip`、`new_rows[-1].get`、`new_rows[0].get`、`previous.decode`、`previous.decode().splitlines`、`print`、`row.get`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 100 | `manifest` | `json.loads((evidence / 'manifest.json').read_text())` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 101 | `project` | `Path(manifest['workspace'])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 102 | `previous` | `(evidence / 'initial_session.jsonl').read_bytes()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 103 | `current` | `(project / '.ai-cli/sessions' / (manifest['session'] + '.jsonl')).read_bytes()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 104 | `old_rows` | `[json.loads(line) for line in previous.decode().splitlines() if line.strip()]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 105 | `new_rows` | `[json.loads(line) for line in current.decode().splitlines() if line.strip()][len(old_rows):]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 106 | `reply` | `new_rows[-1].get('content', '') if new_rows else ''` | 模型最终文字或明确终止说明。 |
| 107 | `checks` | `{'original_history_preserved': current.startswith(previous), 'new_followup_recorded': bool(new_rows) and new_rows[0].get('content'…（见完整源码）` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 114 | `result` | `{'ok': all(checks.values()), 'checks': checks, 'workspace': str(project), 'initial_sha256': hashlib.sha256(previous).hexdigest(), …（见完整源码）` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 100 | 函数体 | 将 `json.loads((evidence / 'manifest.json').read_text())` 赋给 `manifest`。 |
| 101 | 函数体 | 将 `Path(manifest['workspace'])` 赋给 `project`。 |
| 102 | 函数体 | 将 `(evidence / 'initial_session.jsonl').read_bytes()` 赋给 `previous`。 |
| 103 | 函数体 | 将 `(project / '.ai-cli/sessions' / (manifest['session'] + '.jsonl')).read_bytes()` 赋给 `current`。 |
| 104 | 函数体 | 将 `[json.loads(line) for line in previous.decode().splitlines() if line.strip()]` 赋给 `old_rows`。 |
| 105 | 函数体 | 将 `[json.loads(line) for line in current.decode().splitlines() if line.strip()][len(old_rows):]` 赋给 `new_rows`。 |
| 106 | 函数体 | 将 `new_rows[-1].get('content', '') if new_rows else ''` 赋给 `reply`。 |
| 107 | 函数体 | 将 `{'original_history_preserved': current.startswith(previous), 'new_followup_recorded': bool(new_rows) and new_rows[0].get('content') == RESTART_PROMPT, 'no_tools_needed_fo…（见完整源码）` 赋给 `checks`。 |
| 114 | 函数体 | 将 `{'ok': all(checks.values()), 'checks': checks, 'workspace': str(project), 'initial_sha256': hashlib.sha256(previous).hexdigest(), 'reply': reply}` 赋给 `result`。 |
| 116 | 函数体 | 计算表达式/调用产生动作：`(evidence / 'restart_verified.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))`。 |
| 117 | 函数体 | 计算表达式/调用产生动作：`print(json.dumps(result, ensure_ascii=False, indent=2))`。 |
| 118 | 函数体 | 返回 `0 if result['ok'] else 1`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L118：`0 if result['ok'] else 1`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="independent-verify"></a>
## independent_verify

复制独立边界测试模板到临时项目，再经共享沙箱入口验证。

```python
def independent_verify(evidence)
```

位置：[121行](../../../scripts/acceptance.py#L121) 至快照 137 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `evidence` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`(evidence / 'independent_test_result.json').write_text`、`(evidence / 'manifest.json').read_text`、`Path`、`ValueError`、`execute_tool`、`file.write`、`json.dumps`、`json.loads`、`print`、`sha256`、`source.read_bytes`、`str`、`target.exists`、`target.open`、`use_workspace`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 124 | `manifest` | `json.loads((evidence / 'manifest.json').read_text())` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 125 | `project` | `Path(manifest['workspace'])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 126 | `source` | `APP_ROOT / 'examples/acceptance_verify/test_acceptance_independent.py.txt'` | 可信调用方指定的来源，model或user；不能从模型参数中采纳。 |
| 127 | `target` | `project / 'test_acceptance_independent.py'` | 已选定的文件/目录或操作目标，提交前可能需要再次验证。 |
| 133 | `result` | `execute_tool('run_tests', {'path': target.name}, source='user')` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 134 | `result` | `{**result, 'test_sha256': sha256(target), 'workspace': str(project)}` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 122 | 函数体 | 在此处导入依赖：`from tools import execute_tool`；局部导入可延迟加载或避免循环。 |
| 123 | 函数体 | 在此处导入依赖：`from workspace import use_workspace`；局部导入可延迟加载或避免循环。 |
| 124 | 函数体 | 将 `json.loads((evidence / 'manifest.json').read_text())` 赋给 `manifest`。 |
| 125 | 函数体 | 将 `Path(manifest['workspace'])` 赋给 `project`。 |
| 126 | 函数体 | 将 `APP_ROOT / 'examples/acceptance_verify/test_acceptance_independent.py.txt'` 赋给 `source`。 |
| 127 | 函数体 | 将 `project / 'test_acceptance_independent.py'` 赋给 `target`。 |
| 128 | 函数体 | 条件 `target.exists()`：真时执行body，假时进入else/后续。 |
| 129 | 函数体 / 条件为真 | 抛出 `ValueError('独立验证文件已存在，拒绝覆盖；如需重跑可直接调用工具')`。 |
| 130 | 函数体 | 进入资源/状态范围：`target.open('xb')` 绑定 `file`；退出执行清理。 |
| 131 | 函数体 / with范围 | 计算表达式/调用产生动作：`file.write(source.read_bytes())`。 |
| 132 | 函数体 | 进入资源/状态范围：`use_workspace(project)`；退出执行清理。 |
| 133 | 函数体 / with范围 | 将 `execute_tool('run_tests', {'path': target.name}, source='user')` 赋给 `result`。 |
| 134 | 函数体 | 将 `{**result, 'test_sha256': sha256(target), 'workspace': str(project)}` 赋给 `result`。 |
| 135 | 函数体 | 计算表达式/调用产生动作：`(evidence / 'independent_test_result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))`。 |
| 136 | 函数体 | 计算表达式/调用产生动作：`print(json.dumps(result, ensure_ascii=False, indent=2))`。 |
| 137 | 函数体 | 返回 `0 if result['ok'] else 1`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L137：`0 if result['ok'] else 1`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="check"></a>
## check

汇总真实文件、工具链、固定hash、重启和独立测试证据，失败返回非零。

```python
def check(evidence)
```

位置：[140行](../../../scripts/acceptance.py#L140) 至快照 172 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `evidence` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`'\n'.join`、`(evidence / 'manifest.json').read_text`、`(evidence / 'report.json').write_text`、`(evidence / 'session.jsonl').write_text`、`(evidence / (name + '.txt')).write_bytes`、`(project / 'test_discount_edges.py').is_file`、`(project / name).is_file`、`(project / name).read_bytes`、`Path`、`all`、`any`、`checks.values`、`datetime.now`、`datetime.now(timezone.utc).isoformat`、`independent.is_file`、`independent.read_text`、`inspect_history`、`item['result'].get`、`json.dumps`、`json.loads`、`json.loads(independent.read_text()).get`、`json.loads(restart.read_text()).get`、`print`、`restart.is_file`、`restart.read_text`、`sha256`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 141 | `manifest` | `json.loads((evidence / 'manifest.json').read_text())` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 142 | `project` | `Path(manifest['workspace'])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 143 | `(messages, executions, checks)` | `inspect_history(project, manifest['session'])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 144 | `checks['baseline_unchanged']` | `sha256(project / 'test_discount.py') == manifest['baseline_sha256']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 145 | `checks['edge_test_exists']` | `(project / 'test_discount_edges.py').is_file()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 147 | `restart` | `evidence / 'restart_verified.json'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 148 | `checks['restart_verified']` | `restart.is_file() and json.loads(restart.read_text()).get('ok') is True and (json.loads(restart.read_text()).get('workspace') == s…（见完整源码）` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 150 | `independent` | `evidence / 'independent_test_result.json'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 151 | `checks['independent_tests_passed']` | `independent.is_file() and json.loads(independent.read_text()).get('ok') is True and ('8 passed' in json.loads(independent.read_tex…（见完整源码）` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 155 | `report` | `{'checked_at': datetime.now(timezone.utc).isoformat(), 'manifest': manifest, 'checks': checks, 'passed': all(checks.values()), 'ad…（见完整源码）` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 141 | 函数体 | 将 `json.loads((evidence / 'manifest.json').read_text())` 赋给 `manifest`。 |
| 142 | 函数体 | 将 `Path(manifest['workspace'])` 赋给 `project`。 |
| 143 | 函数体 | 将 `inspect_history(project, manifest['session'])` 赋给 `(messages, executions, checks)`。 |
| 144 | 函数体 | 将 `sha256(project / 'test_discount.py') == manifest['baseline_sha256']` 赋给 `checks['baseline_unchanged']`。 |
| 145 | 函数体 | 将 `(project / 'test_discount_edges.py').is_file()` 赋给 `checks['edge_test_exists']`。 |
| 147 | 函数体 | 将 `evidence / 'restart_verified.json'` 赋给 `restart`。 |
| 148 | 函数体 | 将 `restart.is_file() and json.loads(restart.read_text()).get('ok') is True and (json.loads(restart.read_text()).get('workspace') == str(project))` 赋给 `checks['restart_verified']`。 |
| 150 | 函数体 | 将 `evidence / 'independent_test_result.json'` 赋给 `independent`。 |
| 151 | 函数体 | 将 `independent.is_file() and json.loads(independent.read_text()).get('ok') is True and ('8 passed' in json.loads(independent.read_text()).get('output', '')) and (json.loads(…（见完整源码）` 赋给 `checks['independent_tests_passed']`。 |
| 155 | 函数体 | 将 `{'checked_at': datetime.now(timezone.utc).isoformat(), 'manifest': manifest, 'checks': checks, 'passed': all(checks.values()), 'additional_checks': {'real_mcp_add_returne…（见完整源码）` 赋给 `report`。 |
| 166 | 函数体 | 计算表达式/调用产生动作：`(evidence / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))`。 |
| 167 | 函数体 | 计算表达式/调用产生动作：`(evidence / 'session.jsonl').write_text('\n'.join((json.dumps(row, ensure_ascii=False) for row in messages)) + '\n')`。 |
| 168 | 函数体 | 遍历 `('discount.py', 'test_discount.py', 'test_discount_edges.py')`，每次绑定 `name`。 |
| 169 | 函数体 / 循环每次 | 条件 `(project / name).is_file()`：真时执行body，假时进入else/后续。 |
| 170 | 函数体 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`(evidence / (name + '.txt')).write_bytes((project / name).read_bytes())`。 |
| 171 | 函数体 | 计算表达式/调用产生动作：`print(json.dumps(report, ensure_ascii=False, indent=2))`。 |
| 172 | 函数体 | 返回 `0 if report['passed'] else 1`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L172：`0 if report['passed'] else 1`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- with/yield：资源/状态生命周期或逐个生成：L130, L132。
- 推导式/生成器表达式：循环建容器或逐个产生：L54, L59, L66, L69, L72, L77, L80, L84, L104, L105, L110, L158, L164, L167。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """准备独立验收项目，检查真实 CLI 历史并保存证据；不模拟模型回复。"""
0002 | import argparse
0003 | import hashlib
0004 | import json
0005 | import sys
0006 | import tempfile
0007 | from datetime import datetime, timezone
0008 | from pathlib import Path
0009 | 
0010 | APP_ROOT = Path(__file__).resolve().parents[1]
0011 | sys.path.insert(0, str(APP_ROOT))
0012 | 
0013 | PROMPT = (
0014 |     '请完成这个折扣函数修复项目。先读取 README.md、discount.py 和 test_discount.py，'
0015 |     '在任何写入之前调用 run_tests 运行现有测试并观察失败。然后按说明修复 discount.py，'
0016 |     '使用 create_file 新建 test_discount_edges.py，覆盖 0%、100%、负价格和超范围折扣。'
0017 |     '禁止修改或删除固定的 test_discount.py。最后调用 run_tests 运行整个项目，'
0018 |     '若失败，根据真实错误继续修复；只根据工具结果报告最终状态。'
0019 | )
0020 | RESTART_PROMPT = '请只根据本会话已有历史回答：刚才修复了哪个文件、新建了哪个测试文件、最后测试是否通过？不要重新调用工具。'
0021 | 
0022 | 
0023 | def sha256(path):
0024 |     return hashlib.sha256(path.read_bytes()).hexdigest()
0025 | 
0026 | 
0027 | def prepare():
0028 |     from config import model_config
0029 |     run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
0030 |     evidence = APP_ROOT / 'artifacts/acceptance' / run_id
0031 |     evidence.mkdir(parents=True, exist_ok=False)
0032 |     project = Path(tempfile.mkdtemp(prefix='ai-cli-acceptance-', dir='/tmp'))
0033 |     seed = APP_ROOT / 'examples/acceptance_seed'
0034 |     for source in seed.iterdir():
0035 |         if source.is_file():
0036 |             name = source.name.removesuffix('.txt')
0037 |             (project / name).write_bytes(source.read_bytes())
0038 |     manifest = {
0039 |         'run_id': run_id, 'prepared_at': datetime.now(timezone.utc).isoformat(),
0040 |         'workspace': str(project), 'session': 'acceptance',
0041 |         'model': model_config['model'], 'base_url': model_config['base_url'], 'stream': model_config['stream'],
0042 |         'baseline_sha256': sha256(project / 'test_discount.py'),
0043 |         'criteria': ['真实失败在首次写入前', '实现修改', '新增边界测试', '修复后真实测试通过',
0044 |                      '固定测试未改变', '完整工具链', '另进程恢复会话', '独立边界验证通过'],
0045 |     }
0046 |     (evidence / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
0047 |     (evidence / 'task.txt').write_text(PROMPT)
0048 |     print(json.dumps({'evidence': str(evidence), **manifest}, ensure_ascii=False, indent=2))
0049 | 
0050 | 
0051 | def inspect_history(project, session='acceptance'):
0052 |     from context_window import split_turns, valid_turn
0053 |     path = project / '.ai-cli/sessions' / (session + '.jsonl')
0054 |     messages = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
0055 |     pending = []
0056 |     executions = []
0057 |     for message in messages:
0058 |         if message['role'] == 'assistant':
0059 |             pending.extend(call['function'] for call in message.get('tool_calls', []))
0060 |         elif message['role'] == 'tool':
0061 |             if not pending:
0062 |                 raise ValueError('历史中存在孤立工具结果')
0063 |             call = pending.pop(0)
0064 |             executions.append({'name': call['name'], 'arguments': call.get('arguments', {}),
0065 |                                'result': json.loads(message['content'])})
0066 |     writes = [i for i, item in enumerate(executions)
0067 |               if item['name'] in ('edit_file', 'create_file') and item['result'].get('ok')
0068 |               and item['result'].get('changed')]
0069 |     failed = [i for i, item in enumerate(executions)
0070 |               if item['name'] == 'run_tests' and item['result'].get('exit_code') == 1
0071 |               and 'failed' in item['result'].get('output', '')]
0072 |     passed = [i for i, item in enumerate(executions)
0073 |               if item['name'] == 'run_tests' and item['result'].get('ok') is True
0074 |               and 'passed' in item['result'].get('output', '')]
0075 |     checks = {
0076 |         'failure_before_first_write': bool(writes and failed and min(failed) < min(writes)),
0077 |         'edit_executed': any(item['name'] == 'edit_file' and item['result'].get('ok') is True
0078 |                              and Path(item['arguments'].get('path', '')).name == 'discount.py'
0079 |                              and item['result'].get('changed') for item in executions),
0080 |         'create_executed': any(item['name'] == 'create_file' and item['result'].get('ok') is True
0081 |                                and Path(item['arguments'].get('path', '')).name == 'test_discount_edges.py'
0082 |                                and item['result'].get('changed') for item in executions),
0083 |         'passed_after_last_write': bool(writes and passed and max(passed) > max(writes)),
0084 |         'tool_chain_complete': bool(messages) and not pending and all(valid_turn(turn) for turn in split_turns(messages)),
0085 |     }
0086 |     return messages, executions, checks
0087 | 
0088 | 
0089 | def snapshot(evidence):
0090 |     manifest = json.loads((evidence / 'manifest.json').read_text())
0091 |     path = Path(manifest['workspace']) / '.ai-cli/sessions' / (manifest['session'] + '.jsonl')
0092 |     destination = evidence / 'initial_session.jsonl'
0093 |     if destination.exists():
0094 |         raise ValueError('初始历史快照已存在，拒绝覆盖')
0095 |     destination.write_bytes(path.read_bytes())
0096 |     print('已保存初始历史；在新的 CLI 进程中输入：\n' + RESTART_PROMPT)
0097 | 
0098 | 
0099 | def verify_restart(evidence):
0100 |     manifest = json.loads((evidence / 'manifest.json').read_text())
0101 |     project = Path(manifest['workspace'])
0102 |     previous = (evidence / 'initial_session.jsonl').read_bytes()
0103 |     current = (project / '.ai-cli/sessions' / (manifest['session'] + '.jsonl')).read_bytes()
0104 |     old_rows = [json.loads(line) for line in previous.decode().splitlines() if line.strip()]
0105 |     new_rows = [json.loads(line) for line in current.decode().splitlines() if line.strip()][len(old_rows):]
0106 |     reply = new_rows[-1].get('content', '') if new_rows else ''
0107 |     checks = {
0108 |         'original_history_preserved': current.startswith(previous),
0109 |         'new_followup_recorded': bool(new_rows) and new_rows[0].get('content') == RESTART_PROMPT,
0110 |         'no_tools_needed_for_recall': bool(new_rows) and all(row.get('role') != 'tool' for row in new_rows),
0111 |         'recalled_files': bool(new_rows) and new_rows[-1].get('role') == 'assistant'
0112 |                           and 'discount.py' in reply and 'test_discount_edges.py' in reply,
0113 |     }
0114 |     result = {'ok': all(checks.values()), 'checks': checks, 'workspace': str(project),
0115 |               'initial_sha256': hashlib.sha256(previous).hexdigest(), 'reply': reply}
0116 |     (evidence / 'restart_verified.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
0117 |     print(json.dumps(result, ensure_ascii=False, indent=2))
0118 |     return 0 if result['ok'] else 1
0119 | 
0120 | 
0121 | def independent_verify(evidence):
0122 |     from tools import execute_tool
0123 |     from workspace import use_workspace
0124 |     manifest = json.loads((evidence / 'manifest.json').read_text())
0125 |     project = Path(manifest['workspace'])
0126 |     source = APP_ROOT / 'examples/acceptance_verify/test_acceptance_independent.py.txt'
0127 |     target = project / 'test_acceptance_independent.py'
0128 |     if target.exists():
0129 |         raise ValueError('独立验证文件已存在，拒绝覆盖；如需重跑可直接调用工具')
0130 |     with target.open('xb') as file:
0131 |         file.write(source.read_bytes())
0132 |     with use_workspace(project):
0133 |         result = execute_tool('run_tests', {'path': target.name}, source='user')
0134 |     result = {**result, 'test_sha256': sha256(target), 'workspace': str(project)}
0135 |     (evidence / 'independent_test_result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
0136 |     print(json.dumps(result, ensure_ascii=False, indent=2))
0137 |     return 0 if result['ok'] else 1
0138 | 
0139 | 
0140 | def check(evidence):
0141 |     manifest = json.loads((evidence / 'manifest.json').read_text())
0142 |     project = Path(manifest['workspace'])
0143 |     messages, executions, checks = inspect_history(project, manifest['session'])
0144 |     checks['baseline_unchanged'] = sha256(project / 'test_discount.py') == manifest['baseline_sha256']
0145 |     checks['edge_test_exists'] = (project / 'test_discount_edges.py').is_file()
0146 |     # 另进程恢复与独立边界测试必须单独运行，不能用模型声称成功代替证据。
0147 |     restart = evidence / 'restart_verified.json'
0148 |     checks['restart_verified'] = (restart.is_file() and json.loads(restart.read_text()).get('ok') is True
0149 |                                   and json.loads(restart.read_text()).get('workspace') == str(project))
0150 |     independent = evidence / 'independent_test_result.json'
0151 |     checks['independent_tests_passed'] = (independent.is_file() and json.loads(independent.read_text()).get('ok') is True
0152 |                                          and '8 passed' in json.loads(independent.read_text()).get('output', '')
0153 |                                          and json.loads(independent.read_text()).get('test_sha256')
0154 |                                          == sha256(APP_ROOT / 'examples/acceptance_verify/test_acceptance_independent.py.txt'))
0155 |     report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'manifest': manifest,
0156 |               'checks': checks, 'passed': all(checks.values()),
0157 |               'additional_checks': {
0158 |                   'real_mcp_add_returned_42': any(
0159 |                       item['name'] == 'mcp__demo__add' and item['result'].get('ok') is True
0160 |                       and item['arguments'] == {'a': 19, 'b': 23}
0161 |                       and item['result'].get('structured_content') == {'result': 42}
0162 |                       for item in executions)
0163 |               },
0164 |               'tool_calls': [{'name': item['name'], 'ok': item['result'].get('ok'),
0165 |                               'exit_code': item['result'].get('exit_code')} for item in executions]}
0166 |     (evidence / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
0167 |     (evidence / 'session.jsonl').write_text('\n'.join(json.dumps(row, ensure_ascii=False) for row in messages) + '\n')
0168 |     for name in ('discount.py', 'test_discount.py', 'test_discount_edges.py'):
0169 |         if (project / name).is_file():
0170 |             (evidence / (name + '.txt')).write_bytes((project / name).read_bytes())
0171 |     print(json.dumps(report, ensure_ascii=False, indent=2))
0172 |     return 0 if report['passed'] else 1
0173 | 
0174 | 
0175 | if __name__ == '__main__':
0176 |     parser = argparse.ArgumentParser(description=__doc__)
0177 |     subparsers = parser.add_subparsers(dest='command', required=True)
0178 |     subparsers.add_parser('prepare')
0179 |     checker = subparsers.add_parser('check')
0180 |     checker.add_argument('evidence', type=Path)
0181 |     for command in ('snapshot', 'restart', 'verify'):
0182 |         subparsers.add_parser(command).add_argument('evidence', type=Path)
0183 |     args = parser.parse_args()
0184 |     if args.command == 'prepare':
0185 |         prepare()
0186 |     elif args.command == 'check':
0187 |         raise SystemExit(check(args.evidence))
0188 |     elif args.command == 'snapshot':
0189 |         snapshot(args.evidence)
0190 |     elif args.command == 'restart':
0191 |         raise SystemExit(verify_restart(args.evidence))
0192 |     elif args.command == 'verify':
0193 |         raise SystemExit(independent_verify(args.evidence))
```
