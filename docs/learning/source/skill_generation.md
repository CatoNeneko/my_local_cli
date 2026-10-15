# skill_generation.py：源码导读

独立无工具请求生成Markdown草稿，交统一create_skill执行器保存。

先读专题：[05-extensions.md](../05-extensions.md)。

实际源码：[skill_generation.py](../../../skill_generation.py)。

快照 SHA256：`90a75c1a3ec274fc6f092311fe7bed622e724b4252d22f21f64aa8a6e672b919`；41 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `from model_client import request_message` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `from skill_files import check_new_skill_target` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `from skills import MAX_SKILL_BYTES, check_skill_path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `from tool_runtime import execute_tool` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [generate_skill](#generate-skill) | [8](../../../skill_generation.py#L8) | 无工具独立生成草稿，验证后走create_skill审查保存。 |

<a id="generate-skill"></a>
## generate_skill

无工具独立生成草稿，验证后走create_skill审查保存。

```python
def generate_skill(name, purpose)
```

位置：[8行](../../../skill_generation.py#L8) 至快照 41 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| `purpose` | `未显式注解` | 用户要求生成Skill的用途文字。 |

**调用表达式（静态提取，不含内层独立函数体）**：`check_new_skill_target`、`check_skill_path`、`content.encode`、`content.startswith`、`content.strip`、`execute_tool`、`isinstance`、`len`、`purpose.strip`、`reply.get`、`request_message`、`type`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 9 | `named` | `check_skill_path(name)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 12 | `path` | `'skills/' + name + '/SKILL.md'` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| 13 | `target` | `check_new_skill_target(path)` | 已选定的文件/目录或操作目标，提交前可能需要再次验证。 |
| 18 | `messages` | `[{'role': 'system', 'content': '为 Python 终端编程助手生成一份中文 SKILL.md。只返回 Markdown 正文，不要外层代码围栏。包含用途、适用条件、步骤和验收标准。它是可复用的任务说明，不是程序；不要请求绕过权限…（见完整源码）` | 聊天消息字典列表；哪些是原列表/新副本要看赋值表达式。 |
| 28 | `reply` | `request_message(messages, use_tools=False, include_context=False)` | 模型最终文字或明确终止说明。 |
| 31 | `content` | `reply.get('content')` | 文件正文、消息文字或累计响应；看role与来源。 |
| 34 | `content` | `content.strip()` | 文件正文、消息文字或累计响应；看role与来源。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 9 | 函数体 | 将 `check_skill_path(name)` 赋给 `named`。 |
| 10 | 函数体 | 条件 `not named['ok']`：真时执行body，假时进入else/后续。 |
| 11 | 函数体 / 条件为真 | 返回 `named`，结束当前函数；具体分支见完整源码。 |
| 12 | 函数体 | 将 `'skills/' + name + '/SKILL.md'` 赋给 `path`。 |
| 13 | 函数体 | 将 `check_new_skill_target(path)` 赋给 `target`。 |
| 14 | 函数体 | 条件 `not target['ok']`：真时执行body，假时进入else/后续。 |
| 15 | 函数体 / 条件为真 | 返回 `target`，结束当前函数；具体分支见完整源码。 |
| 16 | 函数体 | 条件 `not isinstance(purpose, str) or not purpose.strip() or len(purpose) > 2000`：真时执行body，假时进入else/后续。 |
| 17 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '用途必须是 1～2000 字符的文字'}`，结束当前函数；具体分支见完整源码。 |
| 18 | 函数体 | 将 `[{'role': 'system', 'content': '为 Python 终端编程助手生成一份中文 SKILL.md。只返回 Markdown 正文，不要外层代码围栏。包含用途、适用条件、步骤和验收标准。它是可复用的任务说明，不是程序；不要请求绕过权限、自动执行命令或虚构测试。实际读取、修改和测试应使用客户端提供的工具与权限流程。…（见完整源码）` 赋给 `messages`。 |
| 27 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 28 | 函数体 / try | 将 `request_message(messages, use_tools=False, include_context=False)` 赋给 `reply`。 |
| 29 | 函数体 / try | 条件 `not isinstance(reply, dict) or reply.get('tool_calls')`：真时执行body，假时进入else/后续。 |
| 30 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': '生成失败：模型应返回文字草稿，不能调用工具'}`，结束当前函数；具体分支见完整源码。 |
| 31 | 函数体 / try | 将 `reply.get('content')` 赋给 `content`。 |
| 32 | 函数体 / try | 条件 `not isinstance(content, str) or not content.strip() or '\x00' in content`：真时执行body，假时进入else/后续。 |
| 33 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': '生成失败：模型未返回有效文字'}`，结束当前函数；具体分支见完整源码。 |
| 34 | 函数体 / try | 将 `content.strip()` 赋给 `content`。 |
| 35 | 函数体 / try | 条件 `content.startswith('```') or len(content.encode('utf-8')) > MAX_SKILL_BYTES`：真时执行body，假时进入else/后续。 |
| 36 | 函数体 / try / 条件为真 | 返回 `{'ok': False, 'error': '生成失败：草稿含外层代码围栏或超过 32 KiB'}`，结束当前函数；具体分支见完整源码。 |
| 37 | 函数体 / try | 返回 `execute_tool('create_skill', {'path': path, 'new_content': content + '\n'}, source='user')`，结束当前函数；具体分支见完整源码。 |
| 38 | 函数体 | except KeyboardInterrupt：只处理匹配类型的异常。 |
| 39 | 函数体 / except KeyboardInterrupt | 返回 `{'ok': False, 'cancelled': True, 'error': 'Skill 生成已取消；已完成的写入不会回滚'}`，结束当前函数；具体分支见完整源码。 |
| 40 | 函数体 | except Exception as error：只处理匹配类型的异常。 |
| 41 | 函数体 / except Exception as error | 返回 `{'ok': False, 'error': 'Skill 生成失败: ' + type(error).__name__}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L11：`named`。
- L15：`target`。
- L17：`{'ok': False, 'error': '用途必须是 1～2000 字符的文字'}`。
- L30：`{'ok': False, 'error': '生成失败：模型应返回文字草稿，不能调用工具'}`。
- L33：`{'ok': False, 'error': '生成失败：模型未返回有效文字'}`。
- L36：`{'ok': False, 'error': '生成失败：草稿含外层代码围栏或超过 32 KiB'}`。
- L37：`execute_tool('create_skill', {'path': path, 'new_content': content + '\n'}, source='user')`。
- L39：`{'ok': False, 'cancelled': True, 'error': 'Skill 生成已取消；已完成的写入不会回滚'}`。
- L41：`{'ok': False, 'error': 'Skill 生成失败: ' + type(error).__name__}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L27。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """模型生成 Skill 草稿，交给统一写入入口确认并保存。"""
0002 | from model_client import request_message
0003 | from skill_files import check_new_skill_target
0004 | from skills import MAX_SKILL_BYTES, check_skill_path
0005 | from tool_runtime import execute_tool
0006 | 
0007 | 
0008 | def generate_skill(name, purpose):
0009 |     named = check_skill_path(name)
0010 |     if not named["ok"]:
0011 |         return named
0012 |     path = "skills/" + name + "/SKILL.md"
0013 |     target = check_new_skill_target(path)
0014 |     if not target["ok"]:
0015 |         return target
0016 |     if not isinstance(purpose, str) or not purpose.strip() or len(purpose) > 2000:
0017 |         return {"ok": False, "error": "用途必须是 1～2000 字符的文字"}
0018 |     messages = [
0019 |         {"role": "system", "content": (
0020 |             "为 Python 终端编程助手生成一份中文 SKILL.md。只返回 Markdown 正文，"
0021 |             "不要外层代码围栏。包含用途、适用条件、步骤和验收标准。"
0022 |             "它是可复用的任务说明，不是程序；不要请求绕过权限、自动执行命令或虚构测试。"
0023 |             "实际读取、修改和测试应使用客户端提供的工具与权限流程。"
0024 |         )},
0025 |         {"role": "user", "content": "Skill 名称: " + name + "\n用途: " + purpose}
0026 |     ]
0027 |     try:
0028 |         reply = request_message(messages, use_tools=False, include_context=False)
0029 |         if not isinstance(reply, dict) or reply.get("tool_calls"):
0030 |             return {"ok": False, "error": "生成失败：模型应返回文字草稿，不能调用工具"}
0031 |         content = reply.get("content")
0032 |         if not isinstance(content, str) or not content.strip() or "\x00" in content:
0033 |             return {"ok": False, "error": "生成失败：模型未返回有效文字"}
0034 |         content = content.strip()
0035 |         if content.startswith("```") or len(content.encode("utf-8")) > MAX_SKILL_BYTES:
0036 |             return {"ok": False, "error": "生成失败：草稿含外层代码围栏或超过 32 KiB"}
0037 |         return execute_tool("create_skill", {"path": path, "new_content": content + "\n"}, source="user")
0038 |     except KeyboardInterrupt:
0039 |         return {'ok': False, 'cancelled': True, 'error': 'Skill 生成已取消；已完成的写入不会回滚'}
0040 |     except Exception as error:
0041 |         return {"ok": False, "error": "Skill 生成失败: " + type(error).__name__}
```
