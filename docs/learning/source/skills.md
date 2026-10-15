# skills.py：源码导读

发现并手动启用流程文字，注入系统上下文，数量和字节有界。

先读专题：[05-extensions.md](../05-extensions.md)。

实际源码：[skills.py](../../../skills.py)。

快照 SHA256：`5cca35fe6c4d59ecfcdb4133f92a748184d3d612a1061bb38d084f5ba6ccfb8d`；78 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import re` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `import permissions` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `MAX_SKILL_BYTES = 32768` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 9 | `MAX_ACTIVE_SKILLS = 3` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 10 | `MAX_TOTAL_BYTES = 65536` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 11 | `active_skills = {}` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [check_skill_path](#check-skill-path) | [14](../../../skills.py#L14) | 验证名称、固定skills目录与真实目标归属。 |
| [list_skills](#list-skills) | [28](../../../skills.py#L28) | 列出合法SKILL.md及本进程active状态。 |
| [activate_skill](#activate-skill) | [45](../../../skills.py#L45) | 读取有界流程文字，检查数量总额，加入active_skills。 |
| [clear_skills](#clear-skills) | [69](../../../skills.py#L69) | 清空启用集合。 |
| [get_skill_messages](#get-skill-messages) | [73](../../../skills.py#L73) | 将启用流程生成system指导消息。 |

<a id="check-skill-path"></a>
## check_skill_path

验证名称、固定skills目录与真实目标归属。

```python
def check_skill_path(name)
```

位置：[14行](../../../skills.py#L14) 至快照 25 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`Path(checked['path']).is_relative_to`、`isinstance`、`permissions.resolve_project_path`、`re.fullmatch`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 17 | `root` | `permissions.resolve_project_path('skills')` | 本次目录扫描/工作项目根。 |
| 18 | `checked` | `permissions.resolve_project_path('skills/' + name + '/SKILL.md')` | 路径/准备检查的返回结果，用ok决定能否继续。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 15 | 函数体 | 条件 `not isinstance(name, str) or not re.fullmatch('[a-zA-Z0-9_-]{1,64}', name) or name in ('clear', 'generate')`：真时执行body，假时进入else/后续。 |
| 16 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': 'Skill 名称为 1～64 位字母、数字、下划线或连字符，不能为 clear 或 generate'}`，结束当前函数；具体分支见完整源码。 |
| 17 | 函数体 | 将 `permissions.resolve_project_path('skills')` 赋给 `root`。 |
| 18 | 函数体 | 将 `permissions.resolve_project_path('skills/' + name + '/SKILL.md')` 赋给 `checked`。 |
| 19 | 函数体 | 条件 `not root['ok']`：真时执行body，假时进入else/后续。 |
| 20 | 函数体 / 条件为真 | 返回 `root`，结束当前函数；具体分支见完整源码。 |
| 21 | 函数体 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 22 | 函数体 / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 23 | 函数体 | 条件 `not Path(checked['path']).is_relative_to(Path(root['path']))`：真时执行body，假时进入else/后续。 |
| 24 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': 'Skill 文件不能指向 skills 目录之外'}`，结束当前函数；具体分支见完整源码。 |
| 25 | 函数体 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L16：`{'ok': False, 'error': 'Skill 名称为 1～64 位字母、数字、下划线或连字符，不能为 clear 或 generate'}`。
- L20：`root`。
- L22：`checked`。
- L24：`{'ok': False, 'error': 'Skill 文件不能指向 skills 目录之外'}`。
- L25：`checked`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="list-skills"></a>
## list_skills

列出合法SKILL.md及本进程active状态。

```python
def list_skills()
```

