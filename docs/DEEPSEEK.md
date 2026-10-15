# DeepSeek 接入与实测记录

本文记录本项目对 DeepSeek 官方 API 的配置和真实联测范围。验收使用官方 API，并选用 `deepseek-flash`；这不代表其他 provider 或所有模型均已通过验证。

## 配置

项目通过 OpenAI 兼容 Chat Completions 接入 DeepSeek。将以下配置放入可信用户配置文件：

```toml
[model]
provider = "openai"
name = "deepseek-flash"
base_url = "https://api.deepseek.com/v1"
api_key_env = "DEEPSEEK_API_KEY"
stream = true

[runtime]
approval_mode = "manual"
mcp_enabled = false
```

CLI 和 Web 的密钥由 `DEEPSEEK_API_KEY` 环境变量提供。下述独立联测脚本也允许在交互终端中隐藏输入，运行结束后移除脚本自行设置的环境变量；非交互环境必须预先配置变量，不回退到明文输入。不要把密钥写入配置示例、源码或命令参数。

## 真实 API 验收

验收命令：

```bash
.conda-env/bin/python scripts/live_api_acceptance.py --live
```

只有显式提供 `--live` 才会发起真实 API 调用；这些调用可能产生费用。脚本固定请求 DeepSeek 官方地址，父进程最多记录 24 次请求，子代理和 Web worker 另受各自轮次、时间与工具预算控制；24 次不是包含所有子进程的账户总预算。`/models` 实测返回 `deepseek-flash` 和 `deepseek-v4-pro`，本轮验收选用 `deepseek-flash`，没有测试另一个模型。

最新七项工作流结果全部通过：

| 验收项 | 实测结果 |
|---|---|
| JSON 工具调用往返 | 通过 |
| SSE 工具调用往返 | 通过 |
| 真实模型执行 `apply_changes` | 修复 `calc` 并新增 `notes`；原有测试由 1 failed 变为 1 passed，原测试保持不变 |
| 独立 auto reviewer | 返回 allow，无需人工 fallback |
| PTY 任务生命周期 | 真实模型执行 `start_pty`、`task_status`、`task_input`、`task_wait`，进程以退出码 0 结束 |
| 可写子代理 | 子代理实际修改文件，并通过独立任务审批；限目标的可信测试回调提供批准 |
| Web 独立 worker | 模型调用工具读取文件，SQLite 保存工具结果与协议元数据 |

原始记录位于 `artifacts/live/deepseek.json`。其中保留了一次由验收驱动读取错误状态字段造成的 false 结果；修正为读取公开状态 `state="finished"` 后，该项复测通过。此处所列是修正后的最新七项结果，不删除或覆盖早期尝试。报告 `summary` 汇总每项最后一次尝试，脚本仅在七项完整通过时以 0 退出，失败以 1 退出，配置错误以 2 退出。

编码和 PTY 用例中的人工模式批准由可信测试回调提供，实际模型仍自行决定工具及参数。独立 auto reviewer 用例确实请求了另一份独立模型上下文，并将人工兜底设为拒绝，避免用测试回调冒充独立审查成功。

## reasoning 内容保留修复

实测发现 OpenAI 兼容适配器此前会丢弃 `reasoning_content`。现已在消息规范化、SSE 收集和 assistant wire 消息透传中保留该字段；CLI 最终消息回调与 Web 完成阶段会保存它，上下文预算会计入该字段，两个界面仍只显示消息正文。它只是可选协议元数据，不是授权或工具执行指令。修复前的简单 JSON/SSE 往返也成功，因此不能声称本轮观察到了由该问题引起的 HTTP 400。

新增 20 个协议字段回归用例、9 个验收报告及退出状态用例；本轮完整沙箱回归为 **508 passed、33 skipped**，记录见 `artifacts/live/regression.txt`。

## 用量与验证边界

本轮 18 个父进程内请求具有实测 usage 字段，均返回 HTTP 200，小计 17,993 输入、1,830 输出、19,823 total tokens。这只是经过记录器的请求小计，早期预探针不包含在内；worker 子进程的 usage 缺失保持为 `null`。缺失不能按零计算，因此本文不报告整个联测的总 token 数或总费用。

默认审批仍为人工模式，MCP 默认关闭，本地推理未启用。远程语义 Embedding 尚未实测，其他 provider 兼容性尚未全部验证，GitHub CI 本轮未执行。固定协议夹具验收和本页记录的真实 API 调用是两类独立证据，夹具结果不计作真实模型调用。

## 官方资料

- [DeepSeek API 文档](https://api-docs.deepseek.com/)
- [DeepSeek 思考模式指南](https://api-docs.deepseek.com/guides/thinking_mode/)
