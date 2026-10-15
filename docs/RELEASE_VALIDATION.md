# 0.2.0 本机验收记录

日期：2026-10-15。环境：WSL/Linux、项目 `.conda-env`、Python 3.12。下述结果来自实际运行：先用固定协议夹具验收客户端流程，再单独使用 DeepSeek 官方 `deepseek-flash` 进行真实联测。没有请求远程 Embedding，也没有运行本地推理。

| 验证 | 实际结果 | 能证明的范围 |
|---|---|---|
| `run_tests` 统一工具入口 | 508 passed、33 skipped，退出码 0 | 在既有 Bubblewrap 只读、禁网沙箱中完成回归；跳过项未算通过 |
| `scripts/live_api_acceptance.py --live` | 最新 7 项全部通过 | DeepSeek 官方 JSON/SSE 工具往返、多文件修复与测试、独立自动审查、PTY、可写子代理和 Web 独立 worker |
| Ruff 静态与格式检查 | 通过 | 语法、未使用符号及项目统一格式；不代替功能验证 |
| `scripts/web_acceptance.py` | 通过 | 浏览器→worker→读取→diff 审批→写入→沙箱测试；刷新、审批重启恢复、去重、Git、任务与诊断 |
| `scripts/writable_agent_acceptance.py` | passed=true | 子代理写入与拒绝、外部冲突、取消授权、会话隔离、PTY 与测试 |
| `scripts/changeset_acceptance.py` | succeeded，测试退出码 0 | 同一次审批前两个文件均未写入；批准后更新代码并新建说明；原测试不变且通过 |
| `scripts/ui_readability_acceptance.py` | 11 项检查通过 | Markdown、危险链接与 HTML 呈现、代码复制、输入法、草稿、会话过滤及流式渲染 |
| `scripts/distribution_acceptance.py` | 通过 | 无网络构建 wheel，在临时虚拟环境中安装；离开源码目录后的 CLI、Web 静态资源、会话 API 和服务脚本 |
| `scripts/update_learning_index.py --check` | 一致 | 离线源码快照与当前 Python 文件匹配 |

最新完整 Python 输出保存在 `artifacts/live/regression.txt`，DeepSeek 原始尝试和最新结果汇总在 `artifacts/live/deepseek.json`。升级前一阶段的 479 项回归输出仍保留在 `artifacts/upgrade/pytest.txt`；安装、多文件变更和界面专项报告分别位于该目录的 `distribution.json`、`changeset.json`、`ui-readability.json`。Web 与可写子代理夹具报告保存在 `artifacts/web/`。

浏览器和任务夹具流程使用本机固定模型协议响应，但实际文件工具、审批、worker 进程和测试沙箱会执行。这类检查不计作真实模型能力。后续 DeepSeek 联测确实由远程模型选择工具，详见 [配置和实测记录](DEEPSEEK.md)。其中的手动批准使用可信测试回调，可写子代理也由限目标测试回调批准；不能描述为真人逐次操作。独立自动审查则实际请求模型，且关闭人工兜底放行。

真实编码用例先观察到沙箱测试 1 failed，再由模型调用 `apply_changes` 修正计算函数并创建说明，最后沙箱测试 1 passed；固定测试文件内容未变。PTY 用例由模型启动终端、输入并等待退出，可写子代理用例通过独立任务审批实际写入，Web 用例启动原生 worker 并在 SQLite 中保存工具结果及协议元数据。

原始报告保留一次子代理验收失败：驱动误读 `done`，而公开状态字段实际为 `state="finished"`。修正验收驱动后重跑通过。汇总取每个用例的最后一次结果，不删除早期失败，也不把跳过和缺失记作通过。18 个进程内 HTTP 请求均收到 200；子进程用量未计量，保留 null，因此不据此报告整个联测的总费用。

流式专项比较连续 token 更新前后的历史 DOM 节点身份，确认没有为每个 token 重建全部历史；同时覆盖重复事件 ID 和最终回复。尚未据此声称特定性能提升百分比。

多文件变更覆盖预检拒绝、审批拒绝、冲突、提交失败补偿和外部再次修改的保留。它不能保证进程强杀后的恢复，也不提供文件系统级跨文件原子可见性。沙箱仍共享宿主内核；服务仍面向本机单用户。

DeepSeek 的上述七项已验证；其他服务和语义 Embedding 联测保持待验证，不能从一个模型推断所有兼容服务。GitHub CI 也未在本轮远端执行。
