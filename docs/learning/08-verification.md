# 08：怎么验证、排错并讲给面试官听

## 1. 证据分四层

| 层次 | 做了什么 | 能证明什么 | 不能证明什么 |
| --- | --- | --- | --- |
| 单元测试 | 临时文件、Mock、固定模型响应、函数断言 | 参数、路径、控制流、返回格式等局部逻辑 | 所有真实模型都会正确规划 |
| 宿主集成 | 真实 bwrap、PTY、MCP、Chromium | 真实进程、协议与隔离行为 | 任意项目/网站安全可靠 |
| 真实模型固定任务 | 模型调用工具，独立检查记录与文件 | 该模型在该任务确实执行并成功 | 普遍任务成功率或跨模型保证 |
| CI | 干净 Ubuntu 安装依赖后普通 pytest | 源码可迁移，普通测试不依赖你的环境 | 你的 GPU/本地模型/namespace 都可用 |

目前上传版本 GitHub CI 普通测试是300通过、33跳过。此前完整本机回归332通过，之后新增一项浏览器体积测试，浏览器专项20通过。这些是不同运行口径，不能把skip说成pass，或把模拟响应说成真模型。

## 2. 测试文件与功能地图

| 功能 | 重点测试 |
| --- | --- |
| 代理与消息 | test_agent_history、test_streaming、test_api_adapter、test_cancellation |
| 工具与权限 | test_tool_runtime、test_approval、test_new_files、test_tool_display |
| 项目文件与交互 | test_project_search、test_file_picker、test_file_interaction |
| 上下文与会话 | test_context_window、test_compaction、test_sessions、test_workspace |
| MCP | test_mcp_client、test_mcp_tools、test_mcp_lifecycle |
| 规则/Skill/Hook | test_project_instructions、test_skills、test_hooks_skill_generation |
| 进程 | test_sandbox、test_process_tasks、test_agent_proposals |
| 终端入口 | test_terminal_cli |
| 浏览器 | test_browser |
| 交付证据 | test_acceptance_checks、test_package_project |

逐文件索引另附所有实际 test 函数名称及行号，帮助定位一个断言，而不是只凭文件名猜。

## 3. pytest 语法读法

`def test_xxx(...)` 被pytest收集；参数名tmp_path/monkeypatch等指fixture注入，不是生产代码自己调用。`@pytest.fixture`定义准备与清理，yield之后为清理阶段。

- tmp_path：每个测试一份临时目录，不写真实用户文件。
- monkeypatch.setattr/setitem：临时替换函数/配置，测试后恢复。
- Mock(return_value=...)：模拟依赖并记录调用次数。
- AsyncMock：模拟可await接口，assert_awaited_once核对。
- pytest.raises：必须抛对应异常，否则失败。
- parametrize：同一逻辑用多组输入跑，例如坏URL或工具越界。
- skipif：环境开关没设置则跳过真实宿主能力；不假装通过。

例：普通测试“执行只确认一次”模拟collect_output，并显式模拟bwrap可用，目的是验证授权流程；真实沙箱禁网则在test_real_sandbox_boundaries中运行实际程序。二者都需要，职责不同。

## 4. 怎么运行现有检查

当前用户偏好暂停本地Qwen/Ollama推理。本次编写文档没有运行模型；下面真实模型验收命令说明现有能力，暂停期间不要用当前Ollama配置运行。需要验收时应先配置已授权的远程兼容API，或由用户明确恢复本地推理。

```bash
# 普通逻辑，通常最快，不需模型服务或浏览器下载
PYTHONDONTWRITEBYTECODE=1 .conda-env/bin/python -m pytest -q -p no:cacheprovider tests

# 本机允许这些能力时，明确开启集成
CLI_BROWSER_INTEGRATION=1 CLI_MCP_INTEGRATION=1 CLI_SANDBOX_INTEGRATION=1 CLI_TERMINAL_INTEGRATION=1 CLI_HOST_SECRET=test-only \
PYTHONDONTWRITEBYTECODE=1 .conda-env/bin/python -m pytest -q -p no:cacheprovider tests

# 浏览器真实模型固定网页验收，需要本机模型可用
PYTHONDONTWRITEBYTECODE=1 .conda-env/bin/python scripts/browser_acceptance.py
```

CLI_HOST_SECRET是测试放入的占位值，用于证明子进程环境屏蔽，不要填真实秘密。

## 5. 验收脚本分别做什么

| 文件 | 内容 |
| --- | --- |
| scripts/acceptance.py | 建独立折扣项目、固定测试hash、记录真实调用、前失败后通过、重启与独立验证 |
| scripts/approval_acceptance.py | 真实子代理建议→独立自动审批→改源码→测试，固定测试不变 |
| scripts/compaction_acceptance.py | 固定种子历史、真实摘要与回忆，手动/自动/重启验证 |
| scripts/browser_acceptance.py | 随机名字与本地页，真实模型打开填写点击读取截图，核对PNG与页面 |
| scripts/package_project.py | 明确文件白名单打ZIP，跳符号链接，不含本机环境与记录 |

