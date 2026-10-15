# 09：逐文件源码导读索引

`source/` 下的逐文件说明和行号源码是较早教程留下的历史快照，可能包含旧路径和旧行为。本表与 [离线源码导航](index.html) 可由 `scripts/update_learning_index.py` 按当前源码刷新；链接指向实际源码。升级内容见 [0.2.0 升级指南](../PRODUCT_UPGRADE.md)。静态调用只是 AST 中的调用表达式，不是完整运行时调用图。

| 文件 | 行数 | 函数/方法/嵌套回调数 | 职责 |
| --- | ---: | ---: | --- |
| [agent.py](../../agent.py) | 117 | 2 | 主模型工具循环：按轮次请求、顺序执行、保存完整调用链。不是并行子代理调度器。 |
| [agent_proposals.py](../../agent_proposals.py) | 134 | 4 | 可选的子代理编辑/新建建议路径；不是 worker 修改文件的唯一途径。 |
| [api_adapter.py](../../api_adapter.py) | 159 | 3 | OpenAI 兼容 Chat Completions；内部消息仍统一使用字典参数。 |
| [approval.py](../../approval.py) | 242 | 8 | 可信审批控制器：硬规则先执行，模型只提供受限的风险判断。 |
| [attachments.py](../../attachments.py) | 45 | 1 | 先完整读取并验证一批附件，再一次保存；失败不添加部分附件。 |
| [audit.py](../../audit.py) | 28 | 1 | 记录工具事件摘要；不保存完整diff，但聊天记录可包含完整工具内容。 |
| [browser_runtime.py](../../browser_runtime.py) | 207 | 13 | 单页面、临时上下文的浏览器执行器；不暴露任意 JS、Shell 或文件路径。 |
| [cli.py](../../cli.py) | 102 | 3 | 命令行启动入口；先解析参数，因此 --help 不连接模型或启动 MCP。 |
| [command_help.py](../../command_help.py) | 56 | 1 | 帮助和命令补全共用的命令说明。 |
| [compaction.py](../../compaction.py) | 257 | 8 | 有界会话摘要；检查点追加到原 JSONL，不覆盖原始消息。 |
| [config.py](../../config.py) | 93 | 0 | 模型、预算、权限、沙箱、MCP、Hook与审批配置字典；不保存真实API密钥。 |
| [console_output.py](../../console_output.py) | 27 | 5 | 终端输出状态：每轮响应重置，避免流式显示后重复打印最终文字。 |
| [context_window.py](../../context_window.py) | 121 | 4 | 构造有界请求上下文；磁盘历史不裁剪，工具链按用户轮次保留。 |
| [file_catalog.py](../../file_catalog.py) | 87 | 3 | 有限扫描的项目文件索引与文件名模糊匹配，不读取文件正文。 |
| [file_picker.py](../../file_picker.py) | 121 | 10 | 可筛选、多选的附件面板；选中状态跨筛选保留。 |
| [file_tools.py](../../file_tools.py) | 75 | 3 | 列目录、有限UTF-8读取、单文件字面搜索。 |
| [harness/__init__.py](../../harness/__init__.py) | 1 | 0 | 编程助手的共享基础层；CLI 与 Web 使用同一套任务能力。 |
| [harness/configuration.py](../../harness/configuration.py) | 173 | 6 | CLI 与 Web 共用的可信启动配置；不读取工作区内的项目配置。 |
| [harness/diagnostics.py](../../harness/diagnostics.py) | 116 | 1 | 只读检查 CLI 运行环境，不启动服务或执行外部命令。 |
| [harness/files/__init__.py](../../harness/files/__init__.py) | 1 | 0 | 文件变更应用服务；提交只能由可信 Runtime 调用。 |
| [harness/files/changesets.py](../../harness/files/changesets.py) | 214 | 6 | 有界多文件变更：整批预检、一次审阅、冲突复核和失败补偿。 |
| [harness/infrastructure/__init__.py](../../harness/infrastructure/__init__.py) | 1 | 0 | 与模型和交互界面无关的基础设施。 |
| [harness/infrastructure/workspace_locks.py](../../harness/infrastructure/workspace_locks.py) | 28 | 1 | 规范化工作区的跨进程写锁；只在 Runtime 最终提交阶段使用。 |
| [harness/tasks/__init__.py](../../harness/tasks/__init__.py) | 1 | 0 | 任务应用服务、进程驱动与持久审批；不依赖 Web 编排。 |
| [harness/tasks/approvals.py](../../harness/tasks/approvals.py) | 321 | 18 | TaskApprovalStore 持久化待处理审批，并验证身份、解决决定和一次性消费。 |
| [harness/tasks/processes.py](../../harness/tasks/processes.py) | 259 | 10 | 纯标准库进程驱动；维护 JOBS、启动任务、采集输出并回收进程。 |
| [harness/tasks/runtime.py](../../harness/tasks/runtime.py) | 187 | 13 | 任务应用 API；通过 TASK_BACKEND 调用会话后端，或委托本地进程驱动。 |
| [history.py](../../history.py) | 64 | 4 | JSONL逐行恢复与追加；基本记录验证，链完整性由上下文模块检查。 |
| [hooks.py](../../hooks.py) | 49 | 3 | 可信本地 Hook：执行前可拒绝，执行后失败只附加警告，不伪装回滚。 |
| [mcp_client.py](../../mcp_client.py) | 100 | 4 | MCP 协议操作：连接参数、握手、发现工具和执行调用。 |
| [mcp_manager.py](../../mcp_manager.py) | 194 | 15 | CLI 运行期间持有 MCP 连接；同步主循环通过 portal 请求异步操作。 |
| [mcp_servers/browser_server.py](../../mcp_servers/browser_server.py) | 86 | 9 | 基础浏览器 stdio MCP；启动仅发现工具，首次 open_page 才创建 Chromium。 |
| [mcp_servers/demo_server.py](../../mcp_servers/demo_server.py) | 15 | 1 | 示例 stdio MCP 服务，提供可发现、可调用的加法工具。 |
| [mcp_tools.py](../../mcp_tools.py) | 78 | 4 | 将 MCP 声明转换为统一工具注册项，不负责启动权限。 |
| [model_client.py](../../model_client.py) | 92 | 2 | 唯一模型请求接口 request_message；上下文、协议选择、有限响应与回调。 |
| [new_files.py](../../new_files.py) | 87 | 3 | 普通 UTF-8 文件的新建：审查后创建，已有目标一律拒绝覆盖。 |
| [patches.py](../../patches.py) | 108 | 5 | 全文件内容比较成diff，获准后检查冲突并原子替换。 |
| [path_input.py](../../path_input.py) | 57 | 2 | 路径命令解析和受项目边界约束的文件候选。 |
| [permissions.py](../../permissions.py) | 114 | 7 | 共享路径边界与授权策略；模型参数不能改变策略或调用来源。 |
| [project_instructions.py](../../project_instructions.py) | 53 | 2 | 启动时加载根目录项目规则；请求时注入，不写入聊天历史。 |
| [project_search.py](../../project_search.py) | 141 | 3 | 项目递归文字搜索：共享路径策略，跳过符号链接并限制读取和结果规模。 |
| [sandbox.py](../../sandbox.py) | 297 | 8 | Linux bubblewrap 中的只读项目测试执行器，不提供宿主回退。 |
| [script.py](../../script.py) | 518 | 4 | 实际交互命令循环与会话协调；命令分支continue，自然语言进入agent。 |
| [scripts/acceptance.py](../../scripts/acceptance.py) | 272 | 7 | 准备独立验收项目，检查真实 CLI 历史并保存证据；不模拟模型回复。 |
| [scripts/approval_acceptance.py](../../scripts/approval_acceptance.py) | 70 | 0 | 真实子代理暂存建议与父进程独立自动审批的固定验收。 |
| [scripts/browser_acceptance.py](../../scripts/browser_acceptance.py) | 121 | 4 | 真实模型通过统一工具循环操作固定本地网页；只授权该网页的浏览器工具。 |
| [scripts/compaction_acceptance.py](../../scripts/compaction_acceptance.py) | 101 | 3 | 固定示例历史的真实模型摘要、恢复与自动触发验证；不会调用文件修改工具。 |
| [scripts/package_project.py](../../scripts/package_project.py) | 92 | 2 | 生成供上传的源码包；使用显式目录与文件清单，不包含本机历史、凭据或环境。 |
| [scripts/update_learning_index.py](../../scripts/update_learning_index.py) | 322 | 23 | 从当前 Python 源码刷新离线导航与逐文件索引。 |
| [sessions.py](../../sessions.py) | 118 | 6 | 会话管理；文件路径由名称生成，独立于模型文件工具的访问入口。 |
| [skill_files.py](../../skill_files.py) | 77 | 3 | 新建 Skill 文件：审查后独占创建，不覆盖已有文件。 |
| [skill_generation.py](../../skill_generation.py) | 47 | 1 | 模型生成 Skill 草稿，交给统一写入入口确认并保存。 |
| [skills.py](../../skills.py) | 91 | 5 | 项目内 Skill 的发现、手动启用和停用；不执行文件中的命令。 |
| [streaming.py](../../streaming.py) | 80 | 3 | Ollama NDJSON 响应收集；结束标记到达前不返回可执行工具调用。 |
| [subagent_worker.py](../../subagent_worker.py) | 156 | 2 | 独立开发 worker，可经共享 Runtime 读写、测试和启动 PTY；无父聊天、MCP 或嵌套子代理。 |
| [terminal_dialog.py](../../terminal_dialog.py) | 76 | 8 | 轻量选择面板：上下移动，Enter 确认，Esc 取消。 |
| [terminal_input.py](../../terminal_input.py) | 209 | 12 | 终端输入适配：TTY 使用补全和多行编辑，管道或 --plain 使用 input。 |
| [tool_display.py](../../tool_display.py) | 73 | 6 | 工具状态与修改审查的终端展示；不改变工具结果或授权。 |
| [tool_registry.py](../../tool_registry.py) | 284 | 3 | 工具参数、权限类型、准备函数和实现的唯一注册位置。 |
| [tool_runtime.py](../../tool_runtime.py) | 188 | 4 | 所有模型工具的共享执行入口：验证、授权、执行、规范结果和记录。 |
| [tools.py](../../tools.py) | 21 | 4 | 用户文件工具的便利接口，所有操作复用统一 Runtime。 |
| [web/__init__.py](../../web/__init__.py) | 1 | 0 | Web 工作台；每个 Agent 运行使用独立进程复用 CLI 的执行边界。 |
| [web/__main__.py](../../web/__main__.py) | 37 | 1 | 启动本地工作台：python -m web。 |
| [web/app.py](../../web/app.py) | 464 | 43 | 本机 Web API；同源写入、允许目录、进程隔离。不是公网多租户服务。 |
| [web/diagnostics.py](../../web/diagnostics.py) | 289 | 10 | 为 Web 工作台提供不泄漏异常内容的诊断信息和有界 JSONL 日志。 |
| [web/git_changes.py](../../web/git_changes.py) | 897 | 24 | 只读 Git 状态、任务前文本快照与单文件安全恢复。 |
| [web/guardrails.py](../../web/guardrails.py) | 79 | 4 | 四层护栏。启发式标记不等于注入检测保证，授权仍由 Runtime 决定。 |
| [web/knowledge.py](../../web/knowledge.py) | 953 | 32 | 基于 SQLite 的本地 RAG 索引与显式长期记忆。 |
| [web/prompts.py](../../web/prompts.py) | 44 | 2 | 版本化提示与有界检索上下文。资料不会作为 system 授权注入。 |
| [web/recovery.py](../../web/recovery.py) | 128 | 11 | 副作用日志：完成的不重放，状态不明的调用不假定未发生。 |
| [web/runner.py](../../web/runner.py) | 314 | 13 | 有界调度器。任务状态持久化，运行进程不共享 CLI 全局状态。 |
| [web/settings.py](../../web/settings.py) | 75 | 5 | 服务配置仅来自启动环境，不接受浏览器提交模型地址、密钥或命令。 |
| [web/store.py](../../web/store.py) | 429 | 27 | SQLite-backed persistence for the local web interface. |
| [web/task_host.py](../../web/task_host.py) | 427 | 11 | 服务级任务 supervisor。只接受可信本机 RPC，项目和会话归属由数据库决定。 |
| [web/task_service.py](../../web/task_service.py) | 606 | 32 | Parent-side client for the isolated task supervisor. |
| [web/worker.py](../../web/worker.py) | 192 | 5 | 可信 worker：独立进程绑定 workspace，用 stdout JSONL 传递事件，stdin 接收审批。 |
| [web/workflow.py](../../web/workflow.py) | 197 | 6 | LangGraph 控制模型与工具循环；副作用仍由原 Runtime 执行。 |
| [workspace.py](../../workspace.py) | 57 | 1 | 一次 CLI 运行的项目路径绑定，与助手安装目录和运行环境分开。 |
共 **78** 个当前 Python 源码文件、**523** 个函数/方法/嵌套回调定义。排除测试、环境、构建和验收产物；下列测试另列索引。函数位置、签名、静态调用与源码快照由 AST 从当前文件提取。

