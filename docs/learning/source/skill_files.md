# skill_files.py：源码导读

固定Skill路径的新建专用工具；diff审批、独占创建，不自动启用。

先读专题：[05-extensions.md](../05-extensions.md)。

实际源码：[skill_files.py](../../../skill_files.py)。

快照 SHA256：`959c3184ad738fcd97fd8eb06be848eec11dd96072f7a4d50491c0e0ca62989e`；72 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import os` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import tempfile` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `import permissions` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `from patches import build_diff` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `from skills import MAX_SKILL_BYTES, check_skill_path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [check_new_skill_target](#check-new-skill-target) | [11](../../../skill_files.py#L11) | 仅允许固定Skill三级路径且新目标不为链接/已存在。 |
| [prepare_create_skill](#prepare-create-skill) | [30](../../../skill_files.py#L30) | 校验非空内容/大小并生成新建diff。 |
| [apply_prepared_skill](#apply-prepared-skill) | [46](../../../skill_files.py#L46) | 独占新建SKILL.md，临时文件清理，不自动启用。 |

<a id="check-new-skill-target"></a>
## check_new_skill_target

仅允许固定Skill三级路径且新目标不为链接/已存在。

```python
def check_new_skill_target(path)
```

位置：[11行](../../../skill_files.py#L11) 至快照 27 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`check_skill_path`、`item.is_symlink`、`len`、`permissions.resolve_project_path`、`str`、`target.exists`、`target.relative_to`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 12 | `checked` | `permissions.resolve_project_path(path)` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 15 | `target` | `Path(checked['path'])` | 已选定的文件/目录或操作目标，提交前可能需要再次验证。 |
| 16 | `relative` | `target.relative_to(permissions.PROJECT_ROOT)` | 相对项目路径，供显示或范围检查。 |
| 19 | `skill` | `check_skill_path(relative.parts[1])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 12 | 函数体 | 将 `permissions.resolve_project_path(path)` 赋给 `checked`。 |
| 13 | 函数体 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 14 | 函数体 / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 15 | 函数体 | 将 `Path(checked['path'])` 赋给 `target`。 |
| 16 | 函数体 | 将 `target.relative_to(permissions.PROJECT_ROOT)` 赋给 `relative`。 |
| 17 | 函数体 | 条件 `len(relative.parts) != 3 or relative.parts[0] != 'skills' or relative.parts[2] != 'SKILL.md'`：真时执行body，假时进入else/后续。 |
| 18 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '只能创建 skills/<名称>/SKILL.md'}`，结束当前函数；具体分支见完整源码。 |
| 19 | 函数体 | 将 `check_skill_path(relative.parts[1])` 赋给 `skill`。 |
| 20 | 函数体 | 条件 `not skill['ok']`：真时执行body，假时进入else/后续。 |
| 21 | 函数体 / 条件为真 | 返回 `skill`，结束当前函数；具体分支见完整源码。 |
| 22 | 函数体 | 遍历 `[permissions.PROJECT_ROOT / 'skills', target.parent, target]`，每次绑定 `item`。 |
| 23 | 函数体 / 循环每次 | 条件 `item.is_symlink()`：真时执行body，假时进入else/后续。 |
| 24 | 函数体 / 循环每次 / 条件为真 | 返回 `{'ok': False, 'error': '生成 Skill 的目标不能是符号链接'}`，结束当前函数；具体分支见完整源码。 |
| 25 | 函数体 | 条件 `target.exists()`：真时执行body，假时进入else/后续。 |
| 26 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': 'Skill 文件已存在，生成操作不会覆盖它'}`，结束当前函数；具体分支见完整源码。 |
| 27 | 函数体 | 返回 `{'ok': True, 'path': str(target)}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L14：`checked`。
- L18：`{'ok': False, 'error': '只能创建 skills/<名称>/SKILL.md'}`。
- L21：`skill`。
- L24：`{'ok': False, 'error': '生成 Skill 的目标不能是符号链接'}`。
- L26：`{'ok': False, 'error': 'Skill 文件已存在，生成操作不会覆盖它'}`。
- L27：`{'ok': True, 'path': str(target)}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="prepare-create-skill"></a>
## prepare_create_skill

校验非空内容/大小并生成新建diff。

```python
def prepare_create_skill(path, new_content)
```