浏览器验收脚本仅为固定本地站点预先授权，不改普通CLI策略；九项检查读取真实tool结果和PNG，不信模型一句“完成了”。状态报告在artifacts，被源码包排除。

## 6. 一个问题从哪里开始查

| 现象 | 跟踪顺序 |
| --- | --- |
| 模型说没有MCP工具 | manager是否connect成功→registry工具名→request的get_tool_definitions→预算 |
| 调用出现却未执行 | arguments/schema→policy→路径→before Hook→prepare→approval |
| 修改未写入 | prepared.changed→boundary→审批→字节是否改变→apply结果 |
| 测试失败 | ok/exit_code/error/output→prepare环境→bwrap命令→真正pytest错误 |
| 重启没记忆 | -C/workspace→当前session→HISTORY_PATH→load_history过滤→context预算 |
| 流式中断后工具没执行 | done/finish_reason完整性检查，可能是正确的拒绝路径 |
| 子代理不能改文件 | 这是预期；看proposals，再父apply |
| PTY查询成功但命令失败 | inspect_task.ok是查询，检查exit_code/reason |
| 浏览器ref过期 | 每次read/操作会更新，使用最新elements编号 |
| 自动审查每次ask | control_file/size/no_task/reviewer网络等reason |

定位时先找最早真实错误字段，不要从最终模型措辞猜原因。检查历史里是否有完整assistant调用+tool结果；若只有模型文字没有工具证据，不能算执行。

## 7. 三分钟项目讲解范例

“我实现了一个Python终端编程助手。入口先绑定工作目录和会话，加载项目规则与MCP工具。用户任务保存为消息列表，模型通过HTTP返回文字或结构化工具请求。代理循环把请求交给统一执行器，执行器校验schema、路径、Hook和审批，再调用真实工具；结果写进完整消息链，模型据此继续。

文件修改分准备和应用两阶段，先算diff并审查，再检查原字节和真实目标是否改变，用同目录临时文件发布。测试放在bubblewrap中，通过namespace、只读挂载、禁网和最小环境隔离，并限制时间和输出；没有沙箱时拒绝宿主回退。

MCP用常驻stdio服务，异步连接由同一任务持有，同步CLI通过portal与队列请求。子代理是独立上下文的可信worker，可经统一 Runtime 读取、编辑、新建文件、运行测试和 PTY；它没有父聊天、MCP 或继续派生子代理的能力，也不是 OS 沙箱。manual 模式通过 TaskApprovalStore 等待任务卡或 CLI 的一次性决定，auto 模式的写入复用独立 review_write。工作区锁只在获批写入的最终提交阶段持有。会话 JSONL 保留完整原历史，上下文按完整轮次裁剪，摘要检查点有前缀 hash 并以数据身份注入。”

然后指出实际限制：只有根 AGENTS、手动 Skill、可信 Python Hook、worker 不是 OS 沙箱、MCP 未统一隔离、字符预算、基础单页浏览器；测试和 PTY 的 rlimit 是每进程资源上限，不是 cgroup 级任务总量配额。不要把未来计划补进讲解。

## 8. 常见追问与回答要点

| 面试官问 | 必须具体提到 |
| --- | --- |
| Agent与普通chat有什么区别 | tool_calls→真实执行→tool结果→再次请求，有预算与取消 |
| 为何不用系统命令读所有文件 | 文件工具接口窄、参数明确、边界可复用；通用执行用单独沙箱 |
| 沙箱怎样禁网 | bwrap --unshare-net，不是靠提示词 |
| 自动审批会被注入吗 | 独立无工具上下文+严格输出+硬边界+ask降级；仍非绝对免疫 |
| 子代理共享记忆吗 | 独立messages，收到任务与规则快照，不传父聊天；没有MCP或嵌套子代理 |
| 为什么要PTY | 真实终端语义与交互，不仅stdout管道 |
| MCP与内置工具区别 | 发现/调用外部服务，通过同一registry/runtime，但权限边界不同 |
| 压缩会丢信息吗 | 有损摘要，原历史保留，最新链完整，hash是对应性不是语义验证 |
| 怎么证明真实执行 | 工具历史+磁盘变化+实际exit code+独立测试，非模型自述 |

## 9. 看懂之后可以练的六个小改动

这些是学习建议，本教程没有替你实现。

1. 给 `show_history` 增加显示序号，只改显示，不改消息结构。
2. 在现有 search_file 练习区做大小写不敏感匹配，写两个输入输出样例。
3. 给一个内部helper画输入/返回表，解释每个变量为什么存在。
4. 为一个已有拒绝分支写断言，例如未知task_id。
5. 仿照read_page新增浏览器page_title，但仍经MCP与统一执行器；先说明为何它不需要任意JS。
6. 手工构造一段完整tool链和一段缺结果链，跟踪valid_turn的pending变化。

你的首要目标是解释现有控制链，并知道改哪里会影响什么，再进入更快的AI辅助实现。不要以“完全背下全部四千行”作为理解的门槛。
