# 01：从你学过的 Python 走到成品代码

下面例子不是新功能补丁，而是现有代码的简化解释。先把语法翻译成你熟悉的列表、字典、函数和循环。

## 1. `result['ok']`、`.get()` 与真值

```python
result = {"ok": False, "error": "目录不存在"}
if not result["ok"]:
    return result
```

`result['ok']` 得到 `False`；`not False` 得到 `True`，因此进入失败分支，返回错误。条件不是在问“错误值是不是 true”，而是在问“是不是没有成功”。成功时 `not True` 为 `False`，跳过分支继续执行。

| 表达式 | 意义 | 风险/用途 |
| --- | --- | --- |
| `d['content']` | 必须有 content，取其值 | 缺键抛 `KeyError`，适合已经验证的必需字段 |
| `d.get('content', '')` | 没有时给空字符串 | 不会自动验证类型，`None` 仍然是 None |
| `if value` | 按真值判断 | `''`、`[]`、`{}`、`None`、0、False 都是假 |
| `value is None` | 精确判断是否没有值 | 不能用它代替空列表判断 |
| `type(value) is bool` | 必须真是布尔类型 | 防止 `'false'` 字符串伪装布尔值 |
| `isinstance(value, int)` | 是否为 int 或其子类 | Python 的 bool 是 int 子类，`isinstance(True,int)` 为 True |

项目对超时、预算等用 `type(value) is int`，避免把 `True` 误当数值 1。`is` 检查身份，不是一般相等比较；普通字符串比较用 `==`。

## 2. 函数对象、调用与回调

```python
handler = read_file  # 保存这个函数，不执行
result = handler(path)  # 现在执行
```

注册表保存 `handler`，执行器查到它后才调用。`handler` 是函数引用，像变量保存列表一样，变量也能保存函数。若写 `handler = read_file(path)`，保存的会是执行结果，而非函数。

`on_content=output.write` 保存一个回调：模型流式解析器每收到文字就调用它。`@bindings.add('enter')` 注册的回调则由键盘事件触发。理解“是谁在稍后调用这个函数”，就能读懂回调代码。

## 3. 默认参数、关键字参数、`*` 和展开

实际签名：

```python
def request_message(
    messages, *, use_tools=True, include_context=True, stream=False, on_content=None, timeout=120
): ...
```

`messages` 可以位置传参；裸 `*` 后面的参数只能用名字传。这样 `request_message(messages, use_tools=False)` 可读性强，避免三个布尔值顺序写错。

| 写法 | 作用 | 项目位置 |
| --- | --- | --- |
| `timeout=120` | 不传时默认 120 | 模型请求 |
| `*args` | 收集多个位置参数成元组 | browser server 的 `invoke` |
| `**kwargs` | 收集多个关键字参数成字典 | Python 通用语法；不等于信任这些参数 |
| `fn(**normalized)` | 将字典键展开为参数名 | `tool_runtime` 调 handler |
| `{**old, 'ok': False}` | 创建新字典，后面的键覆盖前面的 | 合并结果与附加状态 |
| `[first, *others]` | 展开列表/元组元素 | 路径父目录检查 |

例如 `normalized={'path':'a.py','keyword':'def'}`，`search_file(**normalized)` 等价于 `search_file(path='a.py', keyword='def')`。工具注册表 schema 限制键名，防止模型添加 `source='user'`。

## 4. 拆包、切片和推导式

```python
path, keyword = path_arguments
name, _, argument = text.partition(" ")
```

右侧必须分别有两个、三个元素。`_` 是普通变量，约定表示暂不关心的值。`partition` 永远返回三项；`split(maxsplit=1)` 返回一项或两项，要先检查数量。

`messages[:covered]` 是前 covered 条；`messages[covered:]` 是后续；`text[:200]` 截取前 200 字符；`positions[-2]` 是倒数第二个。切片通常产生新容器。列表中元素若为字典，仍可能共享原字典。

```python
[item["ref"] for item in result["elements"] if not item["disabled"]]
```

等价于建空列表、循环、条件满足则 append。不要认为推导式“有额外魔法”。`{item['ref']: dict(item) for item in ...}` 是字典推导式。`(expression for item in items)` 是生成器表达式，逐个生成而不先创建完整列表。

`any(...)` 在出现一个真值时停止；`all(...)` 在出现一个假值时停止。空序列的 `any` 为 False，`all` 为 True，因此验证数组往往先检查“非空”。