位置：[30行](../../../skill_files.py#L30) 至快照 43 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| `new_content` | `未显式注解` | 拟写入的完整文字内容，不是模型提供的patch格式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`build_diff`、`check_new_skill_target`、`isinstance`、`len`、`new_content.encode`、`new_content.strip`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 31 | `checked` | `check_new_skill_target(path)` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 36 | `raw` | `new_content.encode('utf-8')` | 未解码字节/完整输出快照，按编码与限额再处理。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 31 | 函数体 | 将 `check_new_skill_target(path)` 赋给 `checked`。 |
| 32 | 函数体 | 条件 `not checked['ok']`：真时执行body，假时进入else/后续。 |
| 33 | 函数体 / 条件为真 | 返回 `checked`，结束当前函数；具体分支见完整源码。 |
| 34 | 函数体 | 条件 `not isinstance(new_content, str) or not new_content.strip() or '\x00' in new_content`：真时执行body，假时进入else/后续。 |
| 35 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': 'Skill 内容必须是非空文字，不能包含空字符'}`，结束当前函数；具体分支见完整源码。 |
| 36 | 函数体 | 将 `new_content.encode('utf-8')` 赋给 `raw`。 |
| 37 | 函数体 | 条件 `len(raw) > MAX_SKILL_BYTES`：真时执行body，假时进入else/后续。 |
| 38 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': 'Skill 内容超过 32 KiB 上限'}`，结束当前函数；具体分支见完整源码。 |
| 39 | 函数体 | 返回 `{'ok': True, 'path': checked['path'], 'new_bytes': raw, 'diff': build_diff(checked['path'], '', new_content), 'details': '新建 Skill 文件，不覆盖已有文件，也不自动启用'}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L33：`checked`。
- L35：`{'ok': False, 'error': 'Skill 内容必须是非空文字，不能包含空字符'}`。
- L38：`{'ok': False, 'error': 'Skill 内容超过 32 KiB 上限'}`。
- L39：`{'ok': True, 'path': checked['path'], 'new_bytes': raw, 'diff': build_diff(checked['path'], '', new_content), 'details': '新建 Skill 文件，不覆盖已有文件，也不自动启用'}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="apply-prepared-skill"></a>
## apply_prepared_skill

独占新建SKILL.md，临时文件清理，不自动启用。

```python
def apply_prepared_skill(prepared)
```

位置：[46行](../../../skill_files.py#L46) 至快照 72 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `prepared` | `未显式注解` | prepare形成的待审快照：diff/字节或沙箱命令参数。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`check_new_skill_target`、`file.fileno`、`file.flush`、`file.write`、`os.fsync`、`os.link`、`print`、`str`、`target.parent.mkdir`、`tempfile.NamedTemporaryFile`、`temporary_path.unlink`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 47 | `temporary_path` | `None` | 尚未发布的同目录临时文件路径，finally清理。 |
| 49 | `checked` | `check_new_skill_target(prepared['path'])` | 路径/准备检查的返回结果，用ok决定能否继续。 |
| 52 | `target` | `Path(checked['path'])` | 已选定的文件/目录或操作目标，提交前可能需要再次验证。 |
| 55 | `temporary_path` | `Path(file.name)` | 尚未发布的同目录临时文件路径，finally清理。 |
| 59 | `checked` | `check_new_skill_target(prepared['path'])` | 路径/准备检查的返回结果，用ok决定能否继续。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 47 | 函数体 | 将 `None` 赋给 `temporary_path`。 |
| 48 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 49 | 函数体 / try | 将 `check_new_skill_target(prepared['path'])` 赋给 `checked`。 |
| 50 | 函数体 / try | 条件 `not checked['ok'] or checked['path'] != prepared['path']`：真时执行body，假时进入else/后续。 |
| 51 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': '目标已变化或已存在，创建已取消'}`，结束当前函数；具体分支见完整源码。 |
| 52 | 函数体 / try | 将 `Path(checked['path'])` 赋给 `target`。 |
| 53 | 函数体 / try | 计算表达式/调用产生动作：`target.parent.mkdir(parents=True, exist_ok=True)`。 |
| 54 | 函数体 / try | 进入资源/状态范围：`tempfile.NamedTemporaryFile(dir=target.parent, prefix='.skill-draft-', delete=False)` 绑定 `file`；退出执行清理。 |
| 55 | 函数体 / try / with范围 | 将 `Path(file.name)` 赋给 `temporary_path`。 |
| 56 | 函数体 / try / with范围 | 计算表达式/调用产生动作：`file.write(prepared['new_bytes'])`。 |
| 57 | 函数体 / try / with范围 | 计算表达式/调用产生动作：`file.flush()`。 |
| 58 | 函数体 / try / with范围 | 计算表达式/调用产生动作：`os.fsync(file.fileno())`。 |
| 59 | 函数体 / try | 将 `check_new_skill_target(prepared['path'])` 赋给 `checked`。 |
| 60 | 函数体 / try | 条件 `not checked['ok'] or checked['path'] != str(target)`：真时执行body，假时进入else/后续。 |
| 61 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': '目标在写入前已变化，创建已取消'}`，结束当前函数；具体分支见完整源码。 |
| 63 | 函数体 / try | 计算表达式/调用产生动作：`os.link(temporary_path, target)`。 |
| 64 | 函数体 / try | 返回 `{'ok': True, 'path': str(target), 'message': 'Skill 已保存，尚未启用'}`，结束当前函数；具体分支见完整源码。 |
| 65 | 函数体 | except OSError as error：只处理匹配类型的异常。 |
| 66 | 函数体 / except OSError as error | 返回 `{'ok': False, 'error': 'Skill 保存失败: ' + str(error)}`，结束当前函数；具体分支见完整源码。 |
| 68 | 函数体 / finally保证清理 | 条件 `temporary_path is not None`：真时执行body，假时进入else/后续。 |
| 69 | 函数体 / finally保证清理 / 条件为真 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 70 | 函数体 / finally保证清理 / 条件为真 / try | 计算表达式/调用产生动作：`temporary_path.unlink()`。 |
| 71 | 函数体 / finally保证清理 / 条件为真 | except OSError as error：只处理匹配类型的异常。 |
| 72 | 函数体 / finally保证清理 / 条件为真 / except OSError as error | 计算表达式/调用产生动作：`print('Skill 临时文件清理失败:', error)`。 |

**实际返回分支**：

- L51：`{'ok': False, 'error': '目标已变化或已存在，创建已取消'}`。
- L61：`{'ok': False, 'error': '目标在写入前已变化，创建已取消'}`。
- L64：`{'ok': True, 'path': str(target), 'message': 'Skill 已保存，尚未启用'}`。
- L66：`{'ok': False, 'error': 'Skill 保存失败: ' + str(error)}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L48, L69。
- with/yield：资源/状态生命周期或逐个生成：L54。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """新建 Skill 文件：审查后独占创建，不覆盖已有文件。"""
0002 | import os
0003 | import tempfile
0004 | from pathlib import Path
0005 | 
0006 | import permissions
0007 | from patches import build_diff
0008 | from skills import MAX_SKILL_BYTES, check_skill_path
0009 | 
0010 | 
0011 | def check_new_skill_target(path):
0012 |     checked = permissions.resolve_project_path(path)
0013 |     if not checked["ok"]:
0014 |         return checked
0015 |     target = Path(checked["path"])
0016 |     relative = target.relative_to(permissions.PROJECT_ROOT)
0017 |     if len(relative.parts) != 3 or relative.parts[0] != "skills" or relative.parts[2] != "SKILL.md":
0018 |         return {"ok": False, "error": "只能创建 skills/<名称>/SKILL.md"}
0019 |     skill = check_skill_path(relative.parts[1])
0020 |     if not skill["ok"]:
0021 |         return skill
0022 |     for item in [permissions.PROJECT_ROOT / "skills", target.parent, target]:
0023 |         if item.is_symlink():
0024 |             return {"ok": False, "error": "生成 Skill 的目标不能是符号链接"}
0025 |     if target.exists():
0026 |         return {"ok": False, "error": "Skill 文件已存在，生成操作不会覆盖它"}
0027 |     return {"ok": True, "path": str(target)}
0028 | 
0029 | 
0030 | def prepare_create_skill(path, new_content):
0031 |     checked = check_new_skill_target(path)
0032 |     if not checked["ok"]:
0033 |         return checked
0034 |     if not isinstance(new_content, str) or not new_content.strip() or "\x00" in new_content:
0035 |         return {"ok": False, "error": "Skill 内容必须是非空文字，不能包含空字符"}
0036 |     raw = new_content.encode("utf-8")
0037 |     if len(raw) > MAX_SKILL_BYTES:
0038 |         return {"ok": False, "error": "Skill 内容超过 32 KiB 上限"}
0039 |     return {
0040 |         "ok": True, "path": checked["path"], "new_bytes": raw,
0041 |         "diff": build_diff(checked["path"], "", new_content),
0042 |         "details": "新建 Skill 文件，不覆盖已有文件，也不自动启用"
0043 |     }
0044 | 
0045 | 
0046 | def apply_prepared_skill(prepared):
0047 |     temporary_path = None
0048 |     try:
0049 |         checked = check_new_skill_target(prepared["path"])
0050 |         if not checked["ok"] or checked["path"] != prepared["path"]:
0051 |             return {"ok": False, "error": "目标已变化或已存在，创建已取消"}
0052 |         target = Path(checked["path"])
0053 |         target.parent.mkdir(parents=True, exist_ok=True)
0054 |         with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".skill-draft-", delete=False) as file:
0055 |             temporary_path = Path(file.name)
0056 |             file.write(prepared["new_bytes"])
0057 |             file.flush()
0058 |             os.fsync(file.fileno())
0059 |         checked = check_new_skill_target(prepared["path"])
0060 |         if not checked["ok"] or checked["path"] != str(target):
0061 |             return {"ok": False, "error": "目标在写入前已变化，创建已取消"}
0062 |         # link 只创建不存在的目标；并发创建时失败，而不是覆盖别人的文件。
0063 |         os.link(temporary_path, target)
0064 |         return {"ok": True, "path": str(target), "message": "Skill 已保存，尚未启用"}
0065 |     except OSError as error:
0066 |         return {"ok": False, "error": "Skill 保存失败: " + str(error)}
0067 |     finally:
0068 |         if temporary_path is not None:
0069 |             try:
0070 |                 temporary_path.unlink()
0071 |             except OSError as error:
0072 |                 print("Skill 临时文件清理失败:", error)
```