## 非Python文件与目录

| 文件/目录 | 用途 |
| --- | --- |
| ai-cli | Bash启动器：固定安装环境，透传argv；详细读法见启动章 |
| requirements.txt / environment.yml | pip依赖版本与Mamba环境声明 |
| .gitignore | 排除环境、密钥、历史、截图与产物；不是工具访问策略 |
| .github/workflows/tests.yml | push/PR触发Ubuntu普通pytest，无本机模型集成 |
| AGENTS.md | 根项目开发规则，启动加载 |
| skills/code-review/SKILL.md | 本机已有的项目内Skill示例；当前源码白名单不自动发布本机skills目录 |
| examples/acceptance_seed | 折扣任务种子，.py.txt在prepare复制时去.txt，不污染pytest收集 |
| examples/acceptance_verify | 独立验收测试模板 |
| artifacts | 本机验收证据与ZIP，未上传GitHub |
| .conda-env / .browser-runtime | 环境与浏览器二进制，未上传 |
| .ai-cli / sessions / history.jsonl / tool_events.jsonl | 私有运行状态，不是源码，不上传 |

## 测试函数索引

以下为现有测试的实际定义；fixture/helper也列出，用于定位准备逻辑。函数名只是索引，真实断言仍在.py中。

### test_acceptance_checks.py

