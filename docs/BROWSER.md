# 基础无头浏览器

浏览器作为独立 stdio MCP 服务接入已有工具循环：

```text
用户任务 → 模型选择工具 → tool_runtime 参数与权限检查
                         → mcp_manager 常驻连接
                         → browser_server → BrowserController → Playwright → Chromium
                         ← 页面正文、元素编号或截图路径
```

没有增加第二套代理循环。Playwright 是控制浏览器的 Python 库；BrowserContext 是临时 Cookie、缓存等会话的容器；ref 是当前页面快照给元素分配的编号。模型根据正文与编号操作，不直接编写浏览器脚本。每次读取或操作返回新的编号，下一次操作使用最新结果中的 ref。

## 安装与启动

Python 依赖安装在 `.conda-env`，Chromium 安装在助手目录的 `.browser-runtime`。当前机器已安装并验证。迁移到其他机器后，在助手安装目录运行：

```bash
.conda-env/bin/python -m pip install -r requirements.txt
PLAYWRIGHT_BROWSERS_PATH="$PWD/.browser-runtime" .conda-env/bin/python -m playwright install chromium --only-shell
./ai-cli
```

若启动提示缺少 Linux 系统库，按 Playwright 的系统依赖说明处理；系统库属于操作系统，不属于虚拟环境。当前机器无需额外安装系统库。浏览器启动启用 Chromium 自身的 sandbox，启动失败不会降级为关闭 sandbox。

启动时批准 browser MCP 服务即可向模型提供七种工具；首次打开网页时才启动 Chromium。`--no-mcp` 同时禁用浏览器。配置位于助手 `config.py` 的 `mcp_config["browser"]`。

## 操作

可以直接告诉模型：

```text
打开 http://127.0.0.1:8000，读取页面。找到搜索框，填写 Python，点击搜索，然后读取结果并保存截图。
```

也可以手动操作：

```text
/browser open http://127.0.0.1:8000
/browser read
/browser fill <最新输入框 ref> Ada
/browser click <最新按钮 ref>
/browser wait Hello Ada
/browser screenshot
/browser close
```

`open` 返回 HTTP 状态，404 页面也会被读取，不代表业务成功。点击后若网站异步更新，用 `wait` 等待文字或再次 `read`。超时后应核实页面状态，动作可能已经发生。

对应工具为 `mcp__browser__open_page/read_page/click/fill/wait_text/screenshot/close_browser`。截图保存于选定项目的 `.ai-cli/.browser-artifacts`；在助手源码目录运行时使用 `.browser-artifacts`。截图返回文件路径，目前不发送给视觉模型。

## 实际范围

一个浏览器、一个临时上下文、一个页面；弹出新窗口自动关闭。读取最多 2000 字符正文及 15 个可见交互元素，并进一步控制序列化体积，超限标明截断。候选元素只扫描前 200 个，暂不提供分页、iframe、Shadow DOM、滚动、多标签页或完整可访问性树。并非所有网站都适用。

仅允许无嵌入用户名密码的 HTTP(S) 地址，包括本地开发服务器。不提供任意 JavaScript 执行、密码输入、文件上传或下载接口。填写最多 4000 字符。每次服务最多保存 32 张视口 PNG，每张最多 4 MiB，不覆盖现有文件。

浏览器可以联网，MCP 服务以当前用户身份运行，**不属于 pytest 的 bubblewrap 禁网沙箱**。它也没有按站点隔离网络权限，本地地址允许访问。页面内容是外部数据，不构成权限授权；MCP 操作仍通过现有人工确认，包括自动审批模式。批准访问页面也意味着加载其资源和执行其脚本，临时会话不代表整个操作系统被隔离。

关闭浏览器后 Cookie 会话清除，下次打开创建新上下文；正常退出 CLI 关闭 MCP 服务和浏览器。异常终止不等于已经发生的网页动作被撤销。

## 验证

```bash
CLI_BROWSER_INTEGRATION=1 PYTHONDONTWRITEBYTECODE=1 .conda-env/bin/python -m pytest -q -p no:cacheprovider tests/test_browser.py
```

测试使用本地网页，真实执行打开、填写、点击、等待、PNG 截图与 Cookie 重置；还验证 MCP 注册、权限拒绝、错误结果、过期编号、密码和上传拒绝。没有访问外部账号或执行真实站点交易。模型能否正确规划网站操作仍取决于模型，另已使用本机 qwen3.8-27b-mtp:latest 完成真实模型浏览验收：模型依次调用 open_page、fill、click、read_page、screenshot，九项证据检查全部通过。仅覆盖固定本地网页，不代表任意网站任务都能通过。

实现参考：[Playwright Python 安装说明](https://playwright.dev/python/docs/intro)、[定位器与自动等待](https://playwright.dev/python/docs/locators)。

真实模型验收可复现命令：

```bash
PYTHONDONTWRITEBYTECODE=1 .conda-env/bin/python scripts/browser_acceptance.py
```

该脚本创建随机端口本地网页和临时项目，测试中仅预先授权该网页的 browser MCP 操作，不改变日常 CLI 确认策略。报告保存到 `artifacts/browser/real_acceptance.json`，包含真实工具结果、随机问候核对和 PNG 文件验证。
