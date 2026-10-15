# sessions.py：源码导读

命名会话路径、切换、重命名、导出；本进程保存Skill快照。

先读专题：[04-context.md](../04-context.md)。

实际源码：[sessions.py](../../../sessions.py)。

快照 SHA256：`f0ead897b326aaecc0520bda8cf76f8b241666b133475b41df55d0c9f86b5894`；112 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import os` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `import re` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `import history` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `from skills import active_skills` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [SessionManager.__init__](#sessionmanager---init--) | [12](../../../sessions.py#L12) | 构造对象的初始状态；调用类创建对象时自动执行。 |
| [SessionManager.path_for](#sessionmanager-path-for) | [18](../../../sessions.py#L18) | 由合法会话名构造固定路径，拒绝链接/非文件。 |
| [SessionManager.switch](#sessionmanager-switch) | [30](../../../sessions.py#L30) | 成功读新会话后再更新当前名称、历史路径和Skill快照。 |
| [SessionManager.list_sessions](#sessionmanager-list-sessions) | [49](../../../sessions.py#L49) | 发现合法JSONL名称并排序。 |
| [SessionManager.rename](#sessionmanager-rename) | [65](../../../sessions.py#L65) | 独占建新名再删旧名，不覆盖同名会话，失败撤销新链接。 |
| [SessionManager.export](#sessionmanager-export) | [98](../../../sessions.py#L98) | 将当前消息导出可读JSON，拒绝符号链接。 |

<a id="sessionmanager---init--"></a>
## SessionManager.__init__

构造对象的初始状态；self上的字段会在后续方法中继续使用。

```python
def __init__(self)
```

位置：[12行](../../../sessions.py#L12) 至快照 16 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 13 | `self.default_path` | `Path(history.HISTORY_PATH)` | 当前项目默认历史路径，命名会话以其父目录为基准。 |
| 14 | `self.directory` | `self.default_path.parent / 'sessions'` | 当前目录路径，遍历/候选/会话使用。 |
| 15 | `self.current_name` | `'default'` | 当前会话名称，成功切换后才提交。 |
| 16 | `self.skill_snapshots` | `{}` | 本进程按会话保存已启用Skill内容的快照。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 13 | 函数体 | 将 `Path(history.HISTORY_PATH)` 赋给 `self.default_path`。 |
| 14 | 函数体 | 将 `self.default_path.parent / 'sessions'` 赋给 `self.directory`。 |
| 15 | 函数体 | 将 `'default'` 赋给 `self.current_name`。 |
| 16 | 函数体 | 将 `{}` 赋给 `self.skill_snapshots`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="sessionmanager-path-for"></a>
## SessionManager.path_for

由合法会话名构造固定路径，拒绝链接/非文件。

```python
def path_for(self, name)
```

位置：[18行](../../../sessions.py#L18) 至快照 28 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ValueError`、`isinstance`、`path.exists`、`path.is_file`、`path.is_symlink`、`re.fullmatch`、`self.directory.is_symlink`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 23 | `path` | `self.default_path if name == 'default' else self.directory / (name + '.jsonl')` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 19 | 函数体 | 条件 `not isinstance(name, str) or not re.fullmatch('[A-Za-z0-9_-]{1,64}', name) or name == 'rename'`：真时执行body，假时进入else/后续。 |
| 20 | 函数体 / 条件为真 | 抛出 `ValueError('会话名为 1～64 位字母、数字、下划线或连字符，不能为 rename')`。 |
| 21 | 函数体 | 条件 `self.directory.is_symlink()`：真时执行body，假时进入else/后续。 |
| 22 | 函数体 / 条件为真 | 抛出 `ValueError('会话目录不能是符号链接')`。 |
| 23 | 函数体 | 将 `self.default_path if name == 'default' else self.directory / (name + '.jsonl')` 赋给 `path`。 |
| 24 | 函数体 | 条件 `path.is_symlink()`：真时执行body，假时进入else/后续。 |
| 25 | 函数体 / 条件为真 | 抛出 `ValueError('会话文件不能是符号链接')`。 |
| 26 | 函数体 | 条件 `path.exists() and (not path.is_file())`：真时执行body，假时进入else/后续。 |
| 27 | 函数体 / 条件为真 | 抛出 `ValueError('会话历史路径不是普通文件')`。 |
| 28 | 函数体 | 返回 `path`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L28：`path`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="sessionmanager-switch"></a>
## SessionManager.switch

