# hooks.py：源码导读

可信Python回调名单；执行前可拒绝，执行后失败只增加warning。

先读专题：[05-extensions.md](../05-extensions.md)。

实际源码：[hooks.py](../../../hooks.py)。

快照 SHA256：`91e7d31b4df3858b4174b6e184be8b5f6b368ab27f3736bb32fff0f5f2096b6f`；45 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `from copy import deepcopy` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `from config import hooks_config` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 23 | `HOOK_HANDLERS = {'deny_configured_tools': deny_configured_tools, 'report_write_result': report_write_result}` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [deny_configured_tools](#deny-configured-tools) | [7](../../../hooks.py#L7) | 根据可信黑名单拒绝工具，配置格式也检查。 |
| [report_write_result](#report-write-result) | [16](../../../hooks.py#L16) | 打印真实写工具成功/失败状态。 |
| [run_hooks](#run-hooks) | [29](../../../hooks.py#L29) | 按配置调用可信回调，传深拷贝快照并检查ok。 |

<a id="deny-configured-tools"></a>
## deny_configured_tools

根据可信黑名单拒绝工具，配置格式也检查。

```python
def deny_configured_tools(context)
```

位置：[7行](../../../hooks.py#L7) 至快照 13 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `context` | `未显式注解` | 资源上下文或准备的模型请求上下文；看当前来源区分。 |

**调用表达式（静态提取，不含内层独立函数体）**：`all`、`hooks_config.get`、`isinstance`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 8 | `denied` | `hooks_config.get('denied_tools', [])` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 8 | 函数体 | 将 `hooks_config.get('denied_tools', [])` 赋给 `denied`。 |
| 9 | 函数体 | 条件 `not isinstance(denied, list) or not all((isinstance(name, str) for name in denied))`：真时执行body，假时进入else/后续。 |
| 10 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': 'Hook 拒绝名单配置无效'}`，结束当前函数；具体分支见完整源码。 |
| 11 | 函数体 | 条件 `context['name'] in denied`：真时执行body，假时进入else/后续。 |
| 12 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': 'Hook 策略拒绝工具: ' + context['name']}`，结束当前函数；具体分支见完整源码。 |
| 13 | 函数体 | 返回 `{'ok': True}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L10：`{'ok': False, 'error': 'Hook 拒绝名单配置无效'}`。
- L12：`{'ok': False, 'error': 'Hook 策略拒绝工具: ' + context['name']}`。
- L13：`{'ok': True}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="report-write-result"></a>
## report_write_result

打印真实写工具成功/失败状态。

```python
def report_write_result(context)
```

位置：[16行](../../../hooks.py#L16) 至快照 20 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `context` | `未显式注解` | 资源上下文或准备的模型请求上下文；看当前来源区分。 |

**调用表达式（静态提取，不含内层独立函数体）**：`print`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 18 | `status` | `'成功' if context['result']['ok'] else '失败或未执行'` | UI提示或项目规则状态，非自动代表成功。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 17 | 函数体 | 条件 `context['operation'] == 'write'`：真时执行body，假时进入else/后续。 |
| 18 | 函数体 / 条件为真 | 将 `'成功' if context['result']['ok'] else '失败或未执行'` 赋给 `status`。 |
| 19 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`print('[Hook] ' + context['name'] + ': ' + status)`。 |
| 20 | 函数体 | 返回 `{'ok': True}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L20：`{'ok': True}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="run-hooks"></a>
## run_hooks

按配置调用可信回调，传深拷贝快照并检查ok。

```python
def run_hooks(event, context)
```

位置：[29行](../../../hooks.py#L29) 至快照 45 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `event` | `未显式注解` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |
| `context` | `未显式注解` | 资源上下文或准备的模型请求上下文；看当前来源区分。 |

**调用表达式（静态提取，不含内层独立函数体）**：`HOOK_HANDLERS[name]`、`ValueError`、`deepcopy`、`hooks_config.get`、`isinstance`、`result.get`、`str`、`type`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 30 | `names` | `hooks_config.get(event)` | 合法会话/工具/附件名称集合，具体看返回结构。 |
| 38 | `result` | `HOOK_HANDLERS[name](deepcopy(context))` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 30 | 函数体 | 将 `hooks_config.get(event)` 赋给 `names`。 |
| 31 | 函数体 | 条件 `not isinstance(names, list)`：真时执行body，假时进入else/后续。 |
| 32 | 函数体 / 条件为真 | 返回 `{'ok': False, 'error': '缺少有效的 Hook 配置: ' + event}`，结束当前函数；具体分支见完整源码。 |
| 33 | 函数体 | 遍历 `names`，每次绑定 `name`。 |
| 34 | 函数体 / 循环每次 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 35 | 函数体 / 循环每次 / try | 条件 `not isinstance(name, str) or name not in HOOK_HANDLERS`：真时执行body，假时进入else/后续。 |
| 36 | 函数体 / 循环每次 / try / 条件为真 | 抛出 `ValueError('未知 Hook')`。 |
| 38 | 函数体 / 循环每次 / try | 将 `HOOK_HANDLERS[name](deepcopy(context))` 赋给 `result`。 |
| 39 | 函数体 / 循环每次 / try | 条件 `not isinstance(result, dict) or type(result.get('ok')) is not bool`：真时执行body，假时进入else/后续。 |
| 40 | 函数体 / 循环每次 / try / 条件为真 | 抛出 `ValueError('Hook 返回格式无效')`。 |
| 41 | 函数体 / 循环每次 / try | 条件 `not result['ok']`：真时执行body，假时进入else/后续。 |
| 42 | 函数体 / 循环每次 / try / 条件为真 | 返回 `{'ok': False, 'error': 'Hook ' + name + ': ' + str(result.get('error', '拒绝'))}`，结束当前函数；具体分支见完整源码。 |
| 43 | 函数体 / 循环每次 | except Exception as error：只处理匹配类型的异常。 |
| 44 | 函数体 / 循环每次 / except Exception as error | 返回 `{'ok': False, 'error': 'Hook ' + str(name) + ' 失败: ' + type(error).__name__}`，结束当前函数；具体分支见完整源码。 |
| 45 | 函数体 | 返回 `{'ok': True}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L32：`{'ok': False, 'error': '缺少有效的 Hook 配置: ' + event}`。
- L42：`{'ok': False, 'error': 'Hook ' + name + ': ' + str(result.get('error', '拒绝'))}`。
- L44：`{'ok': False, 'error': 'Hook ' + str(name) + ' 失败: ' + type(error).__name__}`。
- L45：`{'ok': True}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L34。
- 推导式/生成器表达式：循环建容器或逐个产生：L9。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """可信本地 Hook：执行前可拒绝，执行后失败只附加警告，不伪装回滚。"""
0002 | from copy import deepcopy
0003 | 
0004 | from config import hooks_config
0005 | 
0006 | 
0007 | def deny_configured_tools(context):
0008 |     denied = hooks_config.get("denied_tools", [])
0009 |     if not isinstance(denied, list) or not all(isinstance(name, str) for name in denied):
0010 |         return {"ok": False, "error": "Hook 拒绝名单配置无效"}
0011 |     if context["name"] in denied:
0012 |         return {"ok": False, "error": "Hook 策略拒绝工具: " + context["name"]}
0013 |     return {"ok": True}
0014 | 
0015 | 
0016 | def report_write_result(context):
0017 |     if context["operation"] == "write":
0018 |         status = "成功" if context["result"]["ok"] else "失败或未执行"
0019 |         print("[Hook] " + context["name"] + ": " + status)
0020 |     return {"ok": True}
0021 | 
0022 | 
0023 | HOOK_HANDLERS = {
0024 |     "deny_configured_tools": deny_configured_tools,
0025 |     "report_write_result": report_write_result
0026 | }
0027 | 
0028 | 
0029 | def run_hooks(event, context):
0030 |     names = hooks_config.get(event)
0031 |     if not isinstance(names, list):
0032 |         return {"ok": False, "error": "缺少有效的 Hook 配置: " + event}
0033 |     for name in names:
0034 |         try:
0035 |             if not isinstance(name, str) or name not in HOOK_HANDLERS:
0036 |                 raise ValueError("未知 Hook")
0037 |             # 回调只收到快照，不能通过修改字典改变待执行参数或结果。
0038 |             result = HOOK_HANDLERS[name](deepcopy(context))
0039 |             if not isinstance(result, dict) or type(result.get("ok")) is not bool:
0040 |                 raise ValueError("Hook 返回格式无效")
0041 |             if not result["ok"]:
0042 |                 return {"ok": False, "error": "Hook " + name + ": " + str(result.get("error", "拒绝"))}
0043 |         except Exception as error:
0044 |             return {"ok": False, "error": "Hook " + str(name) + " 失败: " + type(error).__name__}
0045 |     return {"ok": True}
```
