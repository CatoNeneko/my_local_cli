# history.py：源码导读

JSONL逐行恢复与追加；基本记录验证，链完整性由上下文模块检查。

先读专题：[04-context.md](../04-context.md)。

实际源码：[history.py](../../../history.py)。

快照 SHA256：`3f2bcee7dd21339ccd9261ca547e54bf0007fb531ddaab91cb435822dfa7ef65`；62 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 1 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 2 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `HISTORY_PATH = Path(__file__).resolve().parent / 'history.jsonl'` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [clear_history](#clear-history) | [8](../../../history.py#L8) | 用w模式将当前历史文件清空。 |
| [append_messages](#append-messages) | [14](../../../history.py#L14) | 先序列化整批消息为JSONL，再追加磁盘。 |
| [append_message](#append-message) | [22](../../../history.py#L22) | 单条消息包装成列表复用追加。 |
| [load_history](#load-history) | [26](../../../history.py#L26) | 逐行恢复JSONL，跳过坏行和基本字段错误，返回列表。 |

<a id="clear-history"></a>
## clear_history

用w模式将当前历史文件清空。

```python
def clear_history()
```

位置：[8行](../../../history.py#L8) 至快照 11 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`HISTORY_PATH.parent.mkdir`、`open`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 9 | 函数体 | 计算表达式/调用产生动作：`HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)`。 |
| 10 | 函数体 | 进入资源/状态范围：`open(HISTORY_PATH, 'w', encoding='utf-8')` 绑定 `file`；退出执行清理。 |
| 11 | 函数体 / with范围 | pass占位，无动作。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="append-messages"></a>
## append_messages

先序列化整批消息为JSONL，再追加磁盘。

```python
def append_messages(messages)
```

位置：[14行](../../../history.py#L14) 至快照 19 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `messages` | `未显式注解` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`''.join`、`HISTORY_PATH.parent.mkdir`、`file.write`、`json.dumps`、`open`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 16 | `text` | `''.join((json.dumps(message, ensure_ascii=False) + '\n' for message in messages))` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 16 | 函数体 | 将 `''.join((json.dumps(message, ensure_ascii=False) + '\n' for message in messages))` 赋给 `text`。 |
| 17 | 函数体 | 计算表达式/调用产生动作：`HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)`。 |
| 18 | 函数体 | 进入资源/状态范围：`open(HISTORY_PATH, 'a', encoding='utf-8')` 绑定 `file`；退出执行清理。 |
| 19 | 函数体 / with范围 | 计算表达式/调用产生动作：`file.write(text)`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="append-message"></a>
## append_message

单条消息包装成列表复用追加。

```python
def append_message(message)
```

位置：[22行](../../../history.py#L22) 至快照 23 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `message` | `未显式注解` | 单条聊天/协议消息字典；角色和字段随当前分支而定。 |

**调用表达式（静态提取，不含内层独立函数体）**：`append_messages`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 23 | 函数体 | 计算表达式/调用产生动作：`append_messages([message])`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="load-history"></a>
## load_history

逐行恢复JSONL，跳过坏行和基本字段错误，返回列表。

```python
def load_history(path=None)
```

位置：[26行](../../../history.py#L26) 至快照 62 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |

**调用表达式（静态提取，不含内层独立函数体）**：`isinstance`、`json.loads`、`line.strip`、`message.get`、`messages.append`、`open`、`print`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 27 | `messages` | `[]` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |
| 31 | `line` | `line.strip()` | 当前行文字或网络逐行数据。 |
| 35 | `message` | `json.loads(line)` | 单条聊天/协议消息字典；角色和字段随当前分支而定。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 27 | 函数体 | 将 `[]` 赋给 `messages`。 |
| 28 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 29 | 函数体 / try | 进入资源/状态范围：`open(HISTORY_PATH if path is None else path, 'r', encoding='utf-8')` 绑定 `file`；退出执行清理。 |
| 30 | 函数体 / try / with范围 | 遍历 `file`，每次绑定 `line`。 |
| 31 | 函数体 / try / with范围 / 循环每次 | 将 `line.strip()` 赋给 `line`。 |
| 32 | 函数体 / try / with范围 / 循环每次 | 条件 `not line`：真时执行body，假时进入else/后续。 |
| 33 | 函数体 / try / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 34 | 函数体 / try / with范围 / 循环每次 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 35 | 函数体 / try / with范围 / 循环每次 / try | 将 `json.loads(line)` 赋给 `message`。 |
| 36 | 函数体 / try / with范围 / 循环每次 | except json.JSONDecodeError：只处理匹配类型的异常。 |
| 37 | 函数体 / try / with范围 / 循环每次 / except json.JSONDecodeError | 计算表达式/调用产生动作：`print('跳过一条损坏的记录')`。 |
| 38 | 函数体 / try / with范围 / 循环每次 / except json.JSONDecodeError | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 39 | 函数体 / try / with范围 / 循环每次 | 条件 `not isinstance(message, dict)`：真时执行body，假时进入else/后续。 |
| 40 | 函数体 / try / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('跳过一条不是字典的记录')`。 |
| 41 | 函数体 / try / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 42 | 函数体 / try / with范围 / 循环每次 | 条件 `'role' not in message or 'content' not in message`：真时执行body，假时进入else/后续。 |
| 43 | 函数体 / try / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('跳过一条缺少字段的记录')`。 |
| 44 | 函数体 / try / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 45 | 函数体 / try / with范围 / 循环每次 | 条件 `not isinstance(message['content'], str)`：真时执行body，假时进入else/后续。 |
| 46 | 函数体 / try / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('跳过一条非文字记录')`。 |
| 47 | 函数体 / try / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 48 | 函数体 / try / with范围 / 循环每次 | 条件 `message['role'] not in ('user', 'assistant', 'tool')`：真时执行body，假时进入else/后续。 |
| 49 | 函数体 / try / with范围 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`print('跳过一条身份非法记录')`。 |
| 50 | 函数体 / try / with范围 / 循环每次 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 51 | 函数体 / try / with范围 / 循环每次 | 条件 `message['role'] == 'tool'`：真时执行body，假时进入else/后续。 |
| 52 | 函数体 / try / with范围 / 循环每次 / 条件为真 | 条件 `not isinstance(message.get('tool_name'), str) or not message['tool_name']`：真时执行body，假时进入else/后续。 |
| 53 | 函数体 / try / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print('跳过一条缺少工具名称的记录')`。 |
| 54 | 函数体 / try / with范围 / 循环每次 / 条件为真 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 55 | 函数体 / try / with范围 / 循环每次 | 条件 `'tool_calls' in message`：真时执行body，假时进入else/后续。 |
| 56 | 函数体 / try / with范围 / 循环每次 / 条件为真 | 条件 `message['role'] != 'assistant' or not isinstance(message['tool_calls'], list)`：真时执行body，假时进入else/后续。 |
| 57 | 函数体 / try / with范围 / 循环每次 / 条件为真 / 条件为真 | 计算表达式/调用产生动作：`print('跳过一条工具调用格式错误的记录')`。 |
| 58 | 函数体 / try / with范围 / 循环每次 / 条件为真 / 条件为真 | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 59 | 函数体 / try / with范围 / 循环每次 | 计算表达式/调用产生动作：`messages.append(message)`。 |
| 60 | 函数体 | except FileNotFoundError：只处理匹配类型的异常。 |
| 61 | 函数体 / except FileNotFoundError | pass占位，无动作。 |
| 62 | 函数体 | 返回 `messages`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L62：`messages`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- with/yield：资源/状态生命周期或逐个生成：L10, L18, L29。
- try/except/finally：异常与保证清理：L28, L34。
- 推导式/生成器表达式：循环建容器或逐个产生：L16。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | import json
0002 | from pathlib import Path
0003 | 
0004 | 
0005 | HISTORY_PATH = Path(__file__).resolve().parent / "history.jsonl"
0006 | 
0007 | 
0008 | def clear_history():
0009 |     HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
0010 |     with open(HISTORY_PATH, "w", encoding="utf-8") as file:
0011 |         pass
0012 | 
0013 | 
0014 | def append_messages(messages):
0015 |     # 先序列化完整的一轮，成功后再追加；不在模型请求阶段写半条调用。
0016 |     text = "".join(json.dumps(message, ensure_ascii=False) + "\n" for message in messages)
0017 |     HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
0018 |     with open(HISTORY_PATH, "a", encoding="utf-8") as file:
0019 |         file.write(text)
0020 | 
0021 | 
0022 | def append_message(message):
0023 |     append_messages([message])
0024 | 
0025 | 
0026 | def load_history(path=None):
0027 |     messages = []
0028 |     try:
0029 |         with open(HISTORY_PATH if path is None else path, "r", encoding="utf-8") as file:
0030 |             for line in file:
0031 |                 line = line.strip()
0032 |                 if not line:
0033 |                     continue
0034 |                 try:
0035 |                     message = json.loads(line)
0036 |                 except json.JSONDecodeError:
0037 |                     print("跳过一条损坏的记录")
0038 |                     continue
0039 |                 if not isinstance(message, dict):
0040 |                     print("跳过一条不是字典的记录")
0041 |                     continue
0042 |                 if "role" not in message or "content" not in message:
0043 |                     print("跳过一条缺少字段的记录")
0044 |                     continue
0045 |                 if not isinstance(message["content"], str):
0046 |                     print("跳过一条非文字记录")
0047 |                     continue
0048 |                 if message["role"] not in ("user", "assistant", "tool"):
0049 |                     print("跳过一条身份非法记录")
0050 |                     continue
0051 |                 if message["role"] == "tool":
0052 |                     if not isinstance(message.get("tool_name"), str) or not message["tool_name"]:
0053 |                         print("跳过一条缺少工具名称的记录")
0054 |                         continue
0055 |                 if "tool_calls" in message:
0056 |                     if message["role"] != "assistant" or not isinstance(message["tool_calls"], list):
0057 |                         print("跳过一条工具调用格式错误的记录")
0058 |                         continue
0059 |                 messages.append(message)
0060 |     except FileNotFoundError:
0061 |         pass
0062 |     return messages
```