成功读新会话后再更新当前名称、历史路径和Skill快照。

```python
def switch(self, name)
```

位置：[30行](../../../sessions.py#L30) 至快照 47 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |

**调用表达式（静态提取，不含内层独立函数体）**：`active_skills.clear`、`active_skills.update`、`dict`、`history.load_history`、`open`、`path.exists`、`path.parent.mkdir`、`self.path_for`、`self.skill_snapshots.get`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 32 | `path` | `self.path_for(name)` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| 34 | `messages` | `history.load_history(path)` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |
| 39 | `self.skill_snapshots[self.current_name]` | `dict(active_skills)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 43 | `history.HISTORY_PATH` | `path` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 44 | `self.current_name` | `name` | 当前会话名称，成功切换后才提交。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 31 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 32 | 函数体 / try | 将 `self.path_for(name)` 赋给 `path`。 |
| 34 | 函数体 / try | 将 `history.load_history(path)` 赋给 `messages`。 |
| 35 | 函数体 / try | 计算表达式/调用产生动作：`path.parent.mkdir(parents=True, exist_ok=True)`。 |
| 36 | 函数体 / try | 条件 `not path.exists()`：真时执行body，假时进入else/后续。 |
| 37 | 函数体 / try / 条件为真 | 进入资源/状态范围：`open(path, 'x', encoding='utf-8')`；退出执行清理。 |
| 38 | 函数体 / try / 条件为真 / with范围 | pass占位，无动作。 |
| 39 | 函数体 / try | 将 `dict(active_skills)` 赋给 `self.skill_snapshots[self.current_name]`。 |
| 40 | 函数体 / try | 条件 `name != self.current_name`：真时执行body，假时进入else/后续。 |
| 41 | 函数体 / try / 条件为真 | 计算表达式/调用产生动作：`active_skills.clear()`。 |
| 42 | 函数体 / try / 条件为真 | 计算表达式/调用产生动作：`active_skills.update(self.skill_snapshots.get(name, {}))`。 |
| 43 | 函数体 / try | 将 `path` 赋给 `history.HISTORY_PATH`。 |
| 44 | 函数体 / try | 将 `name` 赋给 `self.current_name`。 |
| 45 | 函数体 / try | 返回 `{'ok': True, 'messages': messages, 'name': name}`，结束当前函数；具体分支见完整源码。 |
| 46 | 函数体 | except (OSError, UnicodeError, ValueError) as error：只处理匹配类型的异常。 |
| 47 | 函数体 / except (OSError, UnicodeError, ValueError) as error | 返回 `{'ok': False, 'error': '会话切换失败: ' + str(error)}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L45：`{'ok': True, 'messages': messages, 'name': name}`。
- L47：`{'ok': False, 'error': '会话切换失败: ' + str(error)}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="sessionmanager-list-sessions"></a>
## SessionManager.list_sessions

发现合法JSONL名称并排序。

```python
def list_sessions(self)
```

位置：[49行](../../../sessions.py#L49) 至快照 63 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：`checked.is_file`、`names.add`、`self.directory.exists`、`self.directory.glob`、`self.path_for`、`sorted`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 52 | `names` | `{'default'}` | 合法会话/工具/附件名称集合，具体看返回结构。 |
| 56 | `checked` | `self.path_for(path.stem)` | 路径/准备检查的返回结果，用ok决定能否继续。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 50 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 51 | 函数体 / try | 计算表达式/调用产生动作：`self.path_for('default')`。 |
| 52 | 函数体 / try | 将 `{'default'}` 赋给 `names`。 |
| 53 | 函数体 / try | 条件 `self.directory.exists()`：真时执行body，假时进入else/后续。 |
| 54 | 函数体 / try / 条件为真 | 遍历 `self.directory.glob('*.jsonl')`，每次绑定 `path`。 |
| 55 | 函数体 / try / 条件为真 / 循环每次 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 56 | 函数体 / try / 条件为真 / 循环每次 / try | 将 `self.path_for(path.stem)` 赋给 `checked`。 |
| 57 | 函数体 / try / 条件为真 / 循环每次 / try | 条件 `checked.is_file()`：真时执行body，假时进入else/后续。 |
| 58 | 函数体 / try / 条件为真 / 循环每次 / try / 条件为真 | 计算表达式/调用产生动作：`names.add(path.stem)`。 |
| 59 | 函数体 / try / 条件为真 / 循环每次 | except ValueError：只处理匹配类型的异常。 |
| 60 | 函数体 / try / 条件为真 / 循环每次 / except ValueError | continue跳到最近循环下一次；不再向下处理本次输入。 |
| 61 | 函数体 / try | 返回 `{'ok': True, 'names': sorted(names)}`，结束当前函数；具体分支见完整源码。 |
| 62 | 函数体 | except (OSError, ValueError) as error：只处理匹配类型的异常。 |
| 63 | 函数体 / except (OSError, ValueError) as error | 返回 `{'ok': False, 'error': '无法列出会话: ' + str(error)}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L61：`{'ok': True, 'names': sorted(names)}`。
- L63：`{'ok': False, 'error': '无法列出会话: ' + str(error)}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="sessionmanager-rename"></a>
## SessionManager.rename

独占建新名再删旧名，不覆盖同名会话，失败撤销新链接。

```python
def rename(self, name)
```

位置：[65行](../../../sessions.py#L65) 至快照 96 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ValueError`、`destination.exists`、`destination.parent.mkdir`、`destination.unlink`、`dict`、`open`、`os.link`、`self.path_for`、`self.skill_snapshots.pop`、`source.exists`、`source.unlink`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 66 | `destination` | `None` | 新名称/导出/复制发布的目标路径。 |
| 67 | `linked` | `False` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 69 | `source` | `self.path_for(self.current_name)` | 可信调用方指定的来源，model或user；不能从模型参数中采纳。 |
| 70 | `destination` | `self.path_for(name)` | 新名称/导出/复制发布的目标路径。 |
| 79 | `linked` | `True` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 85 | `self.skill_snapshots[name]` | `dict(active_skills)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 86 | `self.current_name` | `name` | 当前会话名称，成功切换后才提交。 |
| 87 | `history.HISTORY_PATH` | `destination` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 66 | 函数体 | 将 `None` 赋给 `destination`。 |
| 67 | 函数体 | 将 `False` 赋给 `linked`。 |
| 68 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 69 | 函数体 / try | 将 `self.path_for(self.current_name)` 赋给 `source`。 |
| 70 | 函数体 / try | 将 `self.path_for(name)` 赋给 `destination`。 |
| 71 | 函数体 / try | 条件 `name == self.current_name`：真时执行body，假时进入else/后续。 |
| 72 | 函数体 / try / 条件为真 | 返回 `{'ok': True, 'name': name, 'message': '名称没有变化'}`，结束当前函数；具体分支见完整源码。 |
| 73 | 函数体 / try | 条件 `destination.exists() or name in self.skill_snapshots`：真时执行body，假时进入else/后续。 |
| 74 | 函数体 / try / 条件为真 | 抛出 `ValueError('目标会话已经存在，不能覆盖')`。 |
| 75 | 函数体 / try | 计算表达式/调用产生动作：`destination.parent.mkdir(parents=True, exist_ok=True)`。 |
| 76 | 函数体 / try | 条件 `source.exists()`：真时执行body，假时进入else/后续。 |
| 78 | 函数体 / try / 条件为真 | 计算表达式/调用产生动作：`os.link(source, destination)`。 |
| 79 | 函数体 / try / 条件为真 | 将 `True` 赋给 `linked`。 |
| 80 | 函数体 / try / 条件为真 | 计算表达式/调用产生动作：`source.unlink()`。 |
| 82 | 函数体 / try / 条件为假/elif | 进入资源/状态范围：`open(destination, 'x', encoding='utf-8')`；退出执行清理。 |
| 83 | 函数体 / try / 条件为假/elif / with范围 | pass占位，无动作。 |
| 84 | 函数体 / try | 计算表达式/调用产生动作：`self.skill_snapshots.pop(self.current_name, None)`。 |
| 85 | 函数体 / try | 将 `dict(active_skills)` 赋给 `self.skill_snapshots[name]`。 |
| 86 | 函数体 / try | 将 `name` 赋给 `self.current_name`。 |
| 87 | 函数体 / try | 将 `destination` 赋给 `history.HISTORY_PATH`。 |
| 88 | 函数体 / try | 返回 `{'ok': True, 'name': name, 'message': '会话已重命名为 ' + name}`，结束当前函数；具体分支见完整源码。 |
| 89 | 函数体 | except (OSError, ValueError) as error：只处理匹配类型的异常。 |
| 91 | 函数体 / except (OSError, ValueError) as error | 条件 `linked and destination is not None`：真时执行body，假时进入else/后续。 |
| 92 | 函数体 / except (OSError, ValueError) as error / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 93 | 函数体 / except (OSError, ValueError) as error / 条件为真 / try | 计算表达式/调用产生动作：`destination.unlink()`。 |
| 94 | 函数体 / except (OSError, ValueError) as error / 条件为真 | except OSError：只处理匹配类型的异常。 |
| 95 | 函数体 / except (OSError, ValueError) as error / 条件为真 / except OSError | pass占位，无动作。 |
| 96 | 函数体 / except (OSError, ValueError) as error | 返回 `{'ok': False, 'error': '会话重命名失败: ' + str(error)}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L72：`{'ok': True, 'name': name, 'message': '名称没有变化'}`。
- L88：`{'ok': True, 'name': name, 'message': '会话已重命名为 ' + name}`。
- L96：`{'ok': False, 'error': '会话重命名失败: ' + str(error)}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="sessionmanager-export"></a>
## SessionManager.export

将当前消息导出可读JSON，拒绝符号链接。

```python
def export(self, messages)
```

位置：[98行](../../../sessions.py#L98) 至快照 112 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `messages` | `未显式注解` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ValueError`、`json.dump`、`open`、`path.is_symlink`、`path.parent.mkdir`、`self.default_path.with_suffix`、`self.path_for`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 101 | `path` | `self.default_path.with_suffix('.json') if self.current_name == 'default' else self.directory / (self.current_name + '.export.json'…（见完整源码）` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 99 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 100 | 函数体 / try | 计算表达式/调用产生动作：`self.path_for(self.current_name)`。 |
| 101 | 函数体 / try | 将 `self.default_path.with_suffix('.json') if self.current_name == 'default' else self.directory / (self.current_name + '.export.json')` 赋给 `path`。 |
| 105 | 函数体 / try | 条件 `path.is_symlink()`：真时执行body，假时进入else/后续。 |
| 106 | 函数体 / try / 条件为真 | 抛出 `ValueError('导出路径不能是符号链接')`。 |
| 107 | 函数体 / try | 计算表达式/调用产生动作：`path.parent.mkdir(parents=True, exist_ok=True)`。 |
| 108 | 函数体 / try | 进入资源/状态范围：`open(path, 'w', encoding='utf-8')` 绑定 `file`；退出执行清理。 |
| 109 | 函数体 / try / with范围 | 计算表达式/调用产生动作：`json.dump(messages, file, ensure_ascii=False, indent=2)`。 |
| 110 | 函数体 / try | 返回 `{'ok': True, 'path': str(path)}`，结束当前函数；具体分支见完整源码。 |
| 111 | 函数体 | except (OSError, ValueError) as error：只处理匹配类型的异常。 |
| 112 | 函数体 / except (OSError, ValueError) as error | 返回 `{'ok': False, 'error': '会话导出失败: ' + str(error)}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L110：`{'ok': True, 'path': str(path)}`。
- L112：`{'ok': False, 'error': '会话导出失败: ' + str(error)}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- class：对象状态与方法/继承：L11。
- try/except/finally：异常与保证清理：L31, L50, L55, L68, L92, L99。
- with/yield：资源/状态生命周期或逐个生成：L37, L82, L108。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """会话管理；文件路径由名称生成，独立于模型文件工具的访问入口。"""
0002 | import json
0003 | import os
0004 | import re
0005 | from pathlib import Path
0006 | 
0007 | import history
0008 | from skills import active_skills
0009 | 
0010 | 
0011 | class SessionManager:
0012 |     def __init__(self):
0013 |         self.default_path = Path(history.HISTORY_PATH)
0014 |         self.directory = self.default_path.parent / "sessions"
0015 |         self.current_name = "default"
0016 |         self.skill_snapshots = {}
0017 | 
0018 |     def path_for(self, name):
0019 |         if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", name) or name == "rename":
0020 |             raise ValueError("会话名为 1～64 位字母、数字、下划线或连字符，不能为 rename")
0021 |         if self.directory.is_symlink():
0022 |             raise ValueError("会话目录不能是符号链接")
0023 |         path = self.default_path if name == "default" else self.directory / (name + ".jsonl")
0024 |         if path.is_symlink():
0025 |             raise ValueError("会话文件不能是符号链接")
0026 |         if path.exists() and not path.is_file():
0027 |             raise ValueError("会话历史路径不是普通文件")
0028 |         return path
0029 | 
0030 |     def switch(self, name):
0031 |         try:
0032 |             path = self.path_for(name)
0033 |             # 先成功读取目标，再提交路径、名称和 Skill 状态，避免失败后串会话。
0034 |             messages = history.load_history(path)
0035 |             path.parent.mkdir(parents=True, exist_ok=True)
0036 |             if not path.exists():
0037 |                 with open(path, "x", encoding="utf-8"):
0038 |                     pass
0039 |             self.skill_snapshots[self.current_name] = dict(active_skills)
0040 |             if name != self.current_name:
0041 |                 active_skills.clear()
0042 |                 active_skills.update(self.skill_snapshots.get(name, {}))
0043 |             history.HISTORY_PATH = path
0044 |             self.current_name = name
0045 |             return {"ok": True, "messages": messages, "name": name}
0046 |         except (OSError, UnicodeError, ValueError) as error:
0047 |             return {"ok": False, "error": "会话切换失败: " + str(error)}
0048 | 
0049 |     def list_sessions(self):
0050 |         try:
0051 |             self.path_for("default")
0052 |             names = {"default"}
0053 |             if self.directory.exists():
0054 |                 for path in self.directory.glob("*.jsonl"):
0055 |                     try:
0056 |                         checked = self.path_for(path.stem)
0057 |                         if checked.is_file():
0058 |                             names.add(path.stem)
0059 |                     except ValueError:
0060 |                         continue
0061 |             return {"ok": True, "names": sorted(names)}
0062 |         except (OSError, ValueError) as error:
0063 |             return {"ok": False, "error": "无法列出会话: " + str(error)}
0064 | 
0065 |     def rename(self, name):
0066 |         destination = None
0067 |         linked = False
0068 |         try:
0069 |             source = self.path_for(self.current_name)
0070 |             destination = self.path_for(name)
0071 |             if name == self.current_name:
0072 |                 return {"ok": True, "name": name, "message": "名称没有变化"}
0073 |             if destination.exists() or name in self.skill_snapshots:
0074 |                 raise ValueError("目标会话已经存在，不能覆盖")
0075 |             destination.parent.mkdir(parents=True, exist_ok=True)
0076 |             if source.exists():
0077 |                 # 独占创建目标，避免 rename 在并发创建时覆盖另一份会话。
0078 |                 os.link(source, destination)
0079 |                 linked = True
0080 |                 source.unlink()
0081 |             else:
0082 |                 with open(destination, "x", encoding="utf-8"):
0083 |                     pass
0084 |             self.skill_snapshots.pop(self.current_name, None)
0085 |             self.skill_snapshots[name] = dict(active_skills)
0086 |             self.current_name = name
0087 |             history.HISTORY_PATH = destination
0088 |             return {"ok": True, "name": name, "message": "会话已重命名为 " + name}
0089 |         except (OSError, ValueError) as error:
0090 |             # 原文件删除失败时撤销刚建立的链接，原会话仍然有效。
0091 |             if linked and destination is not None:
0092 |                 try:
0093 |                     destination.unlink()
0094 |                 except OSError:
0095 |                     pass
0096 |             return {"ok": False, "error": "会话重命名失败: " + str(error)}
0097 | 
0098 |     def export(self, messages):
0099 |         try:
0100 |             self.path_for(self.current_name)
0101 |             path = (
0102 |                 self.default_path.with_suffix(".json") if self.current_name == "default"
0103 |                 else self.directory / (self.current_name + ".export.json")
0104 |             )
0105 |             if path.is_symlink():
0106 |                 raise ValueError("导出路径不能是符号链接")
0107 |             path.parent.mkdir(parents=True, exist_ok=True)
0108 |             with open(path, "w", encoding="utf-8") as file:
0109 |                 json.dump(messages, file, ensure_ascii=False, indent=2)
0110 |             return {"ok": True, "path": str(path)}
0111 |         except (OSError, ValueError) as error:
0112 |             return {"ok": False, "error": "会话导出失败: " + str(error)}
```
