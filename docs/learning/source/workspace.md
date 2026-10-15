# workspace.py：源码导读

将本次运行绑定到目标项目并在退出恢复模块状态；安装目录保持固定。

先读专题：[04-context.md](../04-context.md)。

实际源码：[workspace.py](../../../workspace.py)。

快照 SHA256：`73e0afc62a3eb8f241d3a977952185ee2ded8c5a433cc88a2a9fabf563302741`；46 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `from contextlib import contextmanager` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `APP_ROOT = Path(__file__).resolve().parent` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [use_workspace](#use-workspace) | [9](../../../workspace.py#L9) | 临时绑定各模块项目/状态路径与规则/Skill状态，退出恢复。 |

<a id="use-workspace"></a>
## use_workspace

临时绑定各模块项目/状态路径与规则/Skill状态，退出恢复。

```python
def use_workspace(directory)
```

位置：[9行](../../../workspace.py#L9) 至快照 46 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `directory` | `未显式注解` | 当前目录路径，遍历/候选/会话使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`Path(directory).expanduser`、`Path(directory).expanduser().resolve`、`ValueError`、`active_skills.clear`、`active_skills.update`、`dict`、`instruction_state.clear`、`instruction_state.update`、`path.exists`、`path.is_dir`、`path.is_file`、`path.is_symlink`、`root.is_dir`、`state.exists`、`state.is_dir`、`state.is_symlink`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 17 | `root` | `Path(directory).expanduser().resolve()` | 本次目录扫描/工作项目根。 |
| 21 | `state` | `root if root == APP_ROOT else root / '.ai-cli'` | 状态目录/有效摘要状态，当前表达式决定。 |
| 32 | `old` | `(permissions.PROJECT_ROOT, sandbox.PROJECT_ROOT, history.HISTORY_PATH, audit.LOG_PATH, dict(instruction_state), dict(active_skills…（见完整源码）` | 待摘要的旧消息或旧值；具体以赋值为准。 |
| 34 | `permissions.PROJECT_ROOT,sandbox.PROJECT_ROOT` | `root` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 35 | `history.HISTORY_PATH` | `state / 'history.jsonl'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 36 | `audit.LOG_PATH` | `state / 'tool_events.jsonl'` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 42 | `(permissions.PROJECT_ROOT, sandbox.PROJECT_ROOT, history.HISTORY_…（见完整源码）` | `old[:4]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 10 | 函数体 | 在此处导入依赖：`import audit`；局部导入可延迟加载或避免循环。 |
| 11 | 函数体 | 在此处导入依赖：`import history`；局部导入可延迟加载或避免循环。 |
| 12 | 函数体 | 在此处导入依赖：`import permissions`；局部导入可延迟加载或避免循环。 |
| 13 | 函数体 | 在此处导入依赖：`import sandbox`；局部导入可延迟加载或避免循环。 |
| 14 | 函数体 | 在此处导入依赖：`from project_instructions import instruction_state`；局部导入可延迟加载或避免循环。 |
| 15 | 函数体 | 在此处导入依赖：`from skills import active_skills`；局部导入可延迟加载或避免循环。 |
| 17 | 函数体 | 将 `Path(directory).expanduser().resolve()` 赋给 `root`。 |
| 18 | 函数体 | 条件 `not root.is_dir()`：真时执行body，假时进入else/后续。 |
| 19 | 函数体 / 条件为真 | 抛出 `ValueError('工作目录不存在或不是目录: ' + str(root))`。 |
| 21 | 函数体 | 将 `root if root == APP_ROOT else root / '.ai-cli'` 赋给 `state`。 |
| 22 | 函数体 | 条件 `state.is_symlink()`：真时执行body，假时进入else/后续。 |
| 23 | 函数体 / 条件为真 | 抛出 `ValueError('项目状态目录不能是符号链接')`。 |
| 24 | 函数体 | 条件 `state.exists() and (not state.is_dir())`：真时执行body，假时进入else/后续。 |
| 25 | 函数体 / 条件为真 | 抛出 `ValueError('项目状态路径不是目录: ' + str(state))`。 |
| 26 | 函数体 | 遍历 `(state / 'history.jsonl', state / 'tool_events.jsonl', state / 'sessions')`，每次绑定 `path`。 |
| 27 | 函数体 / 循环每次 | 条件 `path.is_symlink()`：真时执行body，假时进入else/后续。 |
| 28 | 函数体 / 循环每次 / 条件为真 | 抛出 `ValueError('项目状态路径不能是符号链接: ' + str(path))`。 |
| 29 | 函数体 / 循环每次 | 条件 `path.exists() and (path.name == 'sessions' and (not path.is_dir()) or (path.name != 'sessions' and (not path.is_file())))`：真时执行body，假时进入else/后续。 |
| 31 | 函数体 / 循环每次 / 条件为真 | 抛出 `ValueError('项目状态路径类型无效: ' + str(path))`。 |
| 32 | 函数体 | 将 `(permissions.PROJECT_ROOT, sandbox.PROJECT_ROOT, history.HISTORY_PATH, audit.LOG_PATH, dict(instruction_state), dict(active_skills))` 赋给 `old`。 |
| 34 | 函数体 | 将 `root` 赋给 `permissions.PROJECT_ROOT`, `sandbox.PROJECT_ROOT`。 |
| 35 | 函数体 | 将 `state / 'history.jsonl'` 赋给 `history.HISTORY_PATH`。 |
| 36 | 函数体 | 将 `state / 'tool_events.jsonl'` 赋给 `audit.LOG_PATH`。 |
| 37 | 函数体 | 计算表达式/调用产生动作：`active_skills.clear()`。 |
| 38 | 函数体 | 计算表达式/调用产生动作：`instruction_state.update(status='missing', content='', message='尚未加载项目规则')`。 |
| 39 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 40 | 函数体 / try | yield让出值/控制权；上下文管理器中表示进入with内部代码。 |
| 42 | 函数体 / finally保证清理 | 将 `old[:4]` 赋给 `(permissions.PROJECT_ROOT, sandbox.PROJECT_ROOT, history.HISTORY_PATH, audit.LOG_PATH)`。 |
| 43 | 函数体 / finally保证清理 | 计算表达式/调用产生动作：`instruction_state.clear()`。 |
| 44 | 函数体 / finally保证清理 | 计算表达式/调用产生动作：`instruction_state.update(old[4])`。 |
| 45 | 函数体 / finally保证清理 | 计算表达式/调用产生动作：`active_skills.clear()`。 |
| 46 | 函数体 / finally保证清理 | 计算表达式/调用产生动作：`active_skills.update(old[5])`。 |

**实际返回分支**：

- 这是生成器/上下文管理器式控制，含yield；不按普通return结果理解。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L39。
- with/yield：资源/状态生命周期或逐个生成：L40。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """一次 CLI 运行的项目路径绑定，与助手安装目录和运行环境分开。"""
0002 | from contextlib import contextmanager
0003 | from pathlib import Path
0004 | 
0005 | APP_ROOT = Path(__file__).resolve().parent
0006 | 
0007 | 
0008 | @contextmanager
0009 | def use_workspace(directory):
0010 |     import audit
0011 |     import history
0012 |     import permissions
0013 |     import sandbox
0014 |     from project_instructions import instruction_state
0015 |     from skills import active_skills
0016 | 
0017 |     root = Path(directory).expanduser().resolve()
0018 |     if not root.is_dir():
0019 |         raise ValueError('工作目录不存在或不是目录: ' + str(root))
0020 |     # 保持原仓库历史位置兼容；外部项目使用被工具屏蔽的私有目录。
0021 |     state = root if root == APP_ROOT else root / '.ai-cli'
0022 |     if state.is_symlink():
0023 |         raise ValueError('项目状态目录不能是符号链接')
0024 |     if state.exists() and not state.is_dir():
0025 |         raise ValueError('项目状态路径不是目录: ' + str(state))
0026 |     for path in (state / 'history.jsonl', state / 'tool_events.jsonl', state / 'sessions'):
0027 |         if path.is_symlink():
0028 |             raise ValueError('项目状态路径不能是符号链接: ' + str(path))
0029 |         if path.exists() and ((path.name == 'sessions' and not path.is_dir())
0030 |                               or (path.name != 'sessions' and not path.is_file())):
0031 |             raise ValueError('项目状态路径类型无效: ' + str(path))
0032 |     old = (permissions.PROJECT_ROOT, sandbox.PROJECT_ROOT, history.HISTORY_PATH, audit.LOG_PATH,
0033 |            dict(instruction_state), dict(active_skills))
0034 |     permissions.PROJECT_ROOT = sandbox.PROJECT_ROOT = root
0035 |     history.HISTORY_PATH = state / 'history.jsonl'
0036 |     audit.LOG_PATH = state / 'tool_events.jsonl'
0037 |     active_skills.clear()
0038 |     instruction_state.update(status='missing', content='', message='尚未加载项目规则')
0039 |     try:
0040 |         yield root
0041 |     finally:
0042 |         permissions.PROJECT_ROOT, sandbox.PROJECT_ROOT, history.HISTORY_PATH, audit.LOG_PATH = old[:4]
0043 |         instruction_state.clear()
0044 |         instruction_state.update(old[4])
0045 |         active_skills.clear()
0046 |         active_skills.update(old[5])
```
