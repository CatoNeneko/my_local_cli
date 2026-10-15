# console_output.py：源码导读

每次模型响应的流式显示状态与最终输出去重。

先读专题：[02-agent.md](../02-agent.md)。

实际源码：[console_output.py](../../../console_output.py)。

快照 SHA256：`a5b738b5c390e75f9e6ef86f7c11655fe4451eb61210b79cec2ac3d26d25283a`；25 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [ConsoleOutput.__init__](#consoleoutput---init--) | [3](../../../console_output.py#L3) | 构造对象的初始状态；调用类创建对象时自动执行。 |
| [ConsoleOutput.begin](#consoleoutput-begin) | [6](../../../console_output.py#L6) | 清空当前响应累计content并重置started。 |
| [ConsoleOutput.write](#consoleoutput-write) | [10](../../../console_output.py#L10) | 收到文字时打印并flush，记录已显示文字，用于最终去重。 |
| [ConsoleOutput.end](#consoleoutput-end) | [19](../../../console_output.py#L19) | 已开始显示才补换行。 |
| [ConsoleOutput.final](#consoleoutput-final) | [23](../../../console_output.py#L23) | 未流式显示或返回与已显示不同才打印最终reply。 |

<a id="consoleoutput---init--"></a>
## ConsoleOutput.__init__

构造对象的初始状态；self上的字段会在后续方法中继续使用。

```python
def __init__(self)
```

位置：[3行](../../../console_output.py#L3) 至快照 4 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：`self.begin`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 4 | 函数体 | 计算表达式/调用产生动作：`self.begin()`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="consoleoutput-begin"></a>
## ConsoleOutput.begin

清空当前响应累计content并重置started。

```python
def begin(self)
```

位置：[6行](../../../console_output.py#L6) 至快照 8 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：无直接调用。

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 7 | `self.content` | `''` | 文件正文、消息文字或累计响应；看role与来源。 |
| 8 | `self.started` | `False` | UI是否开始流式打印，或连接已初始化返回的句柄，依模块。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 7 | 函数体 | 将 `''` 赋给 `self.content`。 |
| 8 | 函数体 | 将 `False` 赋给 `self.started`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="consoleoutput-write"></a>
## ConsoleOutput.write

收到文字时打印并flush，记录已显示文字，用于最终去重。

```python
def write(self, text)
```

位置：[10行](../../../console_output.py#L10) 至快照 17 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `text` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`print`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 15 | `self.started` | `True` | UI是否开始流式打印，或连接已初始化返回的句柄，依模块。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 11 | 函数体 | 条件 `not text`：真时执行body，假时进入else/后续。 |
| 12 | 函数体 / 条件为真 | 返回 `None`，结束当前函数；具体分支见完整源码。 |
| 13 | 函数体 | 条件 `not self.started`：真时执行body，假时进入else/后续。 |
| 14 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`print('assistant: ', end='', flush=True)`。 |
| 15 | 函数体 / 条件为真 | 将 `True` 赋给 `self.started`。 |
| 16 | 函数体 | 更新已有变量：`self.content += text`。 |
| 17 | 函数体 | 计算表达式/调用产生动作：`print(text, end='', flush=True)`。 |

**实际返回分支**：

- L12：`None`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="consoleoutput-end"></a>
## ConsoleOutput.end

已开始显示才补换行。

```python
def end(self)
```

位置：[19行](../../../console_output.py#L19) 至快照 21 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：`print`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 20 | 函数体 | 条件 `self.started`：真时执行body，假时进入else/后续。 |
| 21 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`print()`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="consoleoutput-final"></a>
## ConsoleOutput.final

未流式显示或返回与已显示不同才打印最终reply。

```python
def final(self, reply)
```

位置：[23行](../../../console_output.py#L23) 至快照 25 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `reply` | `未显式注解` | 模型最终文字或明确终止说明。 |

**调用表达式（静态提取，不含内层独立函数体）**：`print`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 24 | 函数体 | 条件 `not self.started or reply != self.content`：真时执行body，假时进入else/后续。 |
| 25 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`print('assistant:', reply)`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- class：对象状态与方法/继承：L2。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """终端输出状态：每轮响应重置，避免流式显示后重复打印最终文字。"""
0002 | class ConsoleOutput:
0003 |     def __init__(self):
0004 |         self.begin()
0005 | 
0006 |     def begin(self):
0007 |         self.content = ""
0008 |         self.started = False
0009 | 
0010 |     def write(self, text):
0011 |         if not text:
0012 |             return
0013 |         if not self.started:
0014 |             print("assistant: ", end="", flush=True)
0015 |             self.started = True
0016 |         self.content += text
0017 |         print(text, end="", flush=True)
0018 | 
0019 |     def end(self):
0020 |         if self.started:
0021 |             print()
0022 | 
0023 |     def final(self, reply):
0024 |         if not self.started or reply != self.content:
0025 |             print("assistant:", reply)
```
