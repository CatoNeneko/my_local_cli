# Changelog / 更新记录

## 0.2.0 — 2026-10-15

### 新增与改进

- CLI 与 Web 共用可信用户 TOML、环境变量及启动覆盖；增加离线诊断和配置预览。
- 新增 `apply_changes`：精确替换、多文件合并 diff、整批审批与冲突复核，以及可捕获提交失败后的补偿。
- 可写子代理接入统一 Runtime；文件变更的实际 diff 进入独立任务审批。
- Web 增加 Markdown、代码复制、会话过滤和独立草稿；流式 token 按帧合并更新并去重重复事件。
- 新增标准 wheel 构建、CLI/Web 安装入口；去除子代理启动对源码目录内固定虚拟环境的依赖。
- 提供可重复生成的源码学习导航与版本验收记录。
- 修复 OpenAI 兼容协议对 `reasoning_content` 的保留：覆盖消息规范化、SSE 收集、assistant 消息透传，以及 CLI/Web 保存和上下文预算统计；Web 界面只显示正文。
- 新增 20 个协议字段回归用例、9 个验收报告与失败退出状态用例；完整沙箱回归为 509 passed、33 skipped。
- 修复浏览器配置和 PTY 命令组装测试对本机资源的隐含依赖；用明确夹具覆盖浏览器缓存选择和沙箱准备，不放宽生产边界。

### 验证与边界

- 本机沙箱回归：509 passed、33 skipped。
- 固定协议夹具覆盖 Web、可写子代理、多文件变更、浏览器交互及源码目录外安装运行。
- DeepSeek 官方 API 真实联测最新七项全部通过；验收模型为 `deepseek-flash`。历史记录中的一次 false 来自 driver 读取了错误的状态字段，修正为读取公开状态 `finished` 后复测通过；原始记录保留。其他 provider 与远程语义 Embedding 仍待验证，详见 [DeepSeek 实测记录](docs/DEEPSEEK.md)；远端 CI 记录见 [验收说明](docs/RELEASE_VALIDATION.md)。
- 多文件补偿不保证跨文件原子可见性或进程强杀后的恢复。

### Added and improved

- Shared trusted TOML, environment variables and launch overrides for CLI and Web, with offline diagnostics and configuration inspection.
- Added `apply_changes` for exact text replacements, combined multi-file diffs, batch approval, conflict revalidation and compensation after recoverable commit failures.
- Writable subagents use the shared Runtime and include actual file diffs in independent task approvals.
- Added Markdown rendering, code copying, session filtering and per-session drafts; coalesced streamed tokens by animation frame and ignored duplicate events.
- Added standard wheel builds and installed CLI/Web entry points; subagent startup no longer relies on a fixed virtual environment inside the checkout.
- Added reproducible source-learning navigation and version-specific validation records.
- Fixed preservation of `reasoning_content` in the OpenAI-compatible protocol across message normalization, SSE collection, assistant-message forwarding, CLI/Web persistence, and context-budget accounting; the Web UI displays the message body only.
- Added 20 protocol-field regression cases and 9 cases for acceptance reports and failure exit status; the full sandbox regression reports 509 passed and 33 skipped.
- Removed implicit host-resource dependencies from browser configuration and PTY command-assembly tests using explicit fixtures, without relaxing production boundaries.

### Validation and limitations

- Local sandbox regression: 509 passed, 33 skipped.
- Deterministic protocol fixtures cover the Web workflow, writable subagents, changesets, browser interaction and installation outside the checkout.
- The latest seven live acceptance checks against the official DeepSeek API passed using `deepseek-flash`. One earlier false result was caused by the driver reading the wrong status field; after it was fixed to read the public `finished` state, the check passed on rerun. The original attempt remains in the record. Other providers and remote semantic embeddings remain unverified; see the [DeepSeek live acceptance record](docs/DEEPSEEK.md) and [validation notes](docs/RELEASE_VALIDATION.md) for remote CI history.
- Multi-file compensation does not guarantee atomic visibility across files or recovery after a forced process termination.