`next(iterator, None)` 取下一个值，没有时给 None。参数验证用它取第一条错误，子代理应用用 `next` 找指定建议；没有默认值时找不到会抛 `StopIteration`。

## 5. `class` 和 `self`：把相关状态放一起

```python
class SessionManager:
    def __init__(self):
        self.current_name = "default"

    def switch(self, name):
        self.current_name = name


manager = SessionManager()
manager.switch("work")
```

`class` 定义一种对象；`__init__` 在创建对象时初始化。`self` 是正在操作的这个对象。`manager.switch('work')` 调用时，Python 自动把 manager 传给 self。

普通局部变量函数结束后通常不再使用；`self.current_name` 存在对象中，下一次方法调用还能读取。这是会话管理、终端输入、浏览器控制需要类的原因。

| 对象 | 它保存的状态 |
| --- | --- |
| `SessionManager` | 当前名称、默认路径、Skill 会话快照 |
| `TerminalInput` | 是否有增强输入 session |
| `ConsoleOutput` | 当前响应文字、是否开始打印 |
| `MCPManager` | 外部服务句柄、异步 portal |
| `BrowserController` | playwright、browser、context、page、refs、截图计数 |

`class ModelResponseError(ValueError)` 是继承：项目定义更具体的异常类型，仍可按 ValueError 捕获。`class ProjectCompleter(Completer)` 实现第三方库要求的方法。

## 6. `with` 不是只用于打开文件

`with open(...) as file` 保证离开时关闭文件。更一般地，`with` 表示进入一段资源/状态范围，再保证退出清理。

类可通过 `__enter__` / `__exit__` 支持 `with`。`MCPManager.__enter__` 建立 portal；`__exit__` 断开服务并关闭 portal。即使中途异常，退出路径仍会运行。

另一种写法是生成器上下文管理器：

```python
@contextmanager
def task_scope(task):
    token = _TASK.set(task)
    try:
        yield
    finally:
        _TASK.reset(token)
```

进入 `with task_scope('修复加法')` 时执行 yield 之前；执行 with 内部代码时暂停在 yield；离开后继续 finally。yield 在这里是“让出控制权”，不是 `return`。它不会提前结束整个上下文管理器。

`ContextVar` 保存当前执行上下文的变量。`.set` 返回 token，`.reset(token)` 恢复原状态，支持嵌套范围，比简单全局赋值更适合请求级审批信息。

## 7. 装饰器：定义函数之后再包一层

```python
@server.tool()
def add(a: int, b: int) -> int:
    return a + b
```

大致等价于先定义 add，再 `add = server.tool()(add)`。这里让 FastMCP 登记函数为工具，从参数注解提取 schema。`@contextmanager` 把含 yield 的生成器函数变成 with 可用的对象；按键装饰器登记键盘回调。

`: int`、`-> int` 是类型注解，普通 Python 不会自动严格检查函数参数。MCP/Pydantic 等库会读取它们。浏览器工具返回 `dict[str, Any]` 是“字符串键、任意值的字典”；当前 SDK 可据此生成结构化输出 schema。曾用裸 `dict` 时只得到文本结果，因此准确注解在这里有实际协议作用。

`Any` 不是权限放开，只是类型描述。JSON Schema 和执行器仍负责参数检查。

## 8. 闭包、`nonlocal`、`lambda` 和 `partial`

文件选择面板的 `selected` 在外层函数中，内层键盘回调要改变它：

```python
selected = 0


def down(event):
    nonlocal selected
    selected += 1
```

`nonlocal` 表示使用最近外层函数的变量，不创建新的局部变量。没有它却做 `selected += 1` 会因先读取尚未赋值的局部变量而出错。修改外层列表内容通常不需要 nonlocal，重新赋值整个变量才需要。

`lambda: page.close()` 是匿名小函数表达式；调用时才求值。`partial(fn, connection, name, schema)` 预先固定前三个参数，之后 `handler(arguments)` 等价于调用完整参数的 fn。MCP 注册项正是用 partial 将不同远端工具绑定到同一个协议执行函数。

## 9. 字符串与字节

| 内容 | 类型 | 场景 |
| --- | --- | --- |
| `'你好'` | str | 人可读文本 |
| `'你好'.encode('utf-8')` | bytes | HTTP、磁盘二进制、进程输入 |
| `raw.decode('utf-8')` | str | 从网络/文件解码 |
| `bytearray()` | 可变字节容器 | 连续追加进程输出 |
| `bytes(output)` | 不可变字节快照 | 在锁内取完整输出后解析 |

