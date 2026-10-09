# 真实模型验收与演示

## 本次结果

2026-10-09，在独立临时项目中使用真实 Ollama 模型 `qwen3.8-27b-mtp:latest` 和实际 CLI 完成一轮验收。没有模拟模型响应，没有关闭权限策略，也没有由官方助手代写最终函数；每次写入和执行均审查后批准。

| 项目 | 实际结果 | 证据 |
| --- | --- | --- |
| 修改前运行测试 | 2 failed，退出码 1 | 真实工具结果和终端日志 |
| 修改函数 | 修复折扣计算，增加非法参数检查 | diff、工具结果、源码快照 |
| 新建测试 | 新增 6 项边界测试 | create_file 记录与源码快照 |
| 修改后运行测试 | 8 passed，退出码 0 | 模型发起的真实沙箱执行 |
| 固定测试未被篡改 | SHA-256 与初始值相同 | manifest 和 report |
| 独立核验 | 另行准备的 8 个用例全部通过 | independent_test_result.json |
| 重启恢复 | 新 CLI 进程恢复原历史，无需工具即可回忆修改和测试状态 | restart-cli.log、restart_verified.json |
| MCP | 模型调用 mcp__demo__add，服务真实返回 42 | 会话中的工具结果 |
| 路径权限 | 项目外路径和 .ai-cli 会话文件均拒绝读取 | restart-cli.log |
| 项目回归 | 238 passed，包含真实终端、MCP 和沙箱集成 | 实际 pytest 回归结果 |

主修复任务共执行 7 次工具调用，其中三个读取由同一次模型响应提出，客户端依次执行，当前没有并行工具执行。随后还执行了一次模型发起的 MCP 工具调用。

证据目录：[本次验收文件](../artifacts/acceptance/20261009T122307356474Z/)。优先查看 [结构化报告](../artifacts/acceptance/20261009T122307356474Z/report.json)、[会话历史](../artifacts/acceptance/20261009T122307356474Z/session.jsonl) 和 [独立验证结果](../artifacts/acceptance/20261009T122307356474Z/independent_test_result.json)。模型摘要、后端和 SDK 版本保存在 `model_metadata.json`。日志可能包含终端颜色控制码；JSON 和源码快照便于直接审阅。

这是一轮固定任务的通过记录，不代表任意模型、任意项目均能成功。本轮核心任务使用 `--plain`，增强文件面板的实际按键与多选另有自动集成测试及之前的人工终端验证。没有用这一轮结果宣称 Skills 的所有流程、复杂多文件修改或外部 MCP 隔离都经过了真实模型验收。

## 重新执行核心验收

在助手源码目录创建一份新的验收项目：

```bash
cd /home/perrylong/code/cli
.conda-env/bin/python scripts/acceptance.py prepare
```

命令输出独立 `workspace` 和证据 `evidence` 路径。下面的变量替换成该次输出值，后续步骤一直使用同一组路径：

```bash
case_project=/tmp/ai-cli-acceptance-本次目录
case_evidence=/home/perrylong/code/cli/artifacts/acceptance/本次编号
cat "$case_evidence/task.txt"
ai-cli -C "$case_project" --plain --approval-mode manual --no-mcp --session acceptance
```

将 `task.txt` 内容粘贴给模型。预期顺序为读取 → 第一次测试失败 → 审查函数 diff → 审查新测试 diff → 第二次测试通过。只批准当前演示项目里符合任务要求的动作，不修改固定测试 `test_discount.py`。如果模型没有完成某一步，保留失败记录，不把预期结果当成实测。

本轮第一次实际输入就是 `task.txt` 中的任务文字，无需通过提示要求模型冒充工具执行。

## 验证重启恢复

第一轮完成后输入 `/exit`，保存初始历史快照，再启动一个新 CLI 进程：

```bash
.conda-env/bin/python scripts/acceptance.py snapshot "$case_evidence"
ai-cli -C "$case_project" --plain --approval-mode manual --no-mcp --session acceptance
```

可以先用 `/history` 查看恢复的消息，再输入快照命令给出的回忆问题：

```text
请只根据本会话已有历史回答：刚才修复了哪个文件、新建了哪个测试文件、最后测试是否通过？不要重新调用工具。
```

得到回答后退出，检查原历史未变化、新问题被保存且模型无需工具即可回忆文件：

```bash
.conda-env/bin/python scripts/acceptance.py restart "$case_evidence"
```

这个检查只能确认记录与回答，新的 CLI 进程本身应实际启动，并可用终端日志留证。

## 独立测试与最终报告

运行事先写好的独立测试。该测试在模型修复结束之后加入，避免把它当作模型新增测试的替代品；同样经过执行入口授权和真实沙箱：

```bash
.conda-env/bin/python scripts/acceptance.py verify "$case_evidence"
.conda-env/bin/python scripts/acceptance.py check "$case_evidence"
```

`verify` 预期是 8 passed；`check` 仅在全部必需条件通过时返回退出码 0。它检查实际历史和工具结果、执行顺序、固定测试哈希、独立测试结果以及重启记录，不凭模型文字中的“通过”判定成功。证据检查本身已有 5 项防止误判的测试。

种子中的 `.py.txt` 是模板：准备脚本复制到临时项目时恢复 `.py` 后缀，防止故意错误的样例被助手自身的 pytest 收集。临时项目可能被 `/tmp` 清理；终端记录、会话和源码快照保留在仓库证据目录，重新验收请再次 `prepare`，不要覆盖旧记录。

## MCP 与交互演示

需要演示 MCP 时去掉 `--no-mcp`，审查并批准默认 demo 服务启动，然后输入：

```text
请真实调用 mcp__demo__add 工具计算 19 加 23，并根据工具返回的结果回答。不要心算代替工具调用。
```

工具参数确认后应返回结构化 `{"result": 42}`。这与模型直接回答 42 是两种不同的证据。重启记录检查应在新增这段对话之前完成；然后可以重新运行 `check`，它会额外记录 MCP 演示是否通过。

增强界面演示使用不带 `--plain` 的入口：`/files` 模糊筛选、Tab 多选、Enter 添加；`/browse` 逐层浏览；写入前展示 diff，权限面板默认拒绝，可选择批准。读项目外路径或 `.ai-cli` 应被拒绝。

讲解实现时沿着这条链即可：模型提出工具调用 → 注册表提供参数与权限声明 → 执行入口校验和授权 → 文件工具或沙箱 / MCP 执行 → 结果保存为完整历史 → 模型根据结果继续。沙箱只覆盖 pytest，MCP 服务目前没有统一沙箱隔离；已完成的写入不会因为取消而回滚。