源码：[test_acceptance_checks.py](../../tests/test_acceptance_checks.py)。

| 行 | 定义 |
| ---: | --- |
| 6 | [save_history](../../tests/test_acceptance_checks.py#L6) |
| 20 | [workflow](../../tests/test_acceptance_checks.py#L20) |
| 29 | [test_claimed_success_without_tools_does_not_pass](../../tests/test_acceptance_checks.py#L29) |
| 37 | [test_real_result_sequence_passes_workflow_checks](../../tests/test_acceptance_checks.py#L37) |
| 43 | [test_failure_after_write_does_not_meet_initial_failure_criterion](../../tests/test_acceptance_checks.py#L43) |
| 50 | [test_wrong_new_file_does_not_meet_required_file_criterion](../../tests/test_acceptance_checks.py#L50) |
| 57 | [test_unfinished_tool_chain_is_not_accepted](../../tests/test_acceptance_checks.py#L57) |

### test_agent_history.py

源码：[test_agent_history.py](../../tests/test_agent_history.py)。

| 行 | 定义 |
| ---: | --- |
| 15 | [conversation](../../tests/test_agent_history.py#L15) |
| 23 | [tool_request](../../tests/test_agent_history.py#L23) |
| 30 | [test_tool_content_survives_followup_and_reload](../../tests/test_agent_history.py#L30) |
| 33 | [test_tool_content_survives_followup_and_reload.respond](../../tests/test_agent_history.py#L33) |
| 47 | [test_tool_content_survives_followup_and_reload.answer](../../tests/test_agent_history.py#L47) |
| 54 | [test_denial_is_persisted](../../tests/test_agent_history.py#L54) |
| 63 | [test_malformed_batch_never_partially_executes](../../tests/test_agent_history.py#L63) |
| 75 | [test_budget_preserves_complete_results](../../tests/test_agent_history.py#L75) |
| 86 | [test_exception_result_is_persisted](../../tests/test_agent_history.py#L86) |
| 95 | [test_plain_reply_is_not_saved_twice](../../tests/test_agent_history.py#L95) |
| 102 | [test_tool_history_validation](../../tests/test_agent_history.py#L102) |

### test_agent_proposals.py

源码：[test_agent_proposals.py](../../tests/test_agent_proposals.py)。

| 行 | 定义 |
| ---: | --- |
| 17 | [project](../../tests/test_agent_proposals.py#L17) |
| 30 | [job](../../tests/test_agent_proposals.py#L30) |
| 36 | [test_child_proposal_does_not_write_then_parent_reviews_original_task](../../tests/test_agent_proposals.py#L36) |
| 50 | [test_file_changed_since_child_proposal_is_preserved_before_review](../../tests/test_agent_proposals.py#L50) |
| 60 | [test_child_cannot_escape_or_choose_execution_tool](../../tests/test_agent_proposals.py#L60) |
| 73 | [test_review_denies_child_change_without_writing](../../tests/test_agent_proposals.py#L73) |
| 82 | [test_failed_or_foreign_child_result_cannot_apply](../../tests/test_agent_proposals.py#L82) |
| 95 | [test_proposal_limits](../../tests/test_agent_proposals.py#L95) |

### test_api_adapter.py

源码：[test_api_adapter.py](../../tests/test_api_adapter.py)。

| 行 | 定义 |
| ---: | --- |
| 8 | [event](../../tests/test_api_adapter.py#L8) |
| 12 | [test_fragmented_calls_and_history_ids](../../tests/test_api_adapter.py#L12) |
| 24 | [test_incomplete_stream_never_returns_calls](../../tests/test_api_adapter.py#L24) |
| 30 | [test_old_ollama_history_gets_matching_ids](../../tests/test_api_adapter.py#L30) |
| 36 | [test_malformed_arguments](../../tests/test_api_adapter.py#L36) |
| 41 | [test_authenticated_request_uses_env_and_no_redirect](../../tests/test_api_adapter.py#L41) |

### test_approval.py

源码：[test_approval.py](../../tests/test_approval.py)。

| 行 | 定义 |
| ---: | --- |
| 18 | [project](../../tests/test_approval.py#L18) |
| 29 | [edit](../../tests/test_approval.py#L29) |
| 34 | [test_independent_review_has_no_tools_rules_or_history_and_binds_diff](../../tests/test_approval.py#L34) |
| 58 | [test_invalid_or_uncertain_review_requires_human_and_preserves_file](../../tests/test_approval.py#L58) |
| 66 | [test_review_failure_can_be_approved_manually_without_leaking_exception](../../tests/test_approval.py#L66) |
| 76 | [test_review_denial_is_not_auto_overridden](../../tests/test_approval.py#L76) |
| 86 | [test_control_files_require_human_without_model_review](../../tests/test_approval.py#L86) |
| 95 | [test_missing_task_and_large_diff_do_not_auto_approve](../../tests/test_approval.py#L95) |
| 104 | [test_hard_boundaries_and_invalid_arguments_precede_review](../../tests/test_approval.py#L104) |
| 114 | [test_client_control_cannot_be_rewritten_even_in_manual_mode](../../tests/test_approval.py#L114) |
| 124 | [test_approved_diff_still_rechecks_conflicts](../../tests/test_approval.py#L124) |
| 126 | [test_approved_diff_still_rechecks_conflicts.conflict](../../tests/test_approval.py#L126) |
| 134 | [test_hook_veto_precedes_auto_approval](../../tests/test_approval.py#L134) |
| 142 | [test_manual_mode_never_calls_reviewer](../../tests/test_approval.py#L142) |
| 150 | [test_readonly_sandbox_preflight_required_and_no_host_fallback](../../tests/test_approval.py#L150) |
| 161 | [test_approval_log_contains_reason_and_hash_without_diff](../../tests/test_approval.py#L161) |
| 171 | [test_real_sandbox_auto_approval_without_confirmation](../../tests/test_approval.py#L171) |

### test_browser.py

源码：[test_browser.py](../../tests/test_browser.py)。

| 行 | 定义 |
| ---: | --- |
| 20 | [test_bad_browser_url_rejected](../../tests/test_browser.py#L20) |
| 26 | [test_http_and_local_url_allowed](../../tests/test_browser.py#L26) |
| 30 | [test_invalid_url_never_starts_browser](../../tests/test_browser.py#L30) |
| 38 | [test_screenshot_directory_is_bound_to_workspace_and_runtime_is_private](../../tests/test_browser.py#L38) |
| 50 | [test_password_and_upload_are_rejected_before_fill](../../tests/test_browser.py#L50) |
| 51 | [test_password_and_upload_are_rejected_before_fill.check](../../tests/test_browser.py#L51) |
| 63 | [test_screenshot_symlink_refused_without_writing](../../tests/test_browser.py#L63) |
| 74 | [test_browser_close_clears_refs_and_can_be_repeated](../../tests/test_browser.py#L74) |
| 75 | [test_browser_close_clears_refs_and_can_be_repeated.check](../../tests/test_browser.py#L75) |
| 89 | [website](../../tests/test_browser.py#L89) |
| 98 | [website.Handler.log_message](../../tests/test_browser.py#L98) |
| 99 | [website.Handler.do_GET](../../tests/test_browser.py#L99) |
| 117 | [test_real_browser_fill_click_wait_screenshot_and_ephemeral_session](../../tests/test_browser.py#L117) |
| 119 | [test_real_browser_fill_click_wait_screenshot_and_ephemeral_session.check](../../tests/test_browser.py#L119) |
| 148 | [test_real_browser_mcp_uses_permissions_and_reports_errors](../../tests/test_browser.py#L148) |
| 179 | [test_snapshot_budget_counts_json_escaping_and_keeps_only_returned_refs](../../tests/test_browser.py#L179) |
| 180 | [test_snapshot_budget_counts_json_escaping_and_keeps_only_returned_refs.check](../../tests/test_browser.py#L180) |

### test_cancellation.py

源码：[test_cancellation.py](../../tests/test_cancellation.py)。

| 行 | 定义 |
| ---: | --- |
| 20 | [test_runtime_interrupt_returns_cancelled_and_audits_once](../../tests/test_cancellation.py#L20) |
| 31 | [test_agent_cancellation_stops_batch_and_preserves_complete_chain](../../tests/test_cancellation.py#L31) |
| 51 | [test_skill_generation_cancellation_returns_result](../../tests/test_cancellation.py#L51) |
| 60 | [test_sigint_cancels_and_reaps_test_process](../../tests/test_cancellation.py#L60) |

### test_compaction.py

源码：[test_compaction.py](../../tests/test_compaction.py)。

| 行 | 定义 |
| ---: | --- |
| 18 | [project](../../tests/test_compaction.py#L18) |
| 31 | [turns](../../tests/test_compaction.py#L31) |
| 39 | [stored_messages](../../tests/test_compaction.py#L39) |
| 45 | [test_manual_checkpoint_preserves_raw_history_and_recent_turns](../../tests/test_compaction.py#L45) |
| 65 | [test_restart_rename_switch_and_clear_preserve_session_independence](../../tests/test_compaction.py#L65) |
| 83 | [test_recompression_uses_previous_summary_and_new_old_messages_only](../../tests/test_compaction.py#L83) |
| 98 | [test_bad_summary_never_changes_history_or_memory](../../tests/test_compaction.py#L98) |
| 109 | [test_failed_or_cancelled_summary_keeps_history](../../tests/test_compaction.py#L109) |
| 120 | [test_history_changed_during_summary_is_not_overwritten](../../tests/test_compaction.py#L120) |
| 123 | [test_history_changed_during_summary_is_not_overwritten.change](../../tests/test_compaction.py#L123) |
| 132 | [test_changed_history_invalidates_prefix_digest](../../tests/test_compaction.py#L132) |
| 141 | [test_auto_compaction_trigger_and_off_setting](../../tests/test_compaction.py#L141) |
| 156 | [test_auto_threshold_uses_full_request_before_old_turns_are_dropped](../../tests/test_compaction.py#L156) |
| 164 | [test_auto_failure_not_retried_for_same_old_prefix](../../tests/test_compaction.py#L164) |
| 175 | [test_recent_tool_calls_and_ids_stay_complete](../../tests/test_compaction.py#L175) |
| 189 | [test_incomplete_or_oversized_latest_chain_is_never_discarded](../../tests/test_compaction.py#L189) |
| 201 | [test_oversized_latest_input_cannot_be_fixed_by_summary](../../tests/test_compaction.py#L201) |
| 211 | [test_summary_excerpts_large_old_record_and_marks_loss](../../tests/test_compaction.py#L211) |
| 222 | [test_short_history_needs_no_model_and_raw_list_is_unchanged](../../tests/test_compaction.py#L222) |
| 230 | [test_memory_only_messages_cannot_write_checkpoint](../../tests/test_compaction.py#L230) |
| 236 | [test_multiple_summary_batches_merge_prior_summary_without_tools](../../tests/test_compaction.py#L236) |
| 242 | [test_multiple_summary_batches_merge_prior_summary_without_tools.summarize_batch](../../tests/test_compaction.py#L242) |
| 253 | [test_checkpoint_save_failure_does_not_activate_summary](../../tests/test_compaction.py#L253) |
| 263 | [test_cli_manual_and_auto_controls_operate_on_current_session](../../tests/test_compaction.py#L263) |
| 268 | [test_cli_manual_and_auto_controls_operate_on_current_session.NoServices.__enter__](../../tests/test_compaction.py#L268) |
| 269 | [test_cli_manual_and_auto_controls_operate_on_current_session.NoServices.__exit__](../../tests/test_compaction.py#L269) |

### test_context_window.py

源码：[test_context_window.py](../../tests/test_context_window.py)。

| 行 | 定义 |
| ---: | --- |
| 16 | [budget](../../tests/test_context_window.py#L16) |
| 26 | [turn](../../tests/test_context_window.py#L26) |
| 30 | [tool_turn](../../tests/test_context_window.py#L30) |
| 43 | [test_recent_turns_kept_with_rules_and_skills_history_unchanged](../../tests/test_context_window.py#L43) |
| 54 | [test_tool_calls_and_results_are_kept_as_complete_user_turn](../../tests/test_context_window.py#L54) |
| 60 | [test_char_budget_drops_entire_old_turn](../../tests/test_context_window.py#L60) |
| 69 | [test_oversized_latest_turn_is_rejected_before_network](../../tests/test_context_window.py#L69) |
| 80 | [test_system_and_tool_definitions_are_counted](../../tests/test_context_window.py#L80) |
| 86 | [test_incomplete_latest_tool_turn_is_rejected](../../tests/test_context_window.py#L86) |
| 91 | [test_damaged_old_turn_and_orphan_results_are_not_sent](../../tests/test_context_window.py#L91) |
| 99 | [test_generation_system_prompt_is_preserved_without_project_context](../../tests/test_context_window.py#L99) |
| 104 | [test_actual_request_matches_budgeted_payload_and_disk_is_not_trimmed](../../tests/test_context_window.py#L104) |
| 113 | [test_actual_request_matches_budgeted_payload_and_disk_is_not_trimmed.request](../../tests/test_context_window.py#L113) |
| 124 | [test_agent_returns_readable_budget_error_without_tools](../../tests/test_context_window.py#L124) |
| 133 | [test_invalid_budget_fails_explicitly](../../tests/test_context_window.py#L133) |

### test_file_interaction.py

源码：[test_file_interaction.py](../../tests/test_file_interaction.py)。

| 行 | 定义 |
| ---: | --- |
| 15 | [project](../../tests/test_file_interaction.py#L15) |
| 24 | [completions](../../tests/test_file_interaction.py#L24) |
| 30 | [test_path_completion_hides_private_and_quotes_spaces](../../tests/test_file_interaction.py#L30) |
| 43 | [test_path_parser_preserves_keywords_and_supports_quotes](../../tests/test_file_interaction.py#L43) |
| 51 | [test_picker_navigates_and_cancels_without_reading](../../tests/test_file_interaction.py#L51) |
| 57 | [test_picker_navigates_and_cancels_without_reading.choose](../../tests/test_file_interaction.py#L57) |
| 68 | [test_confirmation_default_denial_and_plain_mode](../../tests/test_file_interaction.py#L68) |
| 84 | [test_files_command_attaches_through_real_permission_entry](../../tests/test_file_interaction.py#L84) |
| 88 | [test_files_command_attaches_through_real_permission_entry.NoServices.__enter__](../../tests/test_file_interaction.py#L88) |
| 89 | [test_files_command_attaches_through_real_permission_entry.NoServices.__exit__](../../tests/test_file_interaction.py#L89) |
| 102 | [test_real_selection_keys](../../tests/test_file_interaction.py#L102) |

### test_file_picker.py

源码：[test_file_picker.py](../../tests/test_file_picker.py)。

| 行 | 定义 |
| ---: | --- |
| 13 | [project](../../tests/test_file_picker.py#L13) |
| 27 | [test_catalog_ignores_protected_dependencies_and_symlinks](../../tests/test_file_picker.py#L27) |
| 33 | [test_catalog_reports_limit](../../tests/test_file_picker.py#L33) |
| 40 | [test_fuzzy_filename_and_path_ranking](../../tests/test_file_picker.py#L40) |
| 47 | [test_attachments_read_all_then_make_one_message](../../tests/test_file_picker.py#L47) |
| 54 | [test_failed_batch_has_no_partial_message](../../tests/test_file_picker.py#L54) |
| 61 | [test_attachment_batch_size_limit](../../tests/test_file_picker.py#L61) |
| 74 | [test_real_fuzzy_multi_select_keys](../../tests/test_file_picker.py#L74) |

### test_hooks_skill_generation.py

源码：[test_hooks_skill_generation.py](../../tests/test_hooks_skill_generation.py)。

| 行 | 定义 |
| ---: | --- |
| 14 | [project](../../tests/test_hooks_skill_generation.py#L14) |
| 30 | [test_generated_skill_uses_diff_confirmation_and_no_auto_activation](../../tests/test_hooks_skill_generation.py#L30) |
| 31 | [test_generated_skill_uses_diff_confirmation_and_no_auto_activation.approve](../../tests/test_hooks_skill_generation.py#L31) |
| 46 | [test_refusal_makes_no_directory_or_file](../../tests/test_hooks_skill_generation.py#L46) |
| 52 | [test_existing_skill_is_not_overwritten_or_sent_to_model](../../tests/test_hooks_skill_generation.py#L52) |
| 61 | [test_conflicting_create_during_confirmation_preserves_other_file](../../tests/test_hooks_skill_generation.py#L61) |
| 62 | [test_conflicting_create_during_confirmation_preserves_other_file.conflict](../../tests/test_hooks_skill_generation.py#L62) |
| 77 | [test_bad_generated_output_is_not_saved_or_confirmed](../../tests/test_hooks_skill_generation.py#L77) |
| 84 | [test_network_failure_reports_error](../../tests/test_hooks_skill_generation.py#L84) |
| 91 | [test_invalid_names_do_not_request_model](../../tests/test_hooks_skill_generation.py#L91) |
| 96 | [test_before_hook_blocks_creation_before_confirmation](../../tests/test_hooks_skill_generation.py#L96) |
| 105 | [test_broken_before_hook_fails_closed](../../tests/test_hooks_skill_generation.py#L105) |
| 112 | [test_after_hook_failure_keeps_success_and_records_warning](../../tests/test_hooks_skill_generation.py#L112) |
| 121 | [test_hook_cannot_mutate_arguments_and_result_snapshots](../../tests/test_hooks_skill_generation.py#L121) |
| 122 | [test_hook_cannot_mutate_arguments_and_result_snapshots.mutate](../../tests/test_hooks_skill_generation.py#L122) |
| 134 | [test_hook_lifecycle_order_and_after_receives_denial](../../tests/test_hooks_skill_generation.py#L134) |
| 136 | [test_hook_lifecycle_order_and_after_receives_denial.before](../../tests/test_hooks_skill_generation.py#L136) |
| 139 | [test_hook_lifecycle_order_and_after_receives_denial.after](../../tests/test_hooks_skill_generation.py#L139) |

### test_mcp_client.py

源码：[test_mcp_client.py](../../tests/test_mcp_client.py)。

| 行 | 定义 |
| ---: | --- |
| 20 | [configured](../../tests/test_mcp_client.py#L20) |
| 34 | [test_real_stdio_handshake_and_discovery](../../tests/test_mcp_client.py#L34) |
| 49 | [test_denied_start_does_not_connect](../../tests/test_mcp_client.py#L49) |
| 57 | [test_unknown_server](../../tests/test_mcp_client.py#L57) |
| 62 | [test_invalid_configuration_does_not_prompt](../../tests/test_mcp_client.py#L62) |
| 70 | [test_dead_server_reports_failure](../../tests/test_mcp_client.py#L70) |
| 77 | [test_unresponsive_server_times_out](../../tests/test_mcp_client.py#L77) |

### test_mcp_lifecycle.py

源码：[test_mcp_lifecycle.py](../../tests/test_mcp_lifecycle.py)。

| 行 | 定义 |
| ---: | --- |
| 23 | [server](../../tests/test_mcp_lifecycle.py#L23) |
| 58 | [assert_process_gone](../../tests/test_mcp_lifecycle.py#L58) |
| 64 | [test_startup_load_reuses_process_refresh_does_not_restart_and_exit_closes](../../tests/test_mcp_lifecycle.py#L64) |
| 78 | [test_keyboard_interrupt_closes_service](../../tests/test_mcp_lifecycle.py#L78) |
| 86 | [test_timeout_disconnects_unregisters_and_refresh_reconnects](../../tests/test_mcp_lifecycle.py#L86) |
| 98 | [test_sigint_cancels_call_closes_service_and_allows_reconnect](../../tests/test_mcp_lifecycle.py#L98) |

### test_mcp_tools.py

源码：[test_mcp_tools.py](../../tests/test_mcp_tools.py)。

| 行 | 定义 |
| ---: | --- |
| 28 | [registry](../../tests/test_mcp_tools.py#L28) |
| 38 | [discovered](../../tests/test_mcp_tools.py#L38) |
| 48 | [test_registration_exposes_model_definition_and_binds_remote_name](../../tests/test_mcp_tools.py#L48) |
| 68 | [test_invalid_mcp_arguments_never_prompt_or_call](../../tests/test_mcp_tools.py#L68) |
| 77 | [test_mcp_denial_and_unknown_source_never_launch](../../tests/test_mcp_tools.py#L77) |
| 94 | [test_invalid_schema_keeps_previous_registration](../../tests/test_mcp_tools.py#L94) |
| 104 | [test_refresh_removes_disappeared_tools](../../tests/test_mcp_tools.py#L104) |
| 113 | [test_duplicate_remote_names_fail_without_partial_registration](../../tests/test_mcp_tools.py#L113) |
| 120 | [test_pagination_is_collected_and_repeating_cursor_rejected](../../tests/test_mcp_tools.py#L120) |
| 121 | [test_pagination_is_collected_and_repeating_cursor_rejected.run](../../tests/test_mcp_tools.py#L121) |
| 126 | [test_pagination_is_collected_and_repeating_cursor_rejected.run.list_tools](../../tests/test_mcp_tools.py#L126) |
| 133 | [real_discovery](../../tests/test_mcp_tools.py#L133) |
| 146 | [test_agent_loop_with_real_mcp_and_history](../../tests/test_mcp_tools.py#L146) |
| 155 | [test_agent_loop_with_real_mcp_and_history.model_response](../../tests/test_mcp_tools.py#L155) |
| 172 | [test_changed_schema_is_rejected_before_remote_call](../../tests/test_mcp_tools.py#L172) |

### test_new_files.py

源码：[test_new_files.py](../../tests/test_new_files.py)。

| 行 | 定义 |
| ---: | --- |
| 14 | [project](../../tests/test_new_files.py#L14) |
| 21 | [create](../../tests/test_new_files.py#L21) |
| 25 | [test_create_nested_file_after_review](../../tests/test_new_files.py#L25) |
| 26 | [test_create_nested_file_after_review.approve](../../tests/test_new_files.py#L26) |
| 37 | [test_refusal_creates_no_directory](../../tests/test_new_files.py#L37) |
| 43 | [test_existing_and_concurrently_created_file_never_overwritten](../../tests/test_new_files.py#L43) |
| 50 | [test_existing_and_concurrently_created_file_never_overwritten.race](../../tests/test_new_files.py#L50) |
| 59 | [test_protected_paths_fail_before_approval](../../tests/test_new_files.py#L59) |
| 64 | [test_symlink_parent_rejected_and_retarget_during_review_blocked](../../tests/test_new_files.py#L64) |
| 69 | [test_symlink_parent_rejected_and_retarget_during_review_blocked.retarget](../../tests/test_new_files.py#L69) |
| 77 | [test_empty_unicode_and_limit](../../tests/test_new_files.py#L77) |
| 88 | [test_created_code_and_test_run_in_real_sandbox](../../tests/test_new_files.py#L88) |

### test_package_project.py

源码：[test_package_project.py](../../tests/test_package_project.py)。

| 行 | 定义 |
| ---: | --- |
| 5 | [test_package_excludes_environment_credentials_and_conversations](../../tests/test_package_project.py#L5) |

### test_process_tasks.py

源码：[test_process_tasks.py](../../tests/test_process_tasks.py)。

| 行 | 定义 |
| ---: | --- |
| 13 | [project](../../tests/test_process_tasks.py#L13) |
| 23 | [test_unknown_task_rejected_before_confirmation](../../tests/test_process_tasks.py#L23) |
| 32 | [test_start_denial_does_not_launch](../../tests/test_process_tasks.py#L32) |
| 42 | [test_real_pty_input_readonly_and_no_secrets](../../tests/test_process_tasks.py#L42) |
| 58 | [test_real_timeout_cancel_and_output_limit](../../tests/test_process_tasks.py#L58) |
| 72 | [test_pty_has_controlling_terminal_and_ctrl_c](../../tests/test_process_tasks.py#L72) |
| 89 | [test_subagent_isolated_config_and_denies_model_write](../../tests/test_process_tasks.py#L89) |
| 96 | [test_subagent_isolated_config_and_denies_model_write.Handler.log_message](../../tests/test_process_tasks.py#L96) |
| 98 | [test_subagent_isolated_config_and_denies_model_write.Handler.do_POST](../../tests/test_process_tasks.py#L98) |
| 134 | [test_launch_payload_failure_reaps_process_and_removes_job](../../tests/test_process_tasks.py#L134) |
| 149 | [test_cancel_finished_job_preserves_result_without_signalling](../../tests/test_process_tasks.py#L149) |
| 161 | [test_invalid_worker_payload_never_starts_process](../../tests/test_process_tasks.py#L161) |

### test_project_instructions.py

源码：[test_project_instructions.py](../../tests/test_project_instructions.py)。

| 行 | 定义 |
| ---: | --- |
| 13 | [project](../../tests/test_project_instructions.py#L13) |
| 21 | [test_loaded_rules_survive_clear_and_are_not_persisted](../../tests/test_project_instructions.py#L21) |
| 37 | [test_request_body_contains_rules_without_mutating_history](../../tests/test_project_instructions.py#L37) |
| 46 | [test_request_body_contains_rules_without_mutating_history.capture](../../tests/test_project_instructions.py#L46) |
| 59 | [test_empty_invalid_large_and_bom_files](../../tests/test_project_instructions.py#L59) |
| 66 | [test_missing_file_clears_previous_rules](../../tests/test_project_instructions.py#L66) |
| 75 | [test_external_symlink_is_rejected](../../tests/test_project_instructions.py#L75) |
| 81 | [test_directory_is_reported_as_error](../../tests/test_project_instructions.py#L81) |

### test_project_search.py

源码：[test_project_search.py](../../tests/test_project_search.py)。

| 行 | 定义 |
| ---: | --- |
| 13 | [project](../../tests/test_project_search.py#L13) |
| 24 | [test_recursive_results_include_paths_lines_and_glob](../../tests/test_project_search.py#L24) |
| 35 | [test_protected_paths_dependencies_and_symlinks_are_skipped](../../tests/test_project_search.py#L35) |
| 49 | [test_non_text_large_and_long_lines_are_reported](../../tests/test_project_search.py#L49) |
| 62 | [test_limits_are_explicit_and_do_not_claim_complete_results](../../tests/test_project_search.py#L62) |
| 68 | [test_timeout_returns_partial_status](../../tests/test_project_search.py#L68) |
| 75 | [test_literal_search_and_invalid_inputs](../../tests/test_project_search.py#L75) |
| 84 | [test_file_read_error_returns_warning_without_hiding_other_results](../../tests/test_project_search.py#L84) |
| 86 | [test_file_read_error_returns_warning_without_hiding_other_results.fail_one](../../tests/test_project_search.py#L86) |

### test_sandbox.py

源码：[test_sandbox.py](../../tests/test_sandbox.py)。

| 行 | 定义 |
| ---: | --- |
| 16 | [isolated_project](../../tests/test_sandbox.py#L16) |
| 25 | [test_reject_before_confirm](../../tests/test_sandbox.py#L25) |
| 33 | [test_rejection_never_starts_process](../../tests/test_sandbox.py#L33) |
| 42 | [test_missing_bwrap_has_no_fallback](../../tests/test_sandbox.py#L42) |
| 50 | [test_command_is_fixed_argv](../../tests/test_sandbox.py#L50) |
| 64 | [test_output_and_time_bounds](../../tests/test_sandbox.py#L64) |
| 83 | [test_real_sandbox_boundaries](../../tests/test_sandbox.py#L83) |
| 130 | [test_real_test_failure](../../tests/test_sandbox.py#L130) |
| 139 | [test_real_timeout](../../tests/test_sandbox.py#L139) |
| 147 | [test_real_output_limit](../../tests/test_sandbox.py#L147) |
| 156 | [test_broken_sandbox_does_not_run_host](../../tests/test_sandbox.py#L156) |

### test_sessions.py

源码：[test_sessions.py](../../tests/test_sessions.py)。

| 行 | 定义 |
| ---: | --- |
| 12 | [project](../../tests/test_sessions.py#L12) |
| 22 | [test_switch_persists_independent_histories_and_default_is_preserved](../../tests/test_sessions.py#L22) |
| 34 | [test_new_process_manager_can_reload_named_history](../../tests/test_sessions.py#L34) |
| 44 | [test_clear_only_clears_current_session](../../tests/test_sessions.py#L44) |
| 54 | [test_tool_request_and_results_survive_session_switch](../../tests/test_sessions.py#L54) |
| 66 | [test_skills_are_isolated_and_restored_within_current_process](../../tests/test_sessions.py#L66) |
| 81 | [test_invalid_name_preserves_current_path_and_skills](../../tests/test_sessions.py#L81) |
| 90 | [test_symlink_directory_and_session_file_are_rejected](../../tests/test_sessions.py#L90) |
| 102 | [test_unreadable_target_keeps_old_session](../../tests/test_sessions.py#L102) |
| 111 | [test_exports_are_per_session_and_private_from_tools](../../tests/test_sessions.py#L111) |
| 123 | [test_rename_default_preserves_history_and_updates_future_writes](../../tests/test_sessions.py#L123) |
| 140 | [test_rename_rejects_existing_target_without_changing_state](../../tests/test_sessions.py#L140) |
| 152 | [test_rename_empty_session_and_same_name](../../tests/test_sessions.py#L152) |
| 160 | [test_invalid_rename_preserves_state](../../tests/test_sessions.py#L160) |
| 166 | [test_rename_source_unlink_failure_rolls_back_new_link](../../tests/test_sessions.py#L166) |
| 171 | [test_rename_source_unlink_failure_rolls_back_new_link.fail_source](../../tests/test_sessions.py#L171) |

### test_skills.py

源码：[test_skills.py](../../tests/test_skills.py)。

| 行 | 定义 |
| ---: | --- |
| 14 | [project](../../tests/test_skills.py#L14) |
| 23 | [write_skill](../../tests/test_skills.py#L23) |
| 30 | [test_discovery_does_not_activate_or_load_content](../../tests/test_skills.py#L30) |
| 37 | [test_only_selected_skill_enters_actual_request](../../tests/test_skills.py#L37) |
| 46 | [test_only_selected_skill_enters_actual_request.request](../../tests/test_skills.py#L46) |
| 57 | [test_clear_history_retains_skill_and_explicit_deactivation_removes_it](../../tests/test_skills.py#L57) |
| 69 | [test_invalid_skill_names_are_rejected](../../tests/test_skills.py#L69) |
| 74 | [test_external_and_outside_skills_symlinks_are_rejected](../../tests/test_skills.py#L74) |
| 87 | [test_invalid_content_is_not_activated](../../tests/test_skills.py#L87) |
| 93 | [test_missing_directory_and_file_are_handled](../../tests/test_skills.py#L93) |
| 98 | [test_activation_limit_reloading_and_total_bytes](../../tests/test_skills.py#L98) |

### test_streaming.py

源码：[test_streaming.py](../../tests/test_streaming.py)。

| 行 | 定义 |
| ---: | --- |
| 15 | [stream_bytes](../../tests/test_streaming.py#L15) |
| 19 | [chunk](../../tests/test_streaming.py#L19) |
| 26 | [call](../../tests/test_streaming.py#L26) |
| 30 | [test_text_is_emitted_before_stream_finishes_and_thinking_is_accumulated](../../tests/test_streaming.py#L30) |
| 34 | [test_text_is_emitted_before_stream_finishes_and_thinking_is_accumulated.show](../../tests/test_streaming.py#L34) |
| 42 | [test_parallel_tool_calls_are_collected_from_multiple_chunks](../../tests/test_streaming.py#L42) |
| 58 | [test_invalid_or_incomplete_stream_fails_explicitly](../../tests/test_streaming.py#L58) |
| 63 | [test_response_size_limit_and_blank_lines](../../tests/test_streaming.py#L63) |
| 70 | [test_connection_reset_is_reported_and_timeout_remains_distinguishable](../../tests/test_streaming.py#L70) |
| 81 | [conversation](../../tests/test_streaming.py#L81) |
| 89 | [test_streaming_agent_waits_for_done_before_executing_and_prints_final_once](../../tests/test_streaming.py#L89) |
| 96 | [test_streaming_agent_waits_for_done_before_executing_and_prints_final_once.request](../../tests/test_streaming.py#L96) |
| 99 | [test_streaming_agent_waits_for_done_before_executing_and_prints_final_once.execute](../../tests/test_streaming.py#L99) |
| 116 | [test_stream_failure_never_executes_or_saves_partial_assistant](../../tests/test_streaming.py#L116) |
| 128 | [test_switch_stream_mode_changes_request_and_nonstream_prints_once](../../tests/test_streaming.py#L128) |
| 130 | [test_switch_stream_mode_changes_request_and_nonstream_prints_once.request](../../tests/test_streaming.py#L130) |
| 147 | [test_skill_generation_style_request_remains_nonstream](../../tests/test_streaming.py#L147) |
| 149 | [test_skill_generation_style_request_remains_nonstream.request](../../tests/test_streaming.py#L149) |
| 157 | [test_nonstream_response_size_limit](../../tests/test_streaming.py#L157) |

### test_terminal_cli.py

源码：[test_terminal_cli.py](../../tests/test_terminal_cli.py)。

| 行 | 定义 |
| ---: | --- |
| 16 | [test_startup_flags_and_help_exit_without_loading_services](../../tests/test_terminal_cli.py#L16) |
| 26 | [test_plain_mode_uses_input_and_help_contains_commands](../../tests/test_terminal_cli.py#L26) |
| 34 | [test_non_tty_uses_plain_input](../../tests/test_terminal_cli.py#L34) |
| 41 | [test_completion_lists_matching_commands](../../tests/test_terminal_cli.py#L41) |
| 50 | [test_alt_enter_newline_enter_submit_with_real_prompt_application](../../tests/test_terminal_cli.py#L50) |
| 61 | [test_cancel_chat_generation_keeps_history_and_next_request_works](../../tests/test_terminal_cli.py#L61) |
| 78 | [test_cli_cancellation_returns_to_input_and_saves_complete_diagnostic](../../tests/test_terminal_cli.py#L78) |
| 81 | [test_cli_cancellation_returns_to_input_and_saves_complete_diagnostic.NoServices.__enter__](../../tests/test_terminal_cli.py#L81) |
| 82 | [test_cli_cancellation_returns_to_input_and_saves_complete_diagnostic.NoServices.__exit__](../../tests/test_terminal_cli.py#L82) |
| 83 | [test_cli_cancellation_returns_to_input_and_saves_complete_diagnostic.NoServices.load_configured](../../tests/test_terminal_cli.py#L83) |
| 95 | [test_startup_session_and_disabled_mcp_refresh](../../tests/test_terminal_cli.py#L95) |
| 98 | [test_startup_session_and_disabled_mcp_refresh.NoServices.__enter__](../../tests/test_terminal_cli.py#L98) |
| 99 | [test_startup_session_and_disabled_mcp_refresh.NoServices.__exit__](../../tests/test_terminal_cli.py#L99) |
| 100 | [test_startup_session_and_disabled_mcp_refresh.NoServices.load_configured](../../tests/test_terminal_cli.py#L100) |
| 109 | [test_user_can_switch_approval_mode_without_model_request](../../tests/test_terminal_cli.py#L109) |
| 114 | [test_user_can_switch_approval_mode_without_model_request.NoServices.__enter__](../../tests/test_terminal_cli.py#L114) |
| 115 | [test_user_can_switch_approval_mode_without_model_request.NoServices.__exit__](../../tests/test_terminal_cli.py#L115) |

### test_tool_display.py

源码：[test_tool_display.py](../../tests/test_tool_display.py)。

| 行 | 定义 |
| ---: | --- |
| 8 | [test_summary_does_not_dump_replacement_or_mcp_arguments](../../tests/test_tool_display.py#L8) |
| 17 | [test_diff_preserves_review_lines_and_escapes_terminal_controls](../../tests/test_tool_display.py#L17) |
| 26 | [test_output_summary_is_bounded_without_changing_result](../../tests/test_tool_display.py#L26) |
| 36 | [test_runtime_refusal_shows_diff_before_prompt_and_preserves_file](../../tests/test_tool_display.py#L36) |
| 42 | [test_runtime_refusal_shows_diff_before_prompt_and_preserves_file.refuse](../../tests/test_tool_display.py#L42) |

### test_tool_runtime.py

源码：[test_tool_runtime.py](../../tests/test_tool_runtime.py)。

| 行 | 定义 |
| ---: | --- |
| 18 | [project](../../tests/test_tool_runtime.py#L18) |
| 28 | [arguments_for](../../tests/test_tool_runtime.py#L28) |
| 41 | [test_every_tool_rejects_escape_before_prompt](../../tests/test_tool_runtime.py#L41) |
| 49 | [test_every_tool_rejects_private_paths](../../tests/test_tool_runtime.py#L49) |
| 55 | [test_symlink_to_private_and_external_targets_is_blocked](../../tests/test_tool_runtime.py#L55) |
| 67 | [test_manual_and_model_read_do_not_require_confirmation](../../tests/test_tool_runtime.py#L67) |
| 75 | [test_model_cannot_supply_source_or_policy](../../tests/test_tool_runtime.py#L75) |
| 82 | [test_unknown_source_or_missing_policy_never_prepares_or_executes](../../tests/test_tool_runtime.py#L82) |
| 94 | [test_edit_diff_precedes_one_confirmation_and_refusal_preserves_file](../../tests/test_tool_runtime.py#L94) |
| 95 | [test_edit_diff_precedes_one_confirmation_and_refusal_preserves_file.refuse](../../tests/test_tool_runtime.py#L95) |
| 107 | [test_direct_edit_still_uses_gate_and_conflict_protection](../../tests/test_tool_runtime.py#L107) |
| 108 | [test_direct_edit_still_uses_gate_and_conflict_protection.conflict](../../tests/test_tool_runtime.py#L108) |
| 117 | [test_accepted_edit_writes_once_and_logs_once](../../tests/test_tool_runtime.py#L117) |
| 125 | [test_path_retargeted_during_confirmation_is_rejected](../../tests/test_tool_runtime.py#L125) |
| 127 | [test_path_retargeted_during_confirmation_is_rejected.change](../../tests/test_tool_runtime.py#L127) |
| 135 | [test_invalid_parameters_do_not_prompt](../../tests/test_tool_runtime.py#L135) |
| 146 | [test_exception_and_bad_result_are_logged_once](../../tests/test_tool_runtime.py#L146) |
| 159 | [test_directory_listing_hides_private_entries](../../tests/test_tool_runtime.py#L159) |
| 167 | [test_test_execution_confirms_once_after_preflight](../../tests/test_tool_runtime.py#L167) |
| 178 | [test_registry_drives_model_definitions](../../tests/test_tool_runtime.py#L178) |

### test_workspace.py

源码：[test_workspace.py](../../tests/test_workspace.py)。

| 行 | 定义 |
| ---: | --- |
| 19 | [test_workspace_routes_tools_state_instructions_and_restores](../../tests/test_workspace.py#L19) |
| 38 | [test_project_histories_and_sessions_do_not_mix](../../tests/test_workspace.py#L38) |
| 53 | [test_invalid_workspace_and_symlinked_state_rejected](../../tests/test_workspace.py#L53) |
| 64 | [test_invalid_state_types_rejected_before_startup](../../tests/test_workspace.py#L64) |
| 76 | [test_script_workspace_option_persists_only_selected_project](../../tests/test_workspace.py#L76) |
| 78 | [test_script_workspace_option_persists_only_selected_project.NoServices.__enter__](../../tests/test_workspace.py#L78) |
| 79 | [test_script_workspace_option_persists_only_selected_project.NoServices.__exit__](../../tests/test_workspace.py#L79) |
| 89 | [test_external_workspace_uses_assistant_runtime_in_real_sandbox](../../tests/test_workspace.py#L89) |
