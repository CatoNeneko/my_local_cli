# command_help.py：源码导读

命令帮助声明和打印；不是实际命令分派器。实际分派在script。

先读专题：[07-terminal.md](../07-terminal.md)。

实际源码：[command_help.py](../../../command_help.py)。

快照 SHA256：`c4dce0bdb5857836425d1f3d16bfc18bae634b1e1bd617902e1f5b79159f8a5a`；48 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `COMMANDS = {'/browser': ('<open\|read\|click\|fill\|wait\|screenshot\|close>', '基础无头浏览器，使用页面返回的 ref 操作'), '/compact': ('[status\|auto on\|auto off]', '手动压缩或管理自动上下文压缩'), '/approva…（见完整源码）` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [show_help](#show-help) | [40](../../../command_help.py#L40) | 打印COMMANDS说明。 |

<a id="show-help"></a>
## show_help

打印COMMANDS说明。

```python
def show_help()
```

位置：[40行](../../../command_help.py#L40) 至快照 48 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`(name + ' ' + arguments).ljust`、`COMMANDS.items`、`print`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 41 | 函数体 | 计算表达式/调用产生动作：`print('直接输入自然语言任务即可，命令主要用于查看和管理。')`。 |
| 42 | 函数体 | 遍历 `COMMANDS.items()`，每次绑定 `(name, (arguments, description))`。 |
| 43 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`print((name + ' ' + arguments).ljust(38) + description)`。 |
| 44 | 函数体 | 计算表达式/调用产生动作：`print('增强输入：Enter 发送，Alt+Enter 换行；候选出现时 ↑/↓ 选择、Enter 接受，再 Enter 发送。')`。 |
| 45 | 函数体 | 计算表达式/调用产生动作：`print('/read、/attach、/search、/grep 支持路径补全；/files 输入关键词筛选、Tab 多选，Esc 取消。')`。 |
| 46 | 函数体 | 计算表达式/调用产生动作：`print('没有候选时 ↑/↓ 浏览输入历史；权限确认默认拒绝，可用方向键或 y/n 选择。')`。 |
| 47 | 函数体 | 计算表达式/调用产生动作：`print('空闲 Ctrl+C 或 Ctrl+D 退出；聊天生成中 Ctrl+C 取消当前生成。')`。 |
| 48 | 函数体 | 计算表达式/调用产生动作：`print('工具执行中 Ctrl+C 停止当前任务并返回输入；已完成的写入不会回滚。')`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。


## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """帮助和命令补全共用的命令说明。"""
0002 | COMMANDS = {
0003 |     '/browser': ('<open|read|click|fill|wait|screenshot|close>', '基础无头浏览器，使用页面返回的 ref 操作'),
0004 |     '/compact': ('[status|auto on|auto off]', '手动压缩或管理自动上下文压缩'),
0005 |     '/approval': ('[auto|manual]', '查看或切换可信审批模式'),
0006 |     '/apply': ('<任务 ID> <建议 ID>', '审批并应用子代理文件建议'),
0007 |     '/pty': ('<命令及参数>', '启动沙箱 PTY 任务；Python 使用 python'),
0008 |     '/agent': ('<任务描述>', '启动独立只读子代理'),
0009 |     '/tasks': ('', '列出当前进程任务'),
0010 |     '/task': ('<任务 ID>', '查看输出和结果'),
0011 |     '/send': ('<任务 ID> <文字>', '向 PTY 发送一行输入'),
0012 |     '/cancel': ('<任务 ID>', '终止任务进程组'),
0013 |     "/help": ("", "查看帮助"),
0014 |     "/exit": ("", "退出并关闭连接"),
0015 |     "/history": ("", "查看当前历史"),
0016 |     "/clear": ("", "清空当前会话历史"),
0017 |     "/save": ("", "导出当前会话 JSON"),
0018 |     "/sessions": ("", "列出会话"),
0019 |     "/session": ("<名称>", "查看、切换或创建会话"),
0020 |     "/session rename": ("<新名称>", "重命名当前会话"),
0021 |     "/context": ("", "查看上下文预算"),
0022 |     "/model": ("[名称]", "查看或切换模型"),
0023 |     "/stream": ("[on/off]", "查看或切换流式输出"),
0024 |     "/read": ("<路径>", "读取文件"),
0025 |     "/attach": ("<路径>", "把文件加入聊天"),
0026 |     "/files": ("", "模糊搜索文件；Tab 多选，Enter 添加附件"),
0027 |     "/browse": ("", "逐层浏览目录并添加单个附件"),
0028 |     "/search": ("<文件> <关键词>", "搜索单文件"),
0029 |     "/grep": ("<目录> <关键词>", "递归搜索项目"),
0030 |     "/instructions": ("", "查看项目规则"),
0031 |     "/skills": ("", "查看 Skills"),
0032 |     "/skill": ("<名称>", "启用 Skill"),
0033 |     "/skill clear": ("", "停用当前会话 Skills"),
0034 |     "/skill generate": ("<名称> <用途>", "生成、审查并保存 Skill"),
0035 |     "/mcp tools": ("", "查看 MCP 工具"),
0036 |     "/mcp refresh": ("", "刷新或重连 MCP"),
0037 | }
0038 | 
0039 | 
0040 | def show_help():
0041 |     print("直接输入自然语言任务即可，命令主要用于查看和管理。")
0042 |     for name, (arguments, description) in COMMANDS.items():
0043 |         print((name + " " + arguments).ljust(38) + description)
0044 |     print("增强输入：Enter 发送，Alt+Enter 换行；候选出现时 ↑/↓ 选择、Enter 接受，再 Enter 发送。")
0045 |     print("/read、/attach、/search、/grep 支持路径补全；/files 输入关键词筛选、Tab 多选，Esc 取消。")
0046 |     print("没有候选时 ↑/↓ 浏览输入历史；权限确认默认拒绝，可用方向键或 y/n 选择。")
0047 |     print("空闲 Ctrl+C 或 Ctrl+D 退出；聊天生成中 Ctrl+C 取消当前生成。")
0048 |     print("工具执行中 Ctrl+C 停止当前任务并返回输入；已完成的写入不会回滚。")
```