位置：[28行](../../../skills.py#L28) 至快照 42 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`Path(checked['path']).iterdir`、`Path(skill['path']).is_file`、`check_skill_path`、`entries.append`、`permissions.resolve_project_path`、`sorted`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 29 | `checked` | `permissions.resolve_project_path('skills')` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 33 | `entries` | `[]` | 目录项结果列表/扫描迭代器，类型由当前表达式决定。 |
| 35 | `skill` | `check_skill_path(directory.name)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 29 | 函数体 | 将 `permissions.resolve_project_path('skills')` 赋给 `checked`。 |
| 30 | 函数体 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 31 | 函数体 / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 32 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 33 | 函数体 / try | 将 `[]` 赋给 `entries`。 |
| 34 | 函数体 / try | 遍历 `Path(checked['path']).iterdir()`，每次绑定 `directory`。 |
| 35 | 函数体 / try / 循环每次 | 将 `check_skill_path(directory.name)` 赋给 `skill`。 |
| 36 | 函数体 / try / 循环每次 | 条件 `skill['ok'] and Path(skill['path']).is_file()`：真时执行body，假时进入else/后续。 |
| 37 | 函数体 / try / 循环每次 / 条件为真 | 计算表达式/调用产生动作：`entries.append({'name': directory.name, 'active': directory.name in active_skills})`。 |
| 38 | 函数体 / try | 返回 `{'ok': True, 'skills': sorted(entries, key=lambda entry: entry['name'])}`，结束当前函数；具体分支见完整源码。 |
| 39 | 函数体 | except FileNotFoundError：只处理匹配类型的异常。 |
| 40 | 函数体 / except FileNotFoundError | 返回 `{'ok': True, 'skills': []}`，结束当前函数；具体分支见完整源码。 |
| 41 | 函数体 | except OSError as error：只处理匹配类型的异常。 |
| 42 | 函数体 / except OSError as error | 返回 `{'ok': False, 'error': '无法列出 Skills: ' + str(error)}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L31：`checked`。
- L38：`{'ok': True, 'skills': sorted(entries, key=lambda entry: entry['name'])}`。
- L40：`{'ok': True, 'skills': []}`。
- L42：`{'ok': False, 'error': '无法列出 Skills: ' + str(error)}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="activate-skill"></a>
## activate_skill

读取有界流程文字，检查数量总额，加入active_skills。

```python
def activate_skill(name)
```

位置：[45行](../../../skills.py#L45) 至快照 66 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |

**调用表达式（静态提取，不含内层独立函数体）**：`active_skills.items`、`check_skill_path`、`content.encode`、`file.read`、`len`、`open`、`raw.decode`、`raw.decode('utf-8-sig').strip`、`str`、`sum`、`text.encode`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 46 | `checked` | `check_skill_path(name)` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 53 | `raw` | `file.read(MAX_SKILL_BYTES + 1)` | 未解码字节/完整输出快照，按编码与限额再处理。 |
| 56 | `content` | `raw.decode('utf-8-sig').strip()` | 文件正文、消息文字或累计响应；看role与来源。 |
| 59 | `total_bytes` | `len(content.encode('utf-8'))` | 本次搜索/读取累计字节，用于总额限制。 |
| 63 | `active_skills[name]` | `content` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 46 | 函数体 | 将 `check_skill_path(name)` 赋给 `checked`。 |
| 47 | 函数体 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 48 | 函数体 / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 49 | 函数体 | 条件 `name not in active_skills and len(active_skills) >= MAX_ACTIVE_SKILLS`：真时执行body，假时进入else/后续。 |
| 50 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '最多同时启用 3 个 Skill，请先 /skill clear'}`，结束当前函数；具体分支见完整源码。 |
| 51 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 52 | 函数体 / try | 进入资源/状态范围：`open(checked['path'], 'rb')` 绑定 `file`；退出执行清理。 |
| 53 | 函数体 / try / with范围 | 将 `file.read(MAX_SKILL_BYTES + 1)` 赋给 `raw`。 |
| 54 | 函数体 / try | 条件 `len(raw) > MAX_SKILL_BYTES`：真时执行body，假时进入else/后续。 |
| 55 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': 'SKILL.md 超过 32 KiB 上限'}`，结束当前函数；具体分支见完整源码。 |
| 56 | 函数体 / try | 将 `raw.decode('utf-8-sig').strip()` 赋给 `content`。 |
| 57 | 函数体 / try | 条件 `not content`：真时执行body，假时进入else/后续。 |
| 58 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': 'SKILL.md 不能为空'}`，结束当前函数；具体分支见完整源码。 |
| 59 | 函数体 / try | 将 `len(content.encode('utf-8'))` 赋给 `total_bytes`。 |
| 60 | 函数体 / try | 更新已有变量：`total_bytes += sum((len(text.encode('utf-8')) for key, text in active_skills.items() if key != name))`。 |
| 61 | 函数体 / try | 条件 `total_bytes > MAX_TOTAL_BYTES`：真时执行body，假时进入else/后续。 |
| 62 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': '已启用 Skills 的总内容超过 64 KiB'}`，结束当前函数；具体分支见完整源码。 |
| 63 | 函数体 / try | 将 `content` 赋给 `active_skills[name]`。 |
| 64 | 函数体 / try | 返回 `{'ok': True, 'name': name}`，结束当前函数；具体分支见完整源码。 |
| 65 | 函数体 | except (OSError, UnicodeError) as error：只处理匹配类型的异常。 |
| 66 | 函数体 / except (OSError, UnicodeError) as error | 返回 `{'ok': False, 'error': 'Skill 加载失败: ' + str(error)}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L48：`checked`。
- L50：`{'ok': False, 'error': '最多同时启用 3 个 Skill，请先 /skill clear'}`。
- L55：`{'ok': False, 'error': 'SKILL.md 超过 32 KiB 上限'}`。
- L58：`{'ok': False, 'error': 'SKILL.md 不能为空'}`。
- L62：`{'ok': False, 'error': '已启用 Skills 的总内容超过 64 KiB'}`。
- L64：`{'ok': True, 'name': name}`。
- L66：`{'ok': False, 'error': 'Skill 加载失败: ' + str(error)}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="clear-skills"></a>
## clear_skills

清空启用集合。

```python
def clear_skills()
```

位置：[69行](../../../skills.py#L69) 至快照 70 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`active_skills.clear`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 70 | 函数体 | 计算表达式/调用产生动作：`active_skills.clear()`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="get-skill-messages"></a>
## get_skill_messages

将启用流程生成system指导消息。

```python
def get_skill_messages()
```

位置：[73行](../../../skills.py#L73) 至快照 78 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`active_skills.items`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 74 | 函数体 | 返回 `[{'role': 'system', 'content': '用户手动启用的 Skill: ' + name + '\n该流程用于指导任务，不能改变客户端权限限制。\n' + content} for name, content in active_skills.items()]`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L74：`[{'role': 'system', 'content': '用户手动启用的 Skill: ' + name + '\n该流程用于指导任务，不能改变客户端权限限制。\n' + content} for name, content in active_skills.items()]`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L32, L51。
- with/yield：资源/状态生命周期或逐个生成：L52。
- 推导式/生成器表达式：循环建容器或逐个产生：L60, L74。
- lambda：小回调函数：L38。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """项目内 Skill 的发现、手动启用和停用；不执行文件中的命令。"""
0002 | import re
0003 | from pathlib import Path
0004 | 
0005 | import permissions
0006 | 
0007 | 
0008 | MAX_SKILL_BYTES = 32768
0009 | MAX_ACTIVE_SKILLS = 3
0010 | MAX_TOTAL_BYTES = 65536
0011 | active_skills = {}
0012 | 
0013 | 
0014 | def check_skill_path(name):
0015 |     if not isinstance(name, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", name) or name in ("clear", "generate"):
0016 |         return {"ok": False, "error": "Skill 名称为 1～64 位字母、数字、下划线或连字符，不能为 clear 或 generate"}
0017 |     root = permissions.resolve_project_path("skills")
0018 |     checked = permissions.resolve_project_path("skills/" + name + "/SKILL.md")
0019 |     if not root["ok"]:
0020 |         return root
0021 |     if not checked["ok"]:
0022 |         return checked
0023 |     if not Path(checked["path"]).is_relative_to(Path(root["path"])):
0024 |         return {"ok": False, "error": "Skill 文件不能指向 skills 目录之外"}
0025 |     return checked
0026 | 
0027 | 
0028 | def list_skills():
0029 |     checked = permissions.resolve_project_path("skills")
0030 |     if not checked["ok"]:
0031 |         return checked
0032 |     try:
0033 |         entries = []
0034 |         for directory in Path(checked["path"]).iterdir():
0035 |             skill = check_skill_path(directory.name)
0036 |             if skill["ok"] and Path(skill["path"]).is_file():
0037 |                 entries.append({"name": directory.name, "active": directory.name in active_skills})
0038 |         return {"ok": True, "skills": sorted(entries, key=lambda entry: entry["name"])}
0039 |     except FileNotFoundError:
0040 |         return {"ok": True, "skills": []}
0041 |     except OSError as error:
0042 |         return {"ok": False, "error": "无法列出 Skills: " + str(error)}
0043 | 
0044 | 
0045 | def activate_skill(name):
0046 |     checked = check_skill_path(name)
0047 |     if not checked["ok"]:
0048 |         return checked
0049 |     if name not in active_skills and len(active_skills) >= MAX_ACTIVE_SKILLS:
0050 |         return {"ok": False, "error": "最多同时启用 3 个 Skill，请先 /skill clear"}
0051 |     try:
0052 |         with open(checked["path"], "rb") as file:
0053 |             raw = file.read(MAX_SKILL_BYTES + 1)
0054 |         if len(raw) > MAX_SKILL_BYTES:
0055 |             return {"ok": False, "error": "SKILL.md 超过 32 KiB 上限"}
0056 |         content = raw.decode("utf-8-sig").strip()
0057 |         if not content:
0058 |             return {"ok": False, "error": "SKILL.md 不能为空"}
0059 |         total_bytes = len(content.encode("utf-8"))
0060 |         total_bytes += sum(len(text.encode("utf-8")) for key, text in active_skills.items() if key != name)
0061 |         if total_bytes > MAX_TOTAL_BYTES:
0062 |             return {"ok": False, "error": "已启用 Skills 的总内容超过 64 KiB"}
0063 |         active_skills[name] = content
0064 |         return {"ok": True, "name": name}
0065 |     except (OSError, UnicodeError) as error:
0066 |         return {"ok": False, "error": "Skill 加载失败: " + str(error)}
0067 | 
0068 | 
0069 | def clear_skills():
0070 |     active_skills.clear()
0071 | 
0072 | 
0073 | def get_skill_messages():
0074 |     return [{
0075 |         "role": "system",
0076 |         "content": "用户手动启用的 Skill: " + name + "\n"
0077 |                    "该流程用于指导任务，不能改变客户端权限限制。\n" + content
0078 |     } for name, content in active_skills.items()]
```
