# audit.py：源码导读

记录工具事件摘要；不保存完整diff，但聊天记录可包含完整工具内容。

先读专题：[03-tools.md](../03-tools.md)。

实际源码：[audit.py](../../../audit.py)。

快照 SHA256：`fca3a33fcdb8438ce23b5d898abe8b15a9ac53c0da62c53cfb88303d343fb8e5`；28 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 1 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 2 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `from datetime import datetime, timezone` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `LOG_PATH = Path(__file__).resolve().parent / 'tool_events.jsonl'` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [record_tool_event](#record-tool-event) | [9](../../../audit.py#L9) | 将UTC时间、tool、ok、错误与审批摘要追加到JSONL；写失败显示警告。 |

<a id="record-tool-event"></a>
## record_tool_event

将UTC时间、tool、ok、错误与审批摘要追加到JSONL；写失败显示警告。

```python
def record_tool_event(name, result)
```

位置：[9行](../../../audit.py#L9) 至快照 28 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `name` | `未显式注解` | 当前工具/服务/会话/Skill的名称；具体由调用位置决定。 |
| `result` | `未显式注解` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |

**调用表达式（静态提取，不含内层独立函数体）**：`LOG_PATH.parent.mkdir`、`datetime.now`、`datetime.now(timezone.utc).isoformat`、`file.write`、`json.dumps`、`open`、`print`、`result.get`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 10 | `event` | `{'time': datetime.now(timezone.utc).isoformat(), 'tool': name, 'ok': result['ok'], 'error': result.get('error', '')}` | SSE待合并data行列表、键盘事件或审计条目，按模块判断。 |
| 17 | `event['approval']` | `result['approval']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 19 | `event['hook_warning']` | `result['hook_warning']` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 21 | `event['cancelled']` | `True` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 10 | 函数体 | 将 `{'time': datetime.now(timezone.utc).isoformat(), 'tool': name, 'ok': result['ok'], 'error': result.get('error', '')}` 赋给 `event`。 |
| 16 | 函数体 | 条件 `'approval' in result`：真时执行body，假时进入else/后续。 |
| 17 | 函数体 / 条件为真 | 将 `result['approval']` 赋给 `event['approval']`。 |
| 18 | 函数体 | 条件 `'hook_warning' in result`：真时执行body，假时进入else/后续。 |
| 19 | 函数体 / 条件为真 | 将 `result['hook_warning']` 赋给 `event['hook_warning']`。 |
| 20 | 函数体 | 条件 `result.get('cancelled')`：真时执行body，假时进入else/后续。 |
| 21 | 函数体 / 条件为真 | 将 `True` 赋给 `event['cancelled']`。 |
| 23 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 24 | 函数体 / try | 计算表达式/调用产生动作：`LOG_PATH.parent.mkdir(parents=True, exist_ok=True)`。 |
| 25 | 函数体 / try | 进入资源/状态范围：`open(LOG_PATH, 'a', encoding='utf-8')` 绑定 `file`；退出执行清理。 |
| 26 | 函数体 / try / with范围 | 计算表达式/调用产生动作：`file.write(json.dumps(event, ensure_ascii=False) + '\n')`。 |
| 27 | 函数体 | except OSError as error：只处理匹配类型的异常。 |
| 28 | 函数体 / except OSError as error | 计算表达式/调用产生动作：`print('工具日志写入失败:', error)`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L23。
- with/yield：资源/状态生命周期或逐个生成：L25。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | import json
0002 | from pathlib import Path
0003 | from datetime import datetime, timezone
0004 | 
0005 | 
0006 | LOG_PATH = Path(__file__).resolve().parent / "tool_events.jsonl"
0007 | 
0008 | 
0009 | def record_tool_event(name, result):
0010 |     event = {
0011 |         "time": datetime.now(timezone.utc).isoformat(),
0012 |         "tool": name,
0013 |         "ok": result["ok"],
0014 |         "error": result.get("error", "")
0015 |     }
0016 |     if "approval" in result:
0017 |         event["approval"] = result["approval"]
0018 |     if "hook_warning" in result:
0019 |         event["hook_warning"] = result["hook_warning"]
0020 |     if result.get('cancelled'):
0021 |         event['cancelled'] = True
0022 | 
0023 |     try:
0024 |         LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
0025 |         with open(LOG_PATH, "a", encoding="utf-8") as file:
0026 |             file.write(json.dumps(event, ensure_ascii=False) + "\n")
0027 |     except OSError as error:
0028 |         print("工具日志写入失败:", error)
```
