# 工作台评估

从仓库根目录运行固定离线集：

```bash
.conda-env/bin/python scripts/evaluate_workbench.py
```

默认不调用模型或 embedding 服务。它在临时 workspace 中使用 `KnowledgeStore` 的确定性 `HashTokenEmbeddings`，并通过统一 `tool_runtime.execute_tool` 检查读取边界、参数校验和人工拒绝写入。报告默认写到 `artifacts/evaluation/report.json`；可用 `--report PATH` 指定其他位置。

固定离线集包含中英文 RAG 来源命中、删除文件后重建索引、项目记忆隔离、缺少必需工具参数拒绝、越界读取拒绝、读取指令诱导内容仍按数据处理，以及可信确认回调拒绝写入后文件保持原样。读写权限测试只针对临时 workspace；确认拒绝由本地测试回调模拟。

报告的 `counts` 是这组固定检查的通过、失败和缺失项数量，`checks` 保留每项名称与状态。它们说明当前实现是否满足这些少量断言，不能解释为大样本成功率、真实模型质量、生产安全保证或用户任务完成率。`missing_configuration` 中的项不能当成通过。

只有显式加 `--live` 才会尝试远程探针：

```bash
AI_CLI_MODEL=your-compatible-model \
AI_CLI_BASE_URL=https://provider.example/v1 \
AI_CLI_API_KEY_ENV=OPENAI_API_KEY \
.conda-env/bin/python scripts/evaluate_workbench.py --live
```

密钥只从 `AI_CLI_API_KEY_ENV` 指定的单个进程环境变量读取；默认变量名是 `OPENAI_API_KEY`。脚本不加载 `.env`、不扫描其他变量，也不会把密钥写入报告。探针强制使用 `model_client` 的 OpenAI 兼容 provider，仅声明 `read_file` 工具：第一次远程请求必须真实返回固定夹具读取调用，Runtime 的实际工具结果再进入第二次请求。模型没有发出符合预期的工具调用时，该项记为失败，脚本不会伪造 tool result。

拒绝 loopback、私有 IP、localhost、11434，以及 Ollama、Qwen、GLM 相关模型和端点。远程 embedding 只有设置 `AI_CLI_EMBEDDING_MODEL` 才会通过 `KnowledgeStore` 的环境配置运行；否则报告将其列为缺失，不能算通过。探针若失败只报告错误类型，不保存服务响应或凭据。

初始阶段固定离线集和远程探针代码已实现，当时只运行本地离线检查，没有调用真实模型或远程 embedding。历史 GLM 请求未通过；后续已完成的 DeepSeek 官方联测单独列在本文末尾，不能把不同阶段的证据混用。

## 本机浏览器与后台任务验收

`scripts/web_acceptance.py` 启动确定性 localhost 协议夹具、实际 Web 服务和 Chromium，验证文件审批、沙箱测试、刷新、重启后审批、Git 单文件恢复，以及 PTY 在审批暂停和后续请求中的存活、输入、取消及会话隔离。模拟 HTTP 503 用于验证结构化错误和敏感响应正文不进入诊断。报告写到 `artifacts/web/acceptance.json`，截图同目录保存。

这些检查实际执行服务、进程和工具，模型输出由固定夹具提供。不能把它们描述为真实模型任务成功率。服务重启恢复的是暂停审批和已存结果；已终止的后台进程不会复活。

`scripts/task_agent_acceptance.py` 单独验证真实子代理进程：读取文件、暂存建议、创建它的运行结束后继续完成、后续运行取回建议、其他会话被拒绝、原 Runtime 展示 diff 并经可信人工确认测试回调应用、重复应用被拒绝。报告写到 `artifacts/web/task-agent-acceptance.json`。该脚本同样只调用本机固定协议夹具。

`scripts/writable_agent_acceptance.py` 验证开发子代理真正修改文件并运行沙箱测试、PTY 交互，以及拒绝保持原文、外部文件冲突不覆盖、取消后审批失效和跨会话审批拒绝。`scripts/web_acceptance.py` 还验证模型协议夹具自己调用任务发现、启动、输入、等待，以及主运行结束后的子代理任务卡片 diff 审批。报告分别在 `artifacts/web/writable-agent-acceptance.json` 和 `artifacts/web/acceptance.json`。这些是本机确定性联测，不是实际模型成功率。

2026-10-14 用户单独授权 MUST OpenHub `glm-4.7-flash` 联测。`scripts/glm_api_probe.py` 由该机器既有 WSL gateway 的无参数 `project_api_probe` 入口调用，共享串行锁，凭据只从用户拥有的 0600 文件读取。最多四次、每次输出上限 1024 token，只在临时项目声明 `read_file`，计划验证非流式和 SSE 工具结果往返；不恢复 GLM 代码委派。其他入口的默认 GLM 禁用规则未解除。

此次实际只尝试了第一条非流式请求，30 秒超时，没有收到 HTTP 状态、工具调用或用量；报告 `artifacts/evaluation/glm-api-probe.json` 为失败，用量字段为 null。没有自动重试，不能宣称 GLM 工具调用或真实模型任务流程已验证。这个联测入口依赖本机 gateway 安装，不是分发包的通用凭据管理功能。

## DeepSeek 官方真实联测（2026-10-15）

用户另行提供凭据并确认 DeepSeek 官方服务后，使用 `scripts/live_api_acceptance.py --live` 验证 `deepseek-flash`。最新七项结果全部通过：非流式和 SSE 工具往返、多文件修复与沙箱测试、独立自动审查、模型操作 PTY、可写子代理，以及 Web 独立 worker 读取与持久历史。配置、各项断言和验证边界见 [DeepSeek 接入与实测记录](DEEPSEEK.md)。没有恢复 GLM 委派或本地推理。

报告 `artifacts/live/deepseek.json` 保留全部尝试，`summary` 按每个用例最后一次尝试判断完整性；任何必需项缺失或失败都不会得到整体 passed。早期子代理 false 来自验收驱动误读状态字段，修正后复测通过；该记录保留。脚本只有完整通过才以 0 退出，失败以 1 退出；配置参数错误以 2 退出。`tests/test_live_api_acceptance.py` 用离线数据验证这些汇总和失败路径。

记录器仅采集父进程中实际经过包装器的 HTTP 状态和服务返回的 usage；没有保存请求正文、密钥或模型推理正文。子代理及 Web 原生子进程不经过该包装器，用量为 null；预探针也不包含在这组统计中，不能把记录器中 18 次请求的 token 小计解释为整个联测总用量。手动批准由可信测试回调提供，与真实模型的独立审查分开记录。

此轮不测试语义 Embedding、其他 provider 或长周期真实仓库任务，不能报告大样本任务成功率或生产安全保证。原始 API 字段丢失已修复并补充回归，最新完整沙箱结果为 509 passed、33 skipped。
