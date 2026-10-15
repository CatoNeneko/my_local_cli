# tool_display.py：源码导读

显示开始/结果/diff，转义控制字符；不授权、不改变工具数据。

先读专题：[03-tools.md](../03-tools.md)。

实际源码：[tool_display.py](../../../tool_display.py)。

快照 SHA256：`c9854e253a95168f1fd5864284440c7484eb9efaa736664e5139abd3660efda4`；70 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import sys` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import unicodedata` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [safe_text](#safe-text) | [6](../../../tool_display.py#L6) | 显示中将控制字符转义，避免终端操纵。 |
| [short_text](#short-text) | [16](../../../tool_display.py#L16) | 转义后将换行显示为文字并按长度截摘要。 |
| [emit](#emit) | [21](../../../tool_display.py#L21) | TTY有色显示，否则普通print。 |
| [tool_started](#tool-started) | [31](../../../tool_display.py#L31) | 开始摘要仅显示工具名与少数安全字段。 |
| [tool_finished](#tool-finished) | [40](../../../tool_display.py#L40) | 基于真实结果展示状态、数量、输出与warning。 |
| [show_diff](#show-diff) | [63](../../../tool_display.py#L63) | 统计差异行、转义显示diff，提醒未获准不写。 |

<a id="safe-text"></a>
## safe_text

显示中将控制字符转义，避免终端操纵。

```python
def safe_text(value)
```

位置：[6行](../../../tool_display.py#L6) 至快照 13 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `value` | `未显式注解` | 正在检查的通用值；其实际类型以赋值与后续校验为准。 |

**调用表达式（静态提取，不含内层独立函数体）**：`''.join`、`format`、`ord`、`str`、`unicodedata.category`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 8 | `text` | `str(value)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 7 | 函数体 | 文档字符串：说明职责，不作为普通语句动作执行。 |
| 8 | 函数体 | 将 `str(value)` 赋给 `text`。 |
| 9 | 函数体 | 返回 `''.join((char if char in '\n\t' or unicodedata.category(char) not in ('Cc', 'Cf') else '\\u' + format(ord(char), '04x') for char in text))`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L9：`''.join((char if char in '\n\t' or unicodedata.category(char) not in ('Cc', 'Cf') else '\\u' + format(ord(char), '04x') for char in text))`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="short-text"></a>
## short_text

转义后将换行显示为文字并按长度截摘要。

```python
def short_text(value, limit=240)
```

位置：[16行](../../../tool_display.py#L16) 至快照 18 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `value` | `未显式注解` | 正在检查的通用值；其实际类型以赋值与后续校验为准。 |
| `limit` | `未显式注解` | 当前输入/输出上限，须看字符还是字节单位。 |

**调用表达式（静态提取，不含内层独立函数体）**：`len`、`safe_text`、`safe_text(value).replace`、`safe_text(value).replace('\n', '\\n').replace`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 17 | `text` | `safe_text(value).replace('\n', '\\n').replace('\t', '\\t')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 17 | 函数体 | 将 `safe_text(value).replace('\n', '\\n').replace('\t', '\\t')` 赋给 `text`。 |
| 18 | 函数体 | 返回 `text if len(text) <= limit else text[:limit] + '…（摘要截断）'`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L18：`text if len(text) <= limit else text[:limit] + '…（摘要截断）'`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="emit"></a>
## emit

TTY有色显示，否则普通print。

```python
def emit(text, color='')
```

位置：[21行](../../../tool_display.py#L21) 至快照 28 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `text` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `color` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`FormattedText`、`print`、`print_formatted_text`、`safe_text`、`sys.stdout.isatty`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 22 | `text` | `safe_text(text)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 22 | 函数体 | 将 `safe_text(text)` 赋给 `text`。 |
| 23 | 函数体 | 条件 `color and sys.stdout.isatty()`：真时执行body，假时进入else/后续。 |
| 24 | 函数体 / 条件为真 | 在此处导入依赖：`from prompt_toolkit import print_formatted_text`；局部导入可延迟加载或避免循环。 |
| 25 | 函数体 / 条件为真 | 在此处导入依赖：`from prompt_toolkit.formatted_text import FormattedText`；局部导入可延迟加载或避免循环。 |
| 26 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`print_formatted_text(FormattedText([(color, text)]))`。 |
| 28 | 函数体 / 条件为假/elif | 计算表达式/调用产生动作：`print(text, flush=True)`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="tool-started"></a>
## tool_started

开始摘要仅显示工具名与少数安全字段。

```python
def tool_started(name, arguments)
```

位置：[31行](../../../tool_display.py#L31) 至快照 37 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| `arguments` | `未显式注解` | 外部或模型提交的工具参数，必须经schema检查。 |

**调用表达式（静态提取，不含内层独立函数体）**：`emit`、`isinstance`、`short_text`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 32 | 函数体 | 计算表达式/调用产生动作：`emit('[执行中] ' + short_text(name), 'ansicyan')`。 |
| 33 | 函数体 | 条件 `isinstance(arguments, dict)`：真时执行body，假时进入else/后续。 |
| 35 | 函数体 / 条件为真 | 遍历 `(('path', '目标'), ('keyword', '关键词'), ('glob', '文件过滤'))`，每次绑定 `(key, label)`。 |
| 36 | 函数体 / 条件为真 / 循环每次 | 条件 `key in arguments`：真时执行body，假时进入else/后续。 |
| 37 | 函数体 / 条件为真 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`emit('  ' + label + ': ' + short_text(arguments[key]))`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="tool-finished"></a>
## tool_finished

基于真实结果展示状态、数量、输出与warning。

```python
def tool_finished(name, result)
```

位置：[40行](../../../tool_display.py#L40) 至快照 60 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| `result` | `未显式注解` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |

**调用表达式（静态提取，不含内层独立函数体）**：`emit`、`isinstance`、`len`、`result.get`、`short_text`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 41 | `succeeded` | `result['ok']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 42 | `label` | `'已取消' if result.get('cancelled') else '成功' if succeeded else '失败/未执行'` | 候选显示标签/提示前缀，与真正返回value分开。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 41 | 函数体 | 将 `result['ok']` 赋给 `succeeded`。 |
| 42 | 函数体 | 将 `'已取消' if result.get('cancelled') else '成功' if succeeded else '失败/未执行'` 赋给 `label`。 |
| 43 | 函数体 | 计算表达式/调用产生动作：`emit('[' + label + '] ' + short_text(name), 'ansigreen' if succeeded else 'ansired')`。 |
| 44 | 函数体 | 条件 `not succeeded`：真时执行body，假时进入else/后续。 |
| 45 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`emit('  原因: ' + short_text(result.get('error', '工具未成功')))`。 |
| 46 | 函数体 / 条件为假/elif | 条件 `'message' in result`：真时执行body，假时进入else/后续。 |
| 47 | 函数体 / 条件为假/elif / 条件为真 | 计算表达式/调用产生动作：`emit('  ' + short_text(result['message']))`。 |
| 48 | 函数体 / 条件为假/elif / 条件为假/elif | 条件 `isinstance(result.get('content'), str)`：真时执行body，假时进入else/后续。 |
| 49 | 函数体 / 条件为假/elif / 条件为假/elif / 条件为真 | 计算表达式/调用产生动作：`emit('  返回文字: ' + str(len(result['content'])) + ' 字符')`。 |
| 50 | 函数体 | 遍历 `(('matches', '匹配行'), ('entries', '目录项'))`，每次绑定 `(key, label)`。 |
| 51 | 函数体 / 循环每次 | 条件 `isinstance(result.get(key), list)`：真时执行body，假时进入else/后续。 |
| 52 | 函数体 / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`emit('  ' + label + ': ' + str(len(result[key])))`。 |
| 53 | 函数体 | 条件 `'exit_code' in result`：真时执行body，假时进入else/后续。 |
| 54 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`emit('  退出码: ' + short_text(result['exit_code']))`。 |
| 55 | 函数体 | 条件 `isinstance(result.get('output'), str) and result['output']`：真时执行body，假时进入else/后续。 |
| 56 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`emit('  测试输出摘要: ' + short_text(result['output'], 800))`。 |
| 57 | 函数体 | 条件 `result.get('truncated') or result.get('output_truncated')`：真时执行body，假时进入else/后续。 |
| 58 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`emit('  注意: 工具返回的数据已截断', 'ansiyellow')`。 |
| 59 | 函数体 | 条件 `result.get('hook_warning')`：真时执行body，假时进入else/后续。 |
| 60 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`emit('  Hook 警告: ' + short_text(result['hook_warning']), 'ansiyellow')`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="show-diff"></a>
## show_diff

统计差异行、转义显示diff，提醒未获准不写。

```python
def show_diff(diff)
```

位置：[63行](../../../tool_display.py#L63) 至快照 70 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `diff` | `未显式注解` | 拟改动的unified diff文字，用于显示与独立审查。 |

**调用表达式（静态提取，不含内层独立函数体）**：`diff.splitlines`、`emit`、`line.startswith`、`str`、`sum`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 64 | `added` | `sum((line.startswith('+') and (not line.startswith('+++')) for line in diff.splitlines()))` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 65 | `removed` | `sum((line.startswith('-') and (not line.startswith('---')) for line in diff.splitlines()))` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 68 | `color` | `'ansigreen' if line.startswith('+') else 'ansired' if line.startswith('-') else ''` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 64 | 函数体 | 将 `sum((line.startswith('+') and (not line.startswith('+++')) for line in diff.splitlines()))` 赋给 `added`。 |
| 65 | 函数体 | 将 `sum((line.startswith('-') and (not line.startswith('---')) for line in diff.splitlines()))` 赋给 `removed`。 |
| 66 | 函数体 | 计算表达式/调用产生动作：`emit('[待审查修改] +' + str(added) + ' / -' + str(removed) + ' 行', 'ansiyellow')`。 |
| 67 | 函数体 | 遍历 `diff.splitlines()`，每次绑定 `line`。 |
| 68 | 函数体 / 循环每次 | 将 `'ansigreen' if line.startswith('+') else 'ansired' if line.startswith('-') else ''` 赋给 `color`。 |
| 69 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`emit(line, color)`。 |
| 70 | 函数体 | 计算表达式/调用产生动作：`emit('[审查结束] 审批通过后才会写入；以上控制字符已转义显示。', 'ansiyellow')`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- 推导式/生成器表达式：循环建容器或逐个产生：L9, L64, L65。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """工具状态与修改审查的终端展示；不改变工具结果或授权。"""
0002 | import sys
0003 | import unicodedata
0004 | 
0005 | 
0006 | def safe_text(value):
0007 |     """把控制字符显示为转义文字，避免文件内容操纵终端。"""
0008 |     text = str(value)
0009 |     return "".join(
0010 |         char if char in "\n\t" or unicodedata.category(char) not in ("Cc", "Cf")
0011 |         else "\\u" + format(ord(char), "04x")
0012 |         for char in text
0013 |     )
0014 | 
0015 | 
0016 | def short_text(value, limit=240):
0017 |     text = safe_text(value).replace("\n", "\\n").replace("\t", "\\t")
0018 |     return text if len(text) <= limit else text[:limit] + "…（摘要截断）"
0019 | 
0020 | 
0021 | def emit(text, color=""):
0022 |     text = safe_text(text)
0023 |     if color and sys.stdout.isatty():
0024 |         from prompt_toolkit import print_formatted_text
0025 |         from prompt_toolkit.formatted_text import FormattedText
0026 |         print_formatted_text(FormattedText([(color, text)]))
0027 |     else:
0028 |         print(text, flush=True)
0029 | 
0030 | 
0031 | def tool_started(name, arguments):
0032 |     emit("[执行中] " + short_text(name), "ansicyan")
0033 |     if isinstance(arguments, dict):
0034 |         # 不打印整份 new_content 或未知 MCP 参数中的敏感内容。
0035 |         for key, label in (("path", "目标"), ("keyword", "关键词"), ("glob", "文件过滤")):
0036 |             if key in arguments:
0037 |                 emit("  " + label + ": " + short_text(arguments[key]))
0038 | 
0039 | 
0040 | def tool_finished(name, result):
0041 |     succeeded = result["ok"]
0042 |     label = '已取消' if result.get('cancelled') else "成功" if succeeded else "失败/未执行"
0043 |     emit("[" + label + "] " + short_text(name), "ansigreen" if succeeded else "ansired")
0044 |     if not succeeded:
0045 |         emit("  原因: " + short_text(result.get("error", "工具未成功")))
0046 |     elif "message" in result:
0047 |         emit("  " + short_text(result["message"]))
0048 |     elif isinstance(result.get("content"), str):
0049 |         emit("  返回文字: " + str(len(result["content"])) + " 字符")
0050 |     for key, label in (("matches", "匹配行"), ("entries", "目录项")):
0051 |         if isinstance(result.get(key), list):
0052 |             emit("  " + label + ": " + str(len(result[key])))
0053 |     if "exit_code" in result:
0054 |         emit("  退出码: " + short_text(result["exit_code"]))
0055 |     if isinstance(result.get("output"), str) and result["output"]:
0056 |         emit("  测试输出摘要: " + short_text(result["output"], 800))
0057 |     if result.get("truncated") or result.get("output_truncated"):
0058 |         emit("  注意: 工具返回的数据已截断", "ansiyellow")
0059 |     if result.get("hook_warning"):
0060 |         emit("  Hook 警告: " + short_text(result["hook_warning"]), "ansiyellow")
0061 | 
0062 | 
0063 | def show_diff(diff):
0064 |     added = sum(line.startswith("+") and not line.startswith("+++") for line in diff.splitlines())
0065 |     removed = sum(line.startswith("-") and not line.startswith("---") for line in diff.splitlines())
0066 |     emit("[待审查修改] +" + str(added) + " / -" + str(removed) + " 行", "ansiyellow")
0067 |     for line in diff.splitlines():
0068 |         color = "ansigreen" if line.startswith("+") else "ansired" if line.startswith("-") else ""
0069 |         emit(line, color)
0070 |     emit("[审查结束] 审批通过后才会写入；以上控制字符已转义显示。", "ansiyellow")
```
