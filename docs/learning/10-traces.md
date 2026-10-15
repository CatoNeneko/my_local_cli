# 10：拿具体数据，手工跑通代码

不要只背流程图。下面是**教学示例数据**，不是本次真实执行记录。目标是跟着每一步看变量怎样改变。

## A. 一个读取任务完整经过几层

假设目标项目有 `calc.py`，当前历史为空，你输入“读取 calc.py，解释 add”。

| 时刻 | messages 内容 | 函数动作 |
| --- | --- | --- |
| 输入前 | `[]` | load_history 恢复空列表 |
| 保存用户后 | `[user任务]` | script 先append内存和JSONL |
| 第一次请求 | 原messages不被规则注入污染 | prepare_context生成新请求列表 |
| 模型回调用 | 原messages仍只有user | request_message返回assistant字典 |
| 执行前 | `round_messages=[assistant调用]` | agent取name/arguments |
| 文件成功 | 原messages仍只有user | runtime检查、handler读文件返回dict |
| 保存批次 | `[user,assistant调用,tool结果]` | append_messages后messages.extend |
| 第二次请求 | 请求含前述完整链+规则 | 模型看到真实文件内容 |
| 最终文字 | agent先return文字 | 没有tool_calls，工具循环结束 |
| 主循环保存 | `[user,assistant调用,tool结果,assistant最终]` | script写最终消息并显示 |

这里规则消息只属于“请求列表”，不能混进“messages原列表”。若你把build_model_messages的结果永久赋到历史里，每次又注入一次，会越叠越多。

### 追踪嵌套字典

```python
call = {"function": {"name": "read_file", "arguments": {"path": "calc.py"}}}
function = call["function"]
name = function["name"]
arguments = function["arguments"]
```

function是含name/arguments的字典，name是字符串，arguments是含path的字典。`spec=TOOL_REGISTRY[name]` 取工具配置；`normalized`合并默认值并通过schema；`spec['handler'](**normalized)` 才是真读文件。

结果 `{'ok':True,'content':'def add(a,b): ...'}` 用json.dumps包进tool消息content。下一次模型请求保留同一个调用和结果配对。不要将tool结果直接当assistant最终回答保存。

## B. 两个工具中第二个取消

假设响应有read_file和edit_file：

1. tool_count由0→1，read成功，round_messages添加对应tool结果。
2. tool_count由1→2，edit确认时Ctrl+C，runtime捕获并返回cancelled=True。
3. agent将cancelled记为True，记录第二个失败结果。
4. 同批若还有第三工具，直接生成未执行的取消结果，不调用handler。
5. 保存整批，然后return取消文字，主循环回到输入。

读操作已发生，若此前更早轮次文件已写入也保留。取消不会清空messages，也不会退出整个CLI，除非发生在最外层输入/启动退出路径。

## C. 编辑期间文件被别人改过

| 时刻 | 字节 |
| --- | --- |
| prepare读取 | `original_bytes=b'return a-b\n'` |
| 模型提交新内容 | `new_bytes=b'return a+b\n'` |
| 展示diff时外部编辑器改了文件 | 当前文件变成 `b'return 0\n'` |
| apply检查 | 当前字节不等于original_bytes |
| 返回 | `ok=False`，请求重新生成修改 |

为什么不能只看文件名一样？同一路径的内容已经变化，直接写会覆盖别人刚做的工作。hash用于子代理跨进程建议的旧版本检查，父patches用原字节比较，原理都是确认“基于哪个版本”。

## D. 上下文里的 pending 队列

| 消息 | pending变化 | valid_turn判断 |
| --- | --- | --- |
| user任务 | `[]` | 合法开始 |
| assistant调用read和tests | `[]→['read_file','run_tests']` | 等两个结果 |
| tool read | pop第一个→`['run_tests']` | 名称匹配 |
| tool tests | pop第一个→`[]` | 名称匹配 |
| assistant最终 | `[]` | 合法，无等待 |

若第二条tool变成edit_file，名称不匹配，整轮无效。若只保存read结果，末尾pending非空，无效。`pop(0)` 修改原列表并返回第一元素，不等于读取`pending[0]`。兼容API另有ID配对，这层主要检查工具名称和顺序。

## E. PTY 的一段状态变化

```text
runtime.start_pty -> processes.launch -> task_id="ab12...", state="running"
harness.tasks.processes.JOBS[id].output = bytearray()
后台collect读取b"hello\r\n" -> output追加7字节
runtime.inspect_task(offset=0) -> output="hello\r\n", next_offset=7
进程结束 -> collect清理fd -> done=True
runtime.inspect_task(offset=7) -> output="", state="finished", exit_code=0
```

offset是字节偏移，不是行数或字符数。UTF-8中文跨块可产生临时替换字符，当前实现是按块decode(errors='replace')，并不是完整增量解码器。查询ok=True只是查询成功，必须结合退出码判断命令。

## F. 浏览器为何每一步换ref

```text
open_page -> Name输入框ref=a1-1，Greet按钮ref=a1-2
fill(a1-1,'Ada') -> 新快照Name=b2-1，按钮=b2-2
click(a1-2) -> 拒绝：过期编号
click(b2-2) -> 成功，新快照显示Hello Ada
read_page -> 又生成一份新编号
screenshot -> 保存文件，返回path
```

ref不是永远绑定的DOM编号，也不是用户可指定的任意selector。每次结果都是“用这一份最新可见元素表操作”。页面动态改变时重新读取，比在旧坐标上盲点更可控。

## G. 子代理的三个数据容器

| 容器 | 在哪个进程 | 装什么 |
| --- | --- | --- |
| 父 messages | 主CLI | 用户任务、spawn/task/apply等真实工具链 |
| 子 messages | worker | 独立task+规则+子代理自己的工具结果；可包含获准的 edit/create/test/PTY 操作 |
| `harness.tasks.processes.JOBS` | 当前任务服务进程 | Popen、采集输出和任务状态；不与子进程共享普通 Python 字典 |
| `TaskApprovalStore` | 本地任务审批存储 | pending 请求及 approve/reject 后一次性消费的结果 |
| 子 `PROPOSALS` → 任务结果 | 可选建议功能 | `propose_edit` / `propose_file` 的完整建议与旧 hash，不是所有子代理修改的必经路径 |

这些数据容器不会因为变量同名自动共享。子代理可直接请求统一 Runtime；manual 审批等待期间会挂起，收到一次性决定后再继续。auto 写入走独立 review_write。工作区写锁只在已审批写入的最终提交阶段持有。

## H. 从这些例子反推代码职责

对任意一句代码，分别问：

1. 左边变量当前是什么类型？
2. 右边函数返回什么类型？
3. 这一步有没有文件/进程/网络副作用？
4. 失败怎么传播：返回ok=False还是raise？
5. 谁保证资源关闭？
6. 原始数据是否被改了，还是只生成新副本？

能用这六个问题跟踪A–G，你就能从成品中独立读懂一个新函数，而不是等待AI再逐句翻译。