字符数不等于字节数，更不等于 token 数。文件 1 MiB 限制是字节；上下文 64000 限制是序列化字符。`errors='replace'` 在进程输出非法编码时替换坏字符，避免整个状态查询崩溃；普通代码文件解码失败则拒绝。

## 10. `Path`、真实路径与符号链接

`Path(__file__)` 是本文件路径；`.parent` 父目录；`.parents[1]` 上两级；`Path.cwd()` 当前工作目录。Path 的 `/` 重载为拼接路径，`root / 'a.py'` 不是除法。

`resolve()` 将相对段和符号链接解析为真实目标；`is_relative_to(root)` 判断真实目标是否在 root 下。不能仅用字符串 `startswith`，因为 `/project-other` 也以 `/project` 开头。

`.exists()`、`.is_file()`、`.is_dir()`、`.is_symlink()` 分别检查存在、普通文件、目录、链接；`.relative_to(root)` 得到项目相对路径。重复检查不是绝对杜绝所有竞态，但用于发现审批期间目标或内容发生变化。

## 11. 异常、finally 与取消

`raise ValueError(...)` 抛异常；`except` 处理；`finally` 无论成功或失败都执行。`raise ... from error` 保留底层异常链；`from None` 隐藏异常链展示。

`KeyboardInterrupt` 继承 BaseException 而非 Exception，因此 `except Exception` 不捕获 Ctrl+C。项目在需要取消并清理的地方单独捕获；`except BaseException` 只用于非常窄的启动清理，随后重新抛出。

`try/finally` 适合确保结束输出、关闭进程/浏览器、恢复变量。清理不是回滚：文件已写入、网页已提交，就不能仅因 Ctrl+C 宣称它没发生。

## 12. async/await、线程与进程

```python
async def read_page():
    result = await page.title()
    return result
```

`async def` 调用后产生协程对象，需由事件循环执行。`await` 等待异步操作完成时可让出执行机会；不是“开一个后台进程”。同步函数不能直接随意 await。

MCP SDK 和 Playwright 是异步接口；CLI 输入与工具循环是同步接口。项目用 anyio portal 在另一个线程中运行事件循环，同步代码通过 `portal.call` 等待异步结果。浏览器 MCP server 自己运行事件循环，不需要主 CLI 直接调用 Playwright。

`asyncio.Queue` 交接异步请求；`Future` 代表稍后完成的结果；`Event` 通知连接清理完成。`async with` 等待异步进入与退出；`asyncio.timeout` 限制范围内操作的时间。

`threading.Thread(..., daemon=True)` 执行后台输出采集；`RLock` 保护共享字典/输出缓冲，不同线程不会随意同时修改关键状态。`subprocess.Popen` 创建独立 OS 进程，`poll()` 查询是否结束，`wait()` 等它结束并回收。

## 13. 导入与共享状态

`import permissions` 后访问 `permissions.PROJECT_ROOT`，会读取该模块当前值。`from permissions import PROJECT_ROOT` 把当时对象绑定到当前模块名称；之后重新赋值 permissions 的同名变量，不会自动改所有已导入名称。

这就是 `workspace.use_workspace` 为什么也显式更新 `sandbox.PROJECT_ROOT`。它对字典状态则 `clear/update`，尽量保留其他模块持有的同一个字典引用。`dict(config)` 为浅拷贝，顶层独立但嵌套对象可能共享；`deepcopy(context)` 连内部字典也复制，用于 Hook 隔离快照。

函数内部 import 常用于避免循环导入，或延迟到真正用功能时才加载依赖。`if __name__ == '__main__'` 只在直接运行文件时执行，import 时不执行入口。

## 14. 为什么这些技术都出现在项目里

| 新知识 | 解决的实际问题 |
| --- | --- |
| 类 | 保存连接、当前会话、输出状态、页面引用 |
| 回调/装饰器 | 流式文字、按键事件、MCP 工具登记 |
| 上下文管理器 | 进入/退出项目、审批范围和连接，保证恢复清理 |
| Schema | 模型给了结构化参数，但必须进一步验证 |
| async/await | SDK 的网络与浏览器等待接口 |
| 线程和锁 | CLI 能继续输入，同时收集后台进程输出 |
| 进程/管道/PTY | 真正跑测试、子代理和交互命令 |
| hash/临时文件/link/replace | 识别修改冲突，控制发布文件的方式 |

读源码时先问“它在解决什么问题”，再问“它为什么用这句语法”。不要反过来背语法名称。
