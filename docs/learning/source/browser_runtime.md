# browser_runtime.py：源码导读

Playwright单页面控制器；固定快照、临时ref、PNG文件、临时Cookie。

先读专题：[05-extensions.md](../05-extensions.md)。

实际源码：[browser_runtime.py](../../../browser_runtime.py)。

快照 SHA256：`52c45911c5a9d5a1fb30ef95850dec3d2c12889ea1d35e77650719f6d0bc33cb`；170 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import asyncio` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import json` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `from urllib.parse import urlsplit` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `import uuid` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `MAX_TEXT = 2000` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 9 | `MAX_ELEMENTS = 15` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 10 | `MAX_SCREENSHOTS = 32` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 27 | `SNAPSHOT_SCRIPT = '({prefix, textLimit, elementLimit}) => {\n    const body = document.body;\n    const text = (body?.innerText \|\| \'\').slice(0, textLimit + 1);\n    con…（见完整源码）` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [validate_url](#validate-url) | [13](../../../browser_runtime.py#L13) | 检查HTTP(S)、凭据、长度、端口与控制字符。 |
| [BrowserController.__init__](#browsercontroller---init--) | [48](../../../browser_runtime.py#L48) | 构造对象的初始状态；调用类创建对象时自动执行。 |
| [BrowserController._start](#browsercontroller--start) | [54](../../../browser_runtime.py#L54) | 惰性启动Playwright/Chromium临时单页环境，失败清理。 |
| [BrowserController._route](#browsercontroller--route) | [73](../../../browser_runtime.py#L73) | 校验页面子资源URL并继续或拒绝。 |
| [BrowserController._require_page](#browsercontroller--require-page) | [81](../../../browser_runtime.py#L81) | 页面存在且未关闭，否则提醒先open。 |
| [BrowserController.open](#browsercontroller-open) | [86](../../../browser_runtime.py#L86) | 校验URL后惰性启动，goto等待文档，再返回带HTTP状态的快照。 |
| [BrowserController.read](#browsercontroller-read) | [95](../../../browser_runtime.py#L95) | 固定JS提取页面正文与元素，限制JSON体积后更新最新refs映射。 |
| [BrowserController._locator](#browsercontroller--locator) | [117](../../../browser_runtime.py#L117) | 只接受最新ref并生成内部CSS locator。 |
| [BrowserController.click](#browsercontroller-click) | [123](../../../browser_runtime.py#L123) | 使用最新ref点击，等待domcontentloaded后返回新快照。 |
| [BrowserController.fill](#browsercontroller-fill) | [129](../../../browser_runtime.py#L129) | 验证输入长度与禁密码/文件，locator.fill后返回新编号快照。 |
| [BrowserController.wait_text](#browsercontroller-wait-text) | [138](../../../browser_runtime.py#L138) | 等可见文字出现，5秒超时，再读取新快照。 |
| [BrowserController.screenshot](#browsercontroller-screenshot) | [144](../../../browser_runtime.py#L144) | 保存有限视口PNG到固定私有目录、独占随机名字。 |
| [BrowserController.close](#browsercontroller-close) | [160](../../../browser_runtime.py#L160) | 清空浏览器状态并关闭browser/Playwright。 |

<a id="validate-url"></a>
## validate_url

检查HTTP(S)、凭据、长度、端口与控制字符。

```python
def validate_url(url)
```

位置：[13行](../../../browser_runtime.py#L13) 至快照 23 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `url` | `未显式注解` | 待打开HTTP(S)地址，验证后才能导航。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ValueError`、`any`、`char.isspace`、`isinstance`、`len`、`ord`、`urlsplit`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 17 | `parsed` | `urlsplit(url)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 20 | `_` | `parsed.port` | 约定不再使用的临时值；它仍是普通Python变量。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 14 | 函数体 | 条件 `not isinstance(url, str) or not url or len(url) > 2048 or any((ord(char) < 32 or char.isspace() for char in url))`：真时执行body，假时进入else/后续。 |
| 15 | 函数体 / 条件为真 | 抛出 `ValueError('URL 必须是 1–2048 字符的 HTTP(S) 地址')`。 |
| 16 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 17 | 函数体 / try | 将 `urlsplit(url)` 赋给 `parsed`。 |
| 18 | 函数体 / try | 条件 `parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username is not None or (parsed.password is not None)`：真时执行body，假时进入else/后续。 |
| 19 | 函数体 / try / 条件为真 | 抛出 `ValueError()`。 |
| 20 | 函数体 / try | 将 `parsed.port` 赋给 `_`。 |
| 21 | 函数体 | except ValueError as error：只处理匹配类型的异常。 |
| 22 | 函数体 / except ValueError as error | 抛出 `ValueError('只允许无嵌入凭据的 HTTP(S) URL；不支持 file/data/javascript')`，异常链关联 `error`。 |
| 23 | 函数体 | 返回 `url`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L23：`url`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="browsercontroller---init--"></a>
## BrowserController.__init__

构造对象的初始状态；self上的字段会在后续方法中继续使用。

```python
def __init__(self, screenshot_directory)
```

位置：[48行](../../../browser_runtime.py#L48) 至快照 52 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `screenshot_directory` | `未显式注解` | 可信父客户端指定的私有截图目录，模型不能任意传文件路径。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 49 | `self.screenshot_directory` | `Path(screenshot_directory)` | 可信父客户端指定的私有截图目录，模型不能任意传文件路径。 |
| 50 | `self.playwright,self.browser,self.context,self.page` | `None` | Playwright异步驱动，退出要stop。；Chromium浏览器对象，close时终止。；资源上下文或准备的模型请求上下文；看当前来源区分。；Playwright单页面对象，具体DOM操作由它执行。 |
| 51 | `self.refs` | `{}` | 当前页面最新元素编号到快照字段的映射，读取后重建。 |
| 52 | `self.screenshots` | `0` | 该服务累计保存截图计数，达到上限拒绝。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 49 | 函数体 | 将 `Path(screenshot_directory)` 赋给 `self.screenshot_directory`。 |
| 50 | 函数体 | 将 `None` 赋给 `self.playwright`, `self.browser`, `self.context`, `self.page`。 |
| 51 | 函数体 | 将 `{}` 赋给 `self.refs`。 |
| 52 | 函数体 | 将 `0` 赋给 `self.screenshots`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="browsercontroller--start"></a>
## BrowserController._start

惰性启动Playwright/Chromium临时单页环境，失败清理。

```python
async def _start(self)
```

位置：[54行](../../../browser_runtime.py#L54) 至快照 71 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：`async_playwright`、`async_playwright().start`、`self.browser.is_connected`、`self.browser.new_context`、`self.close`、`self.context.new_page`、`self.context.on`、`self.context.route`、`self.context.set_default_navigation_timeout`、`self.context.set_default_timeout`、`self.page.on`、`self.playwright.chromium.launch`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 58 | `self.playwright` | `await async_playwright().start()` | Playwright异步驱动，退出要stop。 |
| 60 | `self.browser` | `await self.playwright.chromium.launch(headless=True, chromium_sandbox=True, timeout=15000)` | Chromium浏览器对象，close时终止。 |
| 61 | `self.context` | `await self.browser.new_context(viewport={'width': 1280, 'height': 720}, accept_downloads=False, service_workers='block', permissio…（见完整源码）` | 资源上下文或准备的模型请求上下文；看当前来源区分。 |
| 66 | `self.page` | `await self.context.new_page()` | Playwright单页面对象，具体DOM操作由它执行。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 55 | 函数体 | 条件 `self.browser is not None and self.browser.is_connected()`：真时执行body，假时进入else/后续。 |
| 56 | 函数体 / 条件为真 | 返回 `None`，结束当前函数；具体分支见完整源码。 |
| 57 | 函数体 | 在此处导入依赖：`from playwright.async_api import async_playwright`；局部导入可延迟加载或避免循环。 |
| 58 | 函数体 | 将 `await async_playwright().start()` 赋给 `self.playwright`。 |
| 59 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 60 | 函数体 / try | 将 `await self.playwright.chromium.launch(headless=True, chromium_sandbox=True, timeout=15000)` 赋给 `self.browser`。 |
| 61 | 函数体 / try | 将 `await self.browser.new_context(viewport={'width': 1280, 'height': 720}, accept_downloads=False, service_workers='block', permissions=[])` 赋给 `self.context`。 |
| 63 | 函数体 / try | 计算表达式/调用产生动作：`self.context.set_default_timeout(5000)`。 |
| 64 | 函数体 / try | 计算表达式/调用产生动作：`self.context.set_default_navigation_timeout(10000)`。 |
| 65 | 函数体 / try | 计算表达式/调用产生动作：`await self.context.route('**/*', self._route)`。 |
| 66 | 函数体 / try | 将 `await self.context.new_page()` 赋给 `self.page`。 |
| 67 | 函数体 / try | 计算表达式/调用产生动作：`self.context.on('page', lambda page: asyncio.create_task(page.close()) if page != self.page else None)`。 |
| 68 | 函数体 / try | 计算表达式/调用产生动作：`self.page.on('download', lambda download: asyncio.create_task(download.cancel()))`。 |
| 69 | 函数体 | except BaseException：只处理匹配类型的异常。 |
| 70 | 函数体 / except BaseException | 计算表达式/调用产生动作：`await self.close()`。 |
| 71 | 函数体 / except BaseException | 抛出 `None`。 |

**实际返回分支**：

- L56：`None`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="browsercontroller--route"></a>
## BrowserController._route

校验页面子资源URL并继续或拒绝。

```python
async def _route(self, route)
```

位置：[73行](../../../browser_runtime.py#L73) 至快照 79 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `route` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`route.abort`、`route.continue_`、`validate_url`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 74 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 75 | 函数体 / try | 计算表达式/调用产生动作：`validate_url(route.request.url)`。 |
| 76 | 函数体 | except ValueError：只处理匹配类型的异常。 |
| 77 | 函数体 / except ValueError | 计算表达式/调用产生动作：`await route.abort()`。 |
| 79 | 函数体 / try成功else | 计算表达式/调用产生动作：`await route.continue_()`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

<a id="browsercontroller--require-page"></a>
## BrowserController._require_page

页面存在且未关闭，否则提醒先open。

```python
def _require_page(self)
```

位置：[81行](../../../browser_runtime.py#L81) 至快照 84 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ValueError`、`self.page.is_closed`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 82 | 函数体 | 条件 `self.page is None or self.page.is_closed()`：真时执行body，假时进入else/后续。 |
| 83 | 函数体 / 条件为真 | 抛出 `ValueError('尚未打开页面，请先调用 open_page')`。 |
| 84 | 函数体 | 返回 `self.page`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L84：`self.page`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="browsercontroller-open"></a>
## BrowserController.open

校验URL后惰性启动，goto等待文档，再返回带HTTP状态的快照。

```python
async def open(self, url)
```

位置：[86行](../../../browser_runtime.py#L86) 至快照 93 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `url` | `未显式注解` | 待打开HTTP(S)地址，验证后才能导航。 |

**调用表达式（静态提取，不含内层独立函数体）**：`self._start`、`self.page.goto`、`self.read`、`self.refs.clear`、`validate_url`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 90 | `response` | `await self.page.goto(url, wait_until='domcontentloaded')` | HTTP响应流或异步请求Future，依当前模块。 |
| 91 | `result` | `await self.read()` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 92 | `result['http_status']` | `response.status if response else None` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 87 | 函数体 | 计算表达式/调用产生动作：`validate_url(url)`。 |
| 88 | 函数体 | 计算表达式/调用产生动作：`await self._start()`。 |
| 89 | 函数体 | 计算表达式/调用产生动作：`self.refs.clear()`。 |
| 90 | 函数体 | 将 `await self.page.goto(url, wait_until='domcontentloaded')` 赋给 `response`。 |
| 91 | 函数体 | 将 `await self.read()` 赋给 `result`。 |
| 92 | 函数体 | 将 `response.status if response else None` 赋给 `result['http_status']`。 |
| 93 | 函数体 | 返回 `result`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L93：`result`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="browsercontroller-read"></a>
## BrowserController.read

固定JS提取页面正文与元素，限制JSON体积后更新最新refs映射。

```python
async def read(self)
```

位置：[95行](../../../browser_runtime.py#L95) 至快照 115 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：`dict`、`json.dumps`、`len`、`page.evaluate`、`page.title`、`self._require_page`、`snapshot['elements'].pop`、`uuid.uuid4`、`validate_url`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 96 | `page` | `self._require_page()` | Playwright单页面对象，具体DOM操作由它执行。 |
| 99 | `result` | `await page.evaluate(SNAPSHOT_SCRIPT, {'prefix': uuid.uuid4().hex[:8], 'textLimit': MAX_TEXT, 'elementLimit': MAX_ELEMENTS})` | 当前动作的结果；通常含ok，具体附加字段由调用的函数决定。 |
| 101 | `self.refs` | `{item['ref']: dict(item) for item in result['elements']}` | 当前页面最新元素编号到快照字段的映射，读取后重建。 |
| 102 | `snapshot` | `{'ok': True, 'url': page.url[:300], 'url_truncated': len(page.url) > 300, 'title': (await page.title())[:200], **result}` | 防并发变化的hash或页面快照；需根据所在函数区分。 |
| 107 | `snapshot['text']` | `snapshot['text'][:-200]` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 108 | `snapshot['text_truncated']` | `True` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 111 | `snapshot['elements_truncated']` | `True` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 114 | `self.refs` | `{item['ref']: dict(item) for item in snapshot['elements']}` | 当前页面最新元素编号到快照字段的映射，读取后重建。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 96 | 函数体 | 将 `self._require_page()` 赋给 `page`。 |
| 97 | 函数体 | 条件 `page.url != 'about:blank'`：真时执行body，假时进入else/后续。 |
| 98 | 函数体 / 条件为真 | 计算表达式/调用产生动作：`validate_url(page.url)`。 |
| 99 | 函数体 | 将 `await page.evaluate(SNAPSHOT_SCRIPT, {'prefix': uuid.uuid4().hex[:8], 'textLimit': MAX_TEXT, 'elementLimit': MAX_ELEMENTS})` 赋给 `result`。 |
| 101 | 函数体 | 将 `{item['ref']: dict(item) for item in result['elements']}` 赋给 `self.refs`。 |
| 102 | 函数体 | 将 `{'ok': True, 'url': page.url[:300], 'url_truncated': len(page.url) > 300, 'title': (await page.title())[:200], **result}` 赋给 `snapshot`。 |
| 105 | 函数体 | 循环检查 `len(json.dumps(snapshot, ensure_ascii=False)) > 4000`，break/return/异常可结束。 |
| 106 | 函数体 / 循环每次 | 条件 `snapshot['text']`：真时执行body，假时进入else/后续。 |
| 107 | 函数体 / 循环每次 / 条件为真 | 将 `snapshot['text'][:-200]` 赋给 `snapshot['text']`。 |
| 108 | 函数体 / 循环每次 / 条件为真 | 将 `True` 赋给 `snapshot['text_truncated']`。 |
| 109 | 函数体 / 循环每次 / 条件为假/elif | 条件 `snapshot['elements']`：真时执行body，假时进入else/后续。 |
| 110 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 | 计算表达式/调用产生动作：`snapshot['elements'].pop()`。 |
| 111 | 函数体 / 循环每次 / 条件为假/elif / 条件为真 | 将 `True` 赋给 `snapshot['elements_truncated']`。 |
| 113 | 函数体 / 循环每次 / 条件为假/elif / 条件为假/elif | break结束最近一层循环。 |
| 114 | 函数体 | 将 `{item['ref']: dict(item) for item in snapshot['elements']}` 赋给 `self.refs`。 |
| 115 | 函数体 | 返回 `snapshot`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L115：`snapshot`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="browsercontroller--locator"></a>
## BrowserController._locator

只接受最新ref并生成内部CSS locator。

```python
def _locator(self, ref)
```

位置：[117行](../../../browser_runtime.py#L117) 至快照 121 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `ref` | `未显式注解` | 最新页面快照里的临时元素编号，旧快照编号过期。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ValueError`、`self._require_page`、`self.page.locator`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 118 | 函数体 | 计算表达式/调用产生动作：`self._require_page()`。 |
| 119 | 函数体 | 条件 `ref not in self.refs`：真时执行body，假时进入else/后续。 |
| 120 | 函数体 / 条件为真 | 抛出 `ValueError('元素编号不存在或已过期，请重新 read_page 并使用最新 ref')`。 |
| 121 | 函数体 | 返回 `self.page.locator('[data-ai-cli-ref="' + ref + '"]')`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L121：`self.page.locator('[data-ai-cli-ref="' + ref + '"]')`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="browsercontroller-click"></a>
## BrowserController.click

使用最新ref点击，等待domcontentloaded后返回新快照。

```python
async def click(self, ref)
```

位置：[123行](../../../browser_runtime.py#L123) 至快照 127 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `ref` | `未显式注解` | 最新页面快照里的临时元素编号，旧快照编号过期。 |

**调用表达式（静态提取，不含内层独立函数体）**：`locator.click`、`self._locator`、`self.page.wait_for_load_state`、`self.read`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 124 | `locator` | `self._locator(ref)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 124 | 函数体 | 将 `self._locator(ref)` 赋给 `locator`。 |
| 125 | 函数体 | 计算表达式/调用产生动作：`await locator.click()`。 |
| 126 | 函数体 | 计算表达式/调用产生动作：`await self.page.wait_for_load_state('domcontentloaded')`。 |
| 127 | 函数体 | 返回 `await self.read()`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L127：`await self.read()`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="browsercontroller-fill"></a>
## BrowserController.fill

验证输入长度与禁密码/文件，locator.fill后返回新编号快照。

```python
async def fill(self, ref, value)
```

位置：[129行](../../../browser_runtime.py#L129) 至快照 136 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `ref` | `未显式注解` | 最新页面快照里的临时元素编号，旧快照编号过期。 |
| `value` | `未显式注解` | 正在检查的通用值；其实际类型以赋值与后续校验为准。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ValueError`、`isinstance`、`len`、`locator.fill`、`locator.get_attribute`、`self._locator`、`self.read`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 132 | `locator` | `self._locator(ref)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 130 | 函数体 | 条件 `not isinstance(value, str) or len(value) > 4000 or '\x00' in value`：真时执行body，假时进入else/后续。 |
| 131 | 函数体 / 条件为真 | 抛出 `ValueError('输入内容最多 4000 字符，不允许空字符')`。 |
| 132 | 函数体 | 将 `self._locator(ref)` 赋给 `locator`。 |
| 133 | 函数体 | 条件 `await locator.get_attribute('type') in ('file', 'password')`：真时执行body，假时进入else/后续。 |
| 134 | 函数体 / 条件为真 | 抛出 `ValueError('基础版不支持文件上传或密码输入')`。 |
| 135 | 函数体 | 计算表达式/调用产生动作：`await locator.fill(value)`。 |
| 136 | 函数体 | 返回 `await self.read()`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L136：`await self.read()`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="browsercontroller-wait-text"></a>
## BrowserController.wait_text

等可见文字出现，5秒超时，再读取新快照。

```python
async def wait_text(self, text)
```

位置：[138行](../../../browser_runtime.py#L138) 至快照 142 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |
| `text` | `未显式注解` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ValueError`、`isinstance`、`len`、`self._require_page`、`self._require_page().get_by_text`、`self._require_page().get_by_text(text, exact=False).first.wait_for`、`self.read`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 139 | 函数体 | 条件 `not isinstance(text, str) or not text or len(text) > 200`：真时执行body，假时进入else/后续。 |
| 140 | 函数体 / 条件为真 | 抛出 `ValueError('等待文字必须是 1–200 字符')`。 |
| 141 | 函数体 | 计算表达式/调用产生动作：`await self._require_page().get_by_text(text, exact=False).first.wait_for(state='visible', timeout=5000)`。 |
| 142 | 函数体 | 返回 `await self.read()`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L142：`await self.read()`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="browsercontroller-screenshot"></a>
## BrowserController.screenshot

保存有限视口PNG到固定私有目录、独占随机名字。

```python
async def screenshot(self)
```

位置：[144行](../../../browser_runtime.py#L144) 至快照 158 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：`ValueError`、`any`、`directory.mkdir`、`file.write`、`len`、`path.is_symlink`、`path.open`、`self._require_page`、`self._require_page().screenshot`、`str`、`uuid.uuid4`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 147 | `raw` | `await self._require_page().screenshot(type='png', full_page=False, timeout=5000)` | 未解码字节/完整输出快照，按编码与限额再处理。 |
| 150 | `directory` | `self.screenshot_directory` | 当前目录路径，遍历/候选/会话使用。 |
| 154 | `path` | `directory / (uuid.uuid4().hex + '.png')` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 145 | 函数体 | 条件 `self.screenshots >= MAX_SCREENSHOTS`：真时执行body，假时进入else/后续。 |
| 146 | 函数体 / 条件为真 | 抛出 `ValueError('本次浏览器服务截图达到 32 张上限')`。 |
| 147 | 函数体 | 将 `await self._require_page().screenshot(type='png', full_page=False, timeout=5000)` 赋给 `raw`。 |
| 148 | 函数体 | 条件 `len(raw) > 4194304`：真时执行body，假时进入else/后续。 |
| 149 | 函数体 / 条件为真 | 抛出 `ValueError('截图超过 4 MiB，未保存')`。 |
| 150 | 函数体 | 将 `self.screenshot_directory` 赋给 `directory`。 |
| 151 | 函数体 | 条件 `any((path.is_symlink() for path in (directory, *directory.parents)))`：真时执行body，假时进入else/后续。 |
| 152 | 函数体 / 条件为真 | 抛出 `ValueError('截图目录不能含符号链接')`。 |
| 153 | 函数体 | 计算表达式/调用产生动作：`directory.mkdir(parents=True, exist_ok=True)`。 |
| 154 | 函数体 | 将 `directory / (uuid.uuid4().hex + '.png')` 赋给 `path`。 |
| 155 | 函数体 | 进入资源/状态范围：`path.open('xb')` 绑定 `file`；退出执行清理。 |
| 156 | 函数体 / with范围 | 计算表达式/调用产生动作：`file.write(raw)`。 |
| 157 | 函数体 | 更新已有变量：`self.screenshots += 1`。 |
| 158 | 函数体 | 返回 `{'ok': True, 'path': str(path), 'bytes': len(raw), 'message': '截图仅保存为文件，未发送给视觉模型'}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L158：`{'ok': True, 'path': str(path), 'bytes': len(raw), 'message': '截图仅保存为文件，未发送给视觉模型'}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="browsercontroller-close"></a>
## BrowserController.close

清空浏览器状态并关闭browser/Playwright。

```python
async def close(self)
```

位置：[160行](../../../browser_runtime.py#L160) 至快照 170 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `self` | `未显式注解` | 正在操作的对象；字段在方法调用之间保留。 |

**调用表达式（静态提取，不含内层独立函数体）**：`browser.close`、`playwright.stop`、`self.refs.clear`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 161 | `(browser, playwright)` | `(self.browser, self.playwright)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 162 | `self.browser,self.playwright,self.context,self.page` | `None` | Chromium浏览器对象，close时终止。；Playwright异步驱动，退出要stop。；资源上下文或准备的模型请求上下文；看当前来源区分。；Playwright单页面对象，具体DOM操作由它执行。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 161 | 函数体 | 将 `(self.browser, self.playwright)` 赋给 `(browser, playwright)`。 |
| 162 | 函数体 | 将 `None` 赋给 `self.browser`, `self.playwright`, `self.context`, `self.page`。 |
| 163 | 函数体 | 计算表达式/调用产生动作：`self.refs.clear()`。 |
| 164 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 165 | 函数体 / try | 条件 `browser is not None`：真时执行body，假时进入else/后续。 |
| 166 | 函数体 / try / 条件为真 | 计算表达式/调用产生动作：`await browser.close()`。 |
| 168 | 函数体 / finally保证清理 | 条件 `playwright is not None`：真时执行body，假时进入else/后续。 |
| 169 | 函数体 / finally保证清理 / 条件为真 | 计算表达式/调用产生动作：`await playwright.stop()`。 |
| 170 | 函数体 | 返回 `{'ok': True, 'message': '浏览器及临时会话已关闭'}`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L170：`{'ok': True, 'message': '浏览器及临时会话已关闭'}`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- class：对象状态与方法/继承：L47。
- try/except/finally：异常与保证清理：L16, L59, L74, L164。
- async/await：异步等待与资源范围：L54, L58, L60, L61, L65, L66, L70, L73, L77, L79, L86, L88, L90, L91, L95, L99, L103, L123, L125, L126, L127, L129, L133, L135, L136, L138, L141, L142, L144, L147, L160, L166, L169。
- with/yield：资源/状态生命周期或逐个生成：L155。
- 推导式/生成器表达式：循环建容器或逐个产生：L14, L101, L114, L151。
- lambda：小回调函数：L67, L68。
- 星号展开：展开已有容器：L151。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """单页面、临时上下文的浏览器执行器；不暴露任意 JS、Shell 或文件路径。"""
0002 | import asyncio
0003 | import json
0004 | from pathlib import Path
0005 | from urllib.parse import urlsplit
0006 | import uuid
0007 | 
0008 | MAX_TEXT = 2000
0009 | MAX_ELEMENTS = 15
0010 | MAX_SCREENSHOTS = 32
0011 | 
0012 | 
0013 | def validate_url(url):
0014 |     if not isinstance(url, str) or not url or len(url) > 2048 or any(ord(char) < 32 or char.isspace() for char in url):
0015 |         raise ValueError('URL 必须是 1–2048 字符的 HTTP(S) 地址')
0016 |     try:
0017 |         parsed = urlsplit(url)
0018 |         if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username is not None or parsed.password is not None:
0019 |             raise ValueError()
0020 |         _ = parsed.port
0021 |     except ValueError as error:
0022 |         raise ValueError('只允许无嵌入凭据的 HTTP(S) URL；不支持 file/data/javascript') from error
0023 |     return url
0024 | 
0025 | 
0026 | # 固定的内部 JS，仅提取 DOM 与生成元素编号；模型没有 evaluate 接口。
0027 | SNAPSHOT_SCRIPT = """({prefix, textLimit, elementLimit}) => {
0028 |     const body = document.body;
0029 |     const text = (body?.innerText || '').slice(0, textLimit + 1);
0030 |     const candidates = [...document.querySelectorAll('a[href],button,input,textarea,select,[role="button"],[contenteditable="true"]')].slice(0,200);
0031 |     const elements = [];
0032 |     for (const node of candidates) {
0033 |         const box = node.getBoundingClientRect();
0034 |         if (!box.width || !box.height || getComputedStyle(node).visibility === 'hidden') continue;
0035 |         if (elements.length >= elementLimit) break;
0036 |         const ref = prefix + '-' + (elements.length + 1);
0037 |         node.setAttribute('data-ai-cli-ref', ref);
0038 |         const label = node.getAttribute('aria-label') || node.labels?.[0]?.innerText || node.getAttribute('placeholder') || node.innerText || node.getAttribute('name') || '';
0039 |         elements.push({ref, tag: node.tagName.toLowerCase(), type: (node.getAttribute('type') || '').slice(0,30),
0040 |             label: label.trim().slice(0,80), disabled: !!node.disabled});
0041 |     }
0042 |     return {text: text.slice(0,textLimit), text_truncated: text.length > textLimit,
0043 |         elements, elements_truncated: candidates.length > elements.length};
0044 | }"""
0045 | 
0046 | 
0047 | class BrowserController:
0048 |     def __init__(self, screenshot_directory):
0049 |         self.screenshot_directory = Path(screenshot_directory)
0050 |         self.playwright = self.browser = self.context = self.page = None
0051 |         self.refs = {}
0052 |         self.screenshots = 0
0053 | 
0054 |     async def _start(self):
0055 |         if self.browser is not None and self.browser.is_connected():
0056 |             return
0057 |         from playwright.async_api import async_playwright
0058 |         self.playwright = await async_playwright().start()
0059 |         try:
0060 |             self.browser = await self.playwright.chromium.launch(headless=True, chromium_sandbox=True, timeout=15000)
0061 |             self.context = await self.browser.new_context(viewport={'width': 1280, 'height': 720},
0062 |                 accept_downloads=False, service_workers='block', permissions=[])
0063 |             self.context.set_default_timeout(5000)
0064 |             self.context.set_default_navigation_timeout(10000)
0065 |             await self.context.route('**/*', self._route)
0066 |             self.page = await self.context.new_page()
0067 |             self.context.on('page', lambda page: asyncio.create_task(page.close()) if page != self.page else None)
0068 |             self.page.on('download', lambda download: asyncio.create_task(download.cancel()))
0069 |         except BaseException:
0070 |             await self.close()
0071 |             raise
0072 | 
0073 |     async def _route(self, route):
0074 |         try:
0075 |             validate_url(route.request.url)
0076 |         except ValueError:
0077 |             await route.abort()
0078 |         else:
0079 |             await route.continue_()
0080 | 
0081 |     def _require_page(self):
0082 |         if self.page is None or self.page.is_closed():
0083 |             raise ValueError('尚未打开页面，请先调用 open_page')
0084 |         return self.page
0085 | 
0086 |     async def open(self, url):
0087 |         validate_url(url)
0088 |         await self._start()
0089 |         self.refs.clear()
0090 |         response = await self.page.goto(url, wait_until='domcontentloaded')
0091 |         result = await self.read()
0092 |         result['http_status'] = response.status if response else None
0093 |         return result
0094 | 
0095 |     async def read(self):
0096 |         page = self._require_page()
0097 |         if page.url != 'about:blank':
0098 |             validate_url(page.url)
0099 |         result = await page.evaluate(SNAPSHOT_SCRIPT, {'prefix': uuid.uuid4().hex[:8],
0100 |             'textLimit': MAX_TEXT, 'elementLimit': MAX_ELEMENTS})
0101 |         self.refs = {item['ref']: dict(item) for item in result['elements']}
0102 |         snapshot = {'ok': True, 'url': page.url[:300], 'url_truncated': len(page.url) > 300,
0103 |                     'title': (await page.title())[:200], **result}
0104 |         # MCP 同时返回正文 JSON 和结构化 JSON，转义字符也计入体积预算。
0105 |         while len(json.dumps(snapshot, ensure_ascii=False)) > 4000:
0106 |             if snapshot['text']:
0107 |                 snapshot['text'] = snapshot['text'][:-200]
0108 |                 snapshot['text_truncated'] = True
0109 |             elif snapshot['elements']:
0110 |                 snapshot['elements'].pop()
0111 |                 snapshot['elements_truncated'] = True
0112 |             else:
0113 |                 break
0114 |         self.refs = {item['ref']: dict(item) for item in snapshot['elements']}
0115 |         return snapshot
0116 | 
0117 |     def _locator(self, ref):
0118 |         self._require_page()
0119 |         if ref not in self.refs:
0120 |             raise ValueError('元素编号不存在或已过期，请重新 read_page 并使用最新 ref')
0121 |         return self.page.locator('[data-ai-cli-ref="' + ref + '"]')
0122 | 
0123 |     async def click(self, ref):
0124 |         locator = self._locator(ref)
0125 |         await locator.click()
0126 |         await self.page.wait_for_load_state('domcontentloaded')
0127 |         return await self.read()
0128 | 
0129 |     async def fill(self, ref, value):
0130 |         if not isinstance(value, str) or len(value) > 4000 or '\x00' in value:
0131 |             raise ValueError('输入内容最多 4000 字符，不允许空字符')
0132 |         locator = self._locator(ref)
0133 |         if await locator.get_attribute('type') in ('file', 'password'):
0134 |             raise ValueError('基础版不支持文件上传或密码输入')
0135 |         await locator.fill(value)
0136 |         return await self.read()
0137 | 
0138 |     async def wait_text(self, text):
0139 |         if not isinstance(text, str) or not text or len(text) > 200:
0140 |             raise ValueError('等待文字必须是 1–200 字符')
0141 |         await self._require_page().get_by_text(text, exact=False).first.wait_for(state='visible', timeout=5000)
0142 |         return await self.read()
0143 | 
0144 |     async def screenshot(self):
0145 |         if self.screenshots >= MAX_SCREENSHOTS:
0146 |             raise ValueError('本次浏览器服务截图达到 32 张上限')
0147 |         raw = await self._require_page().screenshot(type='png', full_page=False, timeout=5000)
0148 |         if len(raw) > 4194304:
0149 |             raise ValueError('截图超过 4 MiB，未保存')
0150 |         directory = self.screenshot_directory
0151 |         if any(path.is_symlink() for path in (directory, *directory.parents)):
0152 |             raise ValueError('截图目录不能含符号链接')
0153 |         directory.mkdir(parents=True, exist_ok=True)
0154 |         path = directory / (uuid.uuid4().hex + '.png')
0155 |         with path.open('xb') as file:
0156 |             file.write(raw)
0157 |         self.screenshots += 1
0158 |         return {'ok': True, 'path': str(path), 'bytes': len(raw), 'message': '截图仅保存为文件，未发送给视觉模型'}
0159 | 
0160 |     async def close(self):
0161 |         browser, playwright = self.browser, self.playwright
0162 |         self.browser = self.playwright = self.context = self.page = None
0163 |         self.refs.clear()
0164 |         try:
0165 |             if browser is not None:
0166 |                 await browser.close()
0167 |         finally:
0168 |             if playwright is not None:
0169 |                 await playwright.stop()
0170 |         return {'ok': True, 'message': '浏览器及临时会话已关闭'}
```
