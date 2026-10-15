# scripts/browser_acceptance.py：源码导读

固定本地页面的真实模型打开/填写/点击/读取/截图验收，仅预授权本地browser。

先读专题：[08-verification.md](../08-verification.md)。

实际源码：[scripts/browser_acceptance.py](../../../scripts/browser_acceptance.py)。

快照 SHA256：`4b7388702d55840c6f45b52a97e5534cc577098ebd5b306631633b24955198f9`；90 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `import sys` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `import tempfile` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `import threading` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `import uuid` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 10 | `ROOT = Path(__file__).resolve().parents[1]` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 12 | `from agent import run_agent` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 13 | `from config import model_config` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 14 | `import history` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 15 | `from mcp_manager import MCPManager` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 16 | `import permissions` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 17 | `from workspace import use_workspace` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [main](#main) | [20](../../../scripts/browser_acceptance.py#L20) | 启动固定本地HTTP页和临时项目，真实模型跑浏览器工具链，再核对随机问候/PNG与真实结果。 |
| [main.Handler.log_message](#main-handler-log-message) | [23](../../../scripts/browser_acceptance.py#L23) | 测试HTTP服务器禁止默认日志输出，保持验收输出清楚。 |
| [main.Handler.do_GET](#main-handler-do-get) | [25](../../../scripts/browser_acceptance.py#L25) | 返回固定本地验收HTML，按钮只更新本地页面文字，没有真实业务操作。 |
| [main.confirm](#main-confirm) | [40](../../../scripts/browser_acceptance.py#L40) | 验收脚本仅预授权browser服务与指定本地URL，不改日常策略。 |

<a id="main"></a>
## main

启动固定本地HTTP页和临时项目，真实模型跑浏览器工具链，再核对随机问候/PNG与真实结果。

```python
def main()
```

位置：[20行](../../../scripts/browser_acceptance.py#L20) 至快照 86 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`MCPManager`、`Path`、`Path(path).is_relative_to`、`Path(path).read_bytes`、`Path(path).read_bytes().startswith`、`RuntimeError`、`SystemExit`、`ThreadingHTTPServer`、`all`、`any`、`bool`、`destination.parent.mkdir`、`destination.write_text`、`history.append_message`、`history.append_messages`、`json.dumps`、`json.loads`、`manager.connect`、`name.startswith`、`print`、`report['checks'].values`、`result.get`、`result.get('structured_content', {}).get`、`run_agent`、`str`、`tempfile.mkdtemp`、`threading.Thread`、`use_workspace`、`uuid.uuid4`、`website.server_close`、`website.shutdown`、`worker.join`、`worker.start`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 21 | `marker` | `'Ada_' + uuid.uuid4().hex[:8]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 33 | `website` | `ThreadingHTTPServer(('127.0.0.1', 0), Handler)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 34 | `worker` | `threading.Thread(target=website.serve_forever, daemon=True)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 36 | `url` | `f'http://127.0.0.1:{website.server_port}/'` | 待打开HTTP(S)地址，验证后才能导航。 |
| 37 | `workspace` | `Path(tempfile.mkdtemp(prefix='cli-browser-acceptance-'))` | 目标项目目录，不是助手安装环境。 |
| 38 | `old_confirm` | `permissions.confirm_tool` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 39 | `approvals` | `[]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 47 | `permissions.confirm_tool` | `confirm` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 48 | `report` | `{'workspace': str(workspace), 'model': model_config['model'], 'checks': {}, 'approvals': approvals}` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 51 | `connection` | `manager.connect('browser')` | 固定MCP启动参数与路由信息。 |
| 54 | `messages` | `[{'role': 'user', 'content': f'浏览器验收：真实调用 MCP 浏览器工具打开 {url}，向 Name 输入框填写 {marker}，点击 Greet 按钮，读取并确认页面显示的 Hello 文字，然后保存截图。每次操作使用上一份…（见完整源码）` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |
| 60 | `reply` | `run_agent(messages)` | 模型最终文字或明确终止说明。 |
| 62 | `results` | `[(m['tool_name'], json.loads(m['content'])) for m in messages if m['role'] == 'tool']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 63 | `report['reply']` | `reply` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 64 | `report['tool_results']` | `results` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 65 | `checks` | `report['checks']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 67 | `checks[suffix]` | `any((name == 'mcp__browser__' + suffix and result.get('ok') for name, result in results))` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 68 | `checks['actual_page_greeting']` | `any(('Hello ' + marker in result.get('structured_content', {}).get('text', '') for _, result in results))` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 69 | `shots` | `[result['structured_content']['path'] for name, result in results if name == 'mcp__browser__screenshot' and result.get('ok')]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 71 | `checks['real_png_in_private_directory']` | `bool(shots) and all((Path(path).is_relative_to(workspace / '.ai-cli/.browser-artifacts') and Path(path).read_bytes().startswith(b'…（见完整源码）` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 73 | `checks['answer_matches_page']` | `'Hello ' + marker in reply` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 74 | `checks['only_browser_tools']` | `bool(results) and all((name.startswith('mcp__browser__') for name, _ in results))` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 75 | `checks['no_failed_tools']` | `all((result.get('ok') for _, result in results))` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 77 | `permissions.confirm_tool` | `old_confirm` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 81 | `destination` | `ROOT / 'artifacts/browser/real_acceptance.json'` | 新名称/导出/复制发布的目标路径。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 21 | 函数体 | 将 `'Ada_' + uuid.uuid4().hex[:8]` 赋给 `marker`。 |
| 22 | 函数体 | 定义类 `Handler`，保存方法与对象状态。 |
| 33 | 函数体 | 将 `ThreadingHTTPServer(('127.0.0.1', 0), Handler)` 赋给 `website`。 |
| 34 | 函数体 | 将 `threading.Thread(target=website.serve_forever, daemon=True)` 赋给 `worker`。 |
| 35 | 函数体 | 计算表达式/调用产生动作：`worker.start()`。 |
| 36 | 函数体 | 将 `f'http://127.0.0.1:{website.server_port}/'` 赋给 `url`。 |
| 37 | 函数体 | 将 `Path(tempfile.mkdtemp(prefix='cli-browser-acceptance-'))` 赋给 `workspace`。 |
| 38 | 函数体 | 将 `permissions.confirm_tool` 赋给 `old_confirm`。 |
| 39 | 函数体 | 将 `[]` 赋给 `approvals`。 |
| 40 | 函数体 | 定义嵌套函数 `confirm`；定义本身不执行函数体。 |
| 47 | 函数体 | 将 `confirm` 赋给 `permissions.confirm_tool`。 |
| 48 | 函数体 | 将 `{'workspace': str(workspace), 'model': model_config['model'], 'checks': {}, 'approvals': approvals}` 赋给 `report`。 |
| 49 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 50 | 函数体 / try | 进入资源/状态范围：`use_workspace(workspace)`, `MCPManager()` 绑定 `manager`；退出执行清理。 |
| 51 | 函数体 / try / with范围 | 将 `manager.connect('browser')` 赋给 `connection`。 |
| 52 | 函数体 / try / with范围 | 条件 `not connection['ok']`：真时执行body，假时进入else/后续。 |
| 53 | 函数体 / try / with范围 / 条件为真 | 抛出 `RuntimeError(connection)`。 |
| 54 | 函数体 / try / with范围 | 将 `[{'role': 'user', 'content': f'浏览器验收：真实调用 MCP 浏览器工具打开 {url}，向 Name 输入框填写 {marker}，点击 Greet 按钮，读取并确认页面显示的 Hello 文字，然后保存截图。每次操作使用上一份结果中的最新 ref。只操作这个本地网页，不使用其他工具。最后告诉我页面实际显示…（见完整源码）` 赋给 `messages`。 |
| 59 | 函数体 / try / with范围 | 计算表达式/调用产生动作：`history.append_messages(messages)`。 |
| 60 | 函数体 / try / with范围 | 将 `run_agent(messages)` 赋给 `reply`。 |
| 61 | 函数体 / try / with范围 | 计算表达式/调用产生动作：`history.append_message({'role': 'assistant', 'content': reply})`。 |
| 62 | 函数体 / try / with范围 | 将 `[(m['tool_name'], json.loads(m['content'])) for m in messages if m['role'] == 'tool']` 赋给 `results`。 |
| 63 | 函数体 / try / with范围 | 将 `reply` 赋给 `report['reply']`。 |
| 64 | 函数体 / try / with范围 | 将 `results` 赋给 `report['tool_results']`。 |
| 65 | 函数体 / try / with范围 | 将 `report['checks']` 赋给 `checks`。 |
| 66 | 函数体 / try / with范围 | 遍历 `('open_page', 'fill', 'click', 'screenshot')`，每次绑定 `suffix`。 |
| 67 | 函数体 / try / with范围 / 循环每次 | 将 `any((name == 'mcp__browser__' + suffix and result.get('ok') for name, result in results))` 赋给 `checks[suffix]`。 |
| 68 | 函数体 / try / with范围 | 将 `any(('Hello ' + marker in result.get('structured_content', {}).get('text', '') for _, result in results))` 赋给 `checks['actual_page_greeting']`。 |
| 69 | 函数体 / try / with范围 | 将 `[result['structured_content']['path'] for name, result in results if name == 'mcp__browser__screenshot' and result.get('ok')]` 赋给 `shots`。 |
| 71 | 函数体 / try / with范围 | 将 `bool(shots) and all((Path(path).is_relative_to(workspace / '.ai-cli/.browser-artifacts') and Path(path).read_bytes().startswith(b'\x89PNG') for path in shots))` 赋给 `checks['real_png_in_private_directory']`。 |
| 73 | 函数体 / try / with范围 | 将 `'Hello ' + marker in reply` 赋给 `checks['answer_matches_page']`。 |
| 74 | 函数体 / try / with范围 | 将 `bool(results) and all((name.startswith('mcp__browser__') for name, _ in results))` 赋给 `checks['only_browser_tools']`。 |
| 75 | 函数体 / try / with范围 | 将 `all((result.get('ok') for _, result in results))` 赋给 `checks['no_failed_tools']`。 |
| 77 | 函数体 / finally保证清理 | 将 `old_confirm` 赋给 `permissions.confirm_tool`。 |
| 78 | 函数体 / finally保证清理 | 计算表达式/调用产生动作：`website.shutdown()`。 |
| 79 | 函数体 / finally保证清理 | 计算表达式/调用产生动作：`website.server_close()`。 |
| 80 | 函数体 / finally保证清理 | 计算表达式/调用产生动作：`worker.join()`。 |
| 81 | 函数体 / finally保证清理 | 将 `ROOT / 'artifacts/browser/real_acceptance.json'` 赋给 `destination`。 |
| 82 | 函数体 / finally保证清理 | 计算表达式/调用产生动作：`destination.parent.mkdir(parents=True, exist_ok=True)`。 |
| 83 | 函数体 / finally保证清理 | 计算表达式/调用产生动作：`destination.write_text(json.dumps(report, ensure_ascii=False, indent=2))`。 |
| 84 | 函数体 | 计算表达式/调用产生动作：`print(json.dumps(report, ensure_ascii=False, indent=2))`。 |
| 85 | 函数体 | 条件 `not report['checks'] or not all(report['checks'].values())`：真时执行body，假时进入else/后续。 |
| 86 | 函数体 / 条件为真 | 抛出 `SystemExit(1)`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="main-handler-log-message"></a>
## main.Handler.log_message

测试HTTP服务器禁止默认日志输出，保持验收输出清楚。

```python
def log_message(self, *args)
```

位置：[23行](../../../scripts/browser_acceptance.py#L23) 至快照 24 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `args` | `未显式注解` | 解析启动参数Namespace或工具参数字典，按来源区分。 |

**调用表达式（静态提取，不含内层独立函数体）**：无直接调用。

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 24 | 函数体 | pass占位，无动作。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="main-handler-do-get"></a>
## main.Handler.do_GET

返回固定本地验收HTML，按钮只更新本地页面文字，没有真实业务操作。

```python
def do_GET(self)
```

位置：[25行](../../../scripts/browser_acceptance.py#L25) 至快照 32 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：`self.end_headers`、`self.send_header`、`self.send_response`、`self.wfile.write`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 26 | 函数体 | 计算表达式/调用产生动作：`self.send_response(200)`。 |
| 27 | 函数体 | 计算表达式/调用产生动作：`self.send_header('Content-Type', 'text/html; charset=utf-8')`。 |
| 28 | 函数体 | 计算表达式/调用产生动作：`self.end_headers()`。 |
| 29 | 函数体 | 计算表达式/调用产生动作：`self.wfile.write(b'<!doctype html><title>Browser acceptance</title>\n<label>Name<input id="name" placeholder="Name"></label>\n<button onclick="document.getElementById(\'r…（见完整源码）`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="main-confirm"></a>
## main.confirm

验收脚本仅预授权browser服务与指定本地URL，不改日常策略。

```python
def confirm(name, target, details='')
```

位置：[40行](../../../scripts/browser_acceptance.py#L40) 至快照 46 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| `target` | `未显式注解` | 已选定的文件/目录或操作目标，提交前可能需要再次验证。 |
| `details` | `未显式注解` | 用户确认/审批展示的动作说明。 |

**调用表达式（静态提取，不含内层独立函数体）**：`approvals.append`、`args.get`、`details.split`、`json.loads`、`name.startswith`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 41 | `allowed` | `target == 'browser' and name == 'mcp_connect'` | 通过边界校验的子目录集合，或是否许可的布尔值。 |
| 43 | `args` | `json.loads(details.split('\n工具参数: ', 1)[1])` | 解析启动参数Namespace或工具参数字典，按来源区分。 |
| 44 | `allowed` | `name != 'mcp__browser__open_page' or args.get('url') == url` | 通过边界校验的子目录集合，或是否许可的布尔值。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 41 | 函数体 | 将 `target == 'browser' and name == 'mcp_connect'` 赋给 `allowed`。 |
| 42 | 函数体 | 条件 `target == 'browser' and name.startswith('mcp__browser__')`：真时执行body，假时进入else/后续。 |
| 43 | 函数体 / 条件为真 | 将 `json.loads(details.split('\n工具参数: ', 1)[1])` 赋给 `args`。 |
| 44 | 函数体 / 条件为真 | 将 `name != 'mcp__browser__open_page' or args.get('url') == url` 赋给 `allowed`。 |
| 45 | 函数体 | 计算表达式/调用产生动作：`approvals.append({'tool': name, 'allowed': allowed})`。 |
| 46 | 函数体 | 返回 `allowed`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L46：`allowed`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- class：对象状态与方法/继承：L22。
- try/except/finally：异常与保证清理：L49。
- with/yield：资源/状态生命周期或逐个生成：L50。
- 推导式/生成器表达式：循环建容器或逐个产生：L62, L67, L68, L69, L71, L74, L75。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """真实模型通过统一工具循环操作固定本地网页；只授权该网页的浏览器工具。"""
0002 | import json
0003 | from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
0004 | from pathlib import Path
0005 | import sys
0006 | import tempfile
0007 | import threading
0008 | import uuid
0009 | 
0010 | ROOT = Path(__file__).resolve().parents[1]
0011 | sys.path.insert(0, str(ROOT))
0012 | from agent import run_agent
0013 | from config import model_config
0014 | import history
0015 | from mcp_manager import MCPManager
0016 | import permissions
0017 | from workspace import use_workspace
0018 | 
0019 | 
0020 | def main():
0021 |     marker = 'Ada_' + uuid.uuid4().hex[:8]
0022 |     class Handler(BaseHTTPRequestHandler):
0023 |         def log_message(self, *args):
0024 |             pass
0025 |         def do_GET(self):
0026 |             self.send_response(200)
0027 |             self.send_header('Content-Type', 'text/html; charset=utf-8')
0028 |             self.end_headers()
0029 |             self.wfile.write(b'''<!doctype html><title>Browser acceptance</title>
0030 | <label>Name<input id="name" placeholder="Name"></label>
0031 | <button onclick="document.getElementById('result').textContent='Hello '+document.getElementById('name').value">Greet</button>
0032 | <div id="result"></div>''')
0033 |     website = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
0034 |     worker = threading.Thread(target=website.serve_forever, daemon=True)
0035 |     worker.start()
0036 |     url = f'http://127.0.0.1:{website.server_port}/'
0037 |     workspace = Path(tempfile.mkdtemp(prefix='cli-browser-acceptance-'))
0038 |     old_confirm = permissions.confirm_tool
0039 |     approvals = []
0040 |     def confirm(name, target, details=''):
0041 |         allowed = target == 'browser' and name == 'mcp_connect'
0042 |         if target == 'browser' and name.startswith('mcp__browser__'):
0043 |             args = json.loads(details.split('\n工具参数: ', 1)[1])
0044 |             allowed = name != 'mcp__browser__open_page' or args.get('url') == url
0045 |         approvals.append({'tool': name, 'allowed': allowed})
0046 |         return allowed
0047 |     permissions.confirm_tool = confirm
0048 |     report = {'workspace': str(workspace), 'model': model_config['model'], 'checks': {}, 'approvals': approvals}
0049 |     try:
0050 |         with use_workspace(workspace), MCPManager() as manager:
0051 |             connection = manager.connect('browser')
0052 |             if not connection['ok']:
0053 |                 raise RuntimeError(connection)
0054 |             messages = [{'role': 'user', 'content':
0055 |                 f'浏览器验收：真实调用 MCP 浏览器工具打开 {url}，向 Name 输入框填写 {marker}，'
0056 |                 '点击 Greet 按钮，读取并确认页面显示的 Hello 文字，然后保存截图。'
0057 |                 '每次操作使用上一份结果中的最新 ref。只操作这个本地网页，不使用其他工具。'
0058 |                 '最后告诉我页面实际显示的完整问候和截图路径。不要模拟工具结果。'}]
0059 |             history.append_messages(messages)
0060 |             reply = run_agent(messages)
0061 |             history.append_message({'role': 'assistant', 'content': reply})
0062 |             results = [(m['tool_name'], json.loads(m['content'])) for m in messages if m['role'] == 'tool']
0063 |             report['reply'] = reply
0064 |             report['tool_results'] = results
0065 |             checks = report['checks']
0066 |             for suffix in ('open_page', 'fill', 'click', 'screenshot'):
0067 |                 checks[suffix] = any(name == 'mcp__browser__' + suffix and result.get('ok') for name, result in results)
0068 |             checks['actual_page_greeting'] = any('Hello ' + marker in result.get('structured_content', {}).get('text', '') for _, result in results)
0069 |             shots = [result['structured_content']['path'] for name, result in results
0070 |                      if name == 'mcp__browser__screenshot' and result.get('ok')]
0071 |             checks['real_png_in_private_directory'] = bool(shots) and all(
0072 |                 Path(path).is_relative_to(workspace / '.ai-cli/.browser-artifacts') and Path(path).read_bytes().startswith(b'\x89PNG') for path in shots)
0073 |             checks['answer_matches_page'] = 'Hello ' + marker in reply
0074 |             checks['only_browser_tools'] = bool(results) and all(name.startswith('mcp__browser__') for name, _ in results)
0075 |             checks['no_failed_tools'] = all(result.get('ok') for _, result in results)
0076 |     finally:
0077 |         permissions.confirm_tool = old_confirm
0078 |         website.shutdown()
0079 |         website.server_close()
0080 |         worker.join()
0081 |         destination = ROOT / 'artifacts/browser/real_acceptance.json'
0082 |         destination.parent.mkdir(parents=True, exist_ok=True)
0083 |         destination.write_text(json.dumps(report, ensure_ascii=False, indent=2))
0084 |     print(json.dumps(report, ensure_ascii=False, indent=2))
0085 |     if not report['checks'] or not all(report['checks'].values()):
0086 |         raise SystemExit(1)
0087 | 
0088 | 
0089 | if __name__ == '__main__':
0090 |     main()
```
