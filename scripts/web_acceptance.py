"""本机协议夹具的端到端验收；不连接真实模型。"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def browser_environment(temporary):
    """仅验收进程读取本机已有中文字体，不复制或打包系统字体。"""
    font = Path("/mnt/c/Windows/Fonts/NotoSansSC-VF.ttf")
    environment = dict(os.environ)
    if font.exists():
        directory = Path(temporary) / "fonts"
        directory.mkdir(exist_ok=True)
        (directory / font.name).symlink_to(font)
        config = Path(temporary) / "fonts.conf"
        config.write_text(
            '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd">'
            "<fontconfig><dir>"
            + str(directory)
            + "</dir><cachedir>"
            + str(Path(temporary) / "font-cache")
            + "</cachedir></fontconfig>"
        )
        environment["FONTCONFIG_FILE"] = str(config)
    return environment


class FixtureModel(BaseHTTPRequestHandler):
    requests = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.requests.append(body)
        messages = body["messages"]
        newest = max(i for i, m in enumerate(messages) if m["role"] == "user")
        tool_messages = [m for m in messages[newest:] if m["role"] == "tool"]
        user_text = messages[newest]["content"]
        if "诊断失败" in user_text:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(
                b"fixture-only sensitive response body sk-abcdefghijklmnopqrstuvwxyz123456"
            )
            return
        if "子代理UI修改" in user_text:
            if not tool_messages:
                name, args = "read_file", {"path": "calc.py"}
            elif len(tool_messages) == 1:
                name, args = (
                    "edit_file",
                    {
                        "path": "calc.py",
                        "new_content": "def add(a,b):\n    return a + b\n# child-edit\n",
                    },
                )
            else:
                name, args = None, None
        elif "可写子代理UI" in user_text:
            if not tool_messages:
                name, args = "spawn_agent", {"task": "子代理UI修改：修改 calc.py 并汇报实际结果"}
            else:
                name, args = None, None
        elif "AI终端交互" in user_text:
            if not tool_messages:
                name, args = "list_tasks", {}
            elif len(tool_messages) == 1:
                name, args = (
                    "start_pty",
                    {
                        "argv": [
                            "python",
                            "-u",
                            "-c",
                            "print('AI_PROMPT',flush=True); value=input(); print('AI_INPUT_RESULT',value,flush=True)",
                        ],
                        "timeout": 30,
                    },
                )
            elif len(tool_messages) == 2:
                identifier = json.loads(tool_messages[1]["content"])["task_id"]
                name, args = "task_input", {"task_id": identifier, "text": "from-agent\n"}
            elif len(tool_messages) == 3:
                identifier = json.loads(tool_messages[1]["content"])["task_id"]
                name, args = "task_wait", {"task_id": identifier, "seconds": 3}
            else:
                name, args = None, None
        elif "持久后台" in user_text:
            if not tool_messages:
                name, args = (
                    "start_pty",
                    {
                        "path": ".",
                        "argv": [
                            "python",
                            "-u",
                            "-c",
                            "import time; print('BACKGROUND_READY',flush=True); print('BACKGROUND_INPUT',input(),flush=True); time.sleep(60)",
                        ],
                        "timeout": 120,
                    },
                )
            elif len(tool_messages) == 1:
                name, args = (
                    "edit_file",
                    {"path": "calc.py", "new_content": "def add(a,b):\n    return a + b\n"},
                )
            else:
                name, args = None, None
        elif "查询后台" in user_text:
            if not tool_messages:
                name, args = "task_status", {"task_id": user_text.split()[-1]}
            else:
                name, args = None, None
        elif not tool_messages:
            name, args = "read_file", {"path": "calc.py"}
        elif len(tool_messages) == 1:
            name, args = (
                "edit_file",
                {"path": "calc.py", "new_content": "def add(a, b):\n    return a + b\n"},
            )
        elif len(tool_messages) == 2 and json.loads(tool_messages[-1]["content"])["ok"]:
            name, args = "run_tests", {"path": "test_calc.py"}
        else:
            name, args = None, None
        if name:
            delta = {
                "tool_calls": [
                    {
                        "index": 0,
                        "id": "fixture-" + str(len(tool_messages)),
                        "type": "function",
                        "function": {"name": name, "arguments": json.dumps(args)},
                    }
                ]
            }
            finish = "tool_calls"
        else:
            delta = {"content": "夹具已完成；请以工具实际结果判断测试和修改。"}
            finish = "stop"
        self.send_response(200)
        if not body.get("stream"):
            message = {"role": "assistant", "content": delta.get("content", "")}
            if name:
                message["tool_calls"] = [
                    {k: v for k, v in delta["tool_calls"][0].items() if k != "index"}
                ]
            encoded = json.dumps(
                {"choices": [{"message": message, "finish_reason": finish}]}
            ).encode()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for item in [
            {"choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
            {"choices": [{"index": 0, "delta": {}, "finish_reason": finish}]},
        ]:
            self.wfile.write(("data: " + json.dumps(item, ensure_ascii=False) + "\n\n").encode())
        self.wfile.write(b"data: [DONE]\n\n")


def main():
    fixture = ThreadingHTTPServer(("127.0.0.1", 0), FixtureModel)
    threading.Thread(target=fixture.serve_forever, daemon=True).start()
    with tempfile.TemporaryDirectory(prefix="cli-web-acceptance-") as temporary:
        project = Path(temporary) / "project"
        project.mkdir()
        (project / "calc.py").write_text("def add(a, b):\n    return a - b\n")
        (project / "test_calc.py").write_text(
            "from calc import add\ndef test_add():\n    assert add(2, 3) == 5\n"
        )
        for command in (
            ["git", "init", "-q"],
            ["git", "add", "calc.py", "test_calc.py"],
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "seed",
            ],
        ):
            subprocess.run(command, cwd=project, check=True, capture_output=True)
        # 用户已有的未提交修改；快照必须保存它，而不是恢复到 HEAD。
        (project / "calc.py").write_text("def add(a, b):\n    return a - b\n# 用户已有的说明\n")
        # 端口由内核分配，关闭临时 socket 后立刻启动单个本机服务。
        import socket

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        environment = dict(
            os.environ,
            AI_CLI_WORKSPACE_ROOT=temporary,
            AI_CLI_WEB_STATE=str(Path(temporary) / ".ai-cli/web"),
            AI_CLI_MODEL="fixture",
            AI_CLI_BASE_URL=f"http://127.0.0.1:{fixture.server_port}/v1",
            AI_CLI_API_KEY_ENV="FIXTURE_KEY",
            FIXTURE_KEY="not-a-real-api-key",
            AI_CLI_MCP="0",
            AI_CLI_APPROVAL_MODE="manual",
            AI_CLI_EMBEDDING_MODEL="",
            LANGSMITH_TRACING="false",
            LANGCHAIN_TRACING_V2="false",
        )
        log_path = ROOT / "artifacts/web/acceptance-server.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w") as log:
            server = subprocess.Popen(
                [sys.executable, "-m", "web", "--port", str(port)],
                cwd=ROOT,
                env=environment,
                stdout=log,
                stderr=log,
            )
            base = f"http://127.0.0.1:{port}"
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

            def api(path, data=None, method=None):
                request = urllib.request.Request(
                    base + path,
                    data=json.dumps(data).encode() if data is not None else None,
                    headers={"Content-Type": "application/json"},
                    method=method,
                )
                with opener.open(request, timeout=10) as response:
                    return json.load(response)

            try:
                for _ in range(100):
                    try:
                        api("/api/health")
                        break
                    except OSError:
                        time.sleep(0.1)
                session = api(
                    "/api/sessions", {"title": "修复加法 · 验收", "workspace": str(project)}
                )
                identifier = session["id"]
                memory = api(
                    f"/api/sessions/{identifier}/memories",
                    {"content": "项目需求：add 必须执行加法，测试断言不能削弱"},
                )
                index = api(f"/api/sessions/{identifier}/index", {}, "POST")
                reused_index = api(f"/api/sessions/{identifier}/index", {}, "POST")
                assert reused_index["embedded_chunks"] == 0
                assert reused_index["reused_chunks"] == index["chunks"]
                hits = api(f"/api/sessions/{identifier}/search", {"query": "add"})
                from playwright.sync_api import sync_playwright

                with sync_playwright() as playwright:
                    executable = next(
                        (ROOT / ".browser-runtime").glob(
                            "chromium_headless_shell-*/chrome-linux/headless_shell"
                        ),
                        None,
                    )
                    if executable is None:
                        executable = next(
                            (ROOT / ".browser-runtime").glob(
                                "chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell"
                            )
                        )
                    browser = playwright.chromium.launch(
                        executable_path=str(executable),
                        headless=True,
                        chromium_sandbox=True,
                        env=browser_environment(temporary),
                    )
                    page = browser.new_page(viewport={"width": 1440, "height": 1000})
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto(base)
                    page.locator("#messageInput").wait_for(state="visible")
                    page.locator("#messageInput").fill(
                        "修复 calc.py 的加法，并运行 test_calc.py；不要改变测试断言。"
                    )
                    page.locator("#sendButton").click()
                    approvals = []
                    deadline = time.monotonic() + 45
                    run = None
                    restarted = False
                    while time.monotonic() < deadline:
                        runs = api("/api/runs")
                        if runs:
                            run = runs[-1]
                            pending = api(f"/api/runs/{run['id']}/approvals")
                            if pending:
                                if not restarted:
                                    from web.store import Store

                                    db = Store(Path(temporary) / ".ai-cli/web/workbench.sqlite")
                                    if not any(e["kind"] == "paused" for e in db.events(run["id"])):
                                        page.wait_for_timeout(100)
                                        continue
                                    server.terminate()
                                    server.wait(timeout=8)
                                    server = subprocess.Popen(
                                        [sys.executable, "-m", "web", "--port", str(port)],
                                        cwd=ROOT,
                                        env=environment,
                                        stdout=log,
                                        stderr=log,
                                    )
                                    for _ in range(100):
                                        try:
                                            api("/api/health")
                                            break
                                        except OSError:
                                            time.sleep(0.1)
                                    assert (
                                        api(f"/api/runs/{run['id']}")["status"]
                                        == "waiting_approval"
                                    )
                                    page.reload()
                                    restarted = True
                                page.get_by_role("button", name="允许", exact=True).first.wait_for()
                                page.get_by_role("button", name="允许", exact=True).first.click(
                                    timeout=5000
                                )
                                approvals.append(pending[0]["action"].splitlines()[0])
                            if run["status"] not in ("queued", "running", "waiting_approval"):
                                break
                        page.wait_for_timeout(150)
                    assert run and run["status"] == "succeeded", run
                    persisted = api(f"/api/sessions/{identifier}/messages")
                    results = [json.loads(m["content"]) for m in persisted if m["role"] == "tool"]
                    assert results[-1]["ok"] and results[-1]["exit_code"] == 0, results
                    assert "return a + b" in (project / "calc.py").read_text()
                    assert any(
                        "参考资料" in m.get("content", "") and "项目需求" in m.get("content", "")
                        for request in fixture.RequestHandlerClass.requests
                        for m in request["messages"]
                    ), "RAG 和记忆未进入实际协议请求"
                    snapshots = api(f"/api/sessions/{identifier}/git/snapshots")
                    baseline = next(item for item in snapshots if item["run_id"] == run["id"])
                    preview = api(
                        f"/api/sessions/{identifier}/git/restore-preview",
                        {"snapshot_id": baseline["id"], "path": "calc.py"},
                    )
                    assert "# 用户已有的说明" in preview["diff"]
                    page.wait_for_timeout(500)
                    page.screenshot(path=str(ROOT / "artifacts/web/workbench.png"), full_page=True)
                    page.reload()
                    page.get_by_text(
                        "夹具已完成；请以工具实际结果判断测试和修改。", exact=True
                    ).first.wait_for()
                    page.screenshot(path=str(ROOT / "artifacts/web/workbench.png"), full_page=True)
                    # 真实拒绝流程：先恢复夹具原文件，再发新任务拒绝写入。
                    original = "def add(a, b):\n    return a - b\n"
                    (project / "calc.py").write_text(original)
                    page.locator("#messageInput").fill("再次检查 calc.py，但本次我将拒绝修改")
                    page.locator("#sendButton").click()
                    page.get_by_role("button", name="拒绝", exact=True).first.wait_for()
                    page.get_by_role("button", name="拒绝", exact=True).first.click()
                    deadline = time.monotonic() + 15
                    rejected_run = None
                    while time.monotonic() < deadline:
                        latest = api("/api/runs")[-1]
                        if latest["id"] != run["id"] and latest["status"] not in (
                            "queued",
                            "running",
                            "waiting_approval",
                        ):
                            rejected_run = latest
                            break
                        page.wait_for_timeout(100)
                    assert rejected_run and (project / "calc.py").read_text() == original
                    rejected_messages = api(f"/api/sessions/{identifier}/messages")
                    rejected_results = [
                        json.loads(m["content"]) for m in rejected_messages if m["role"] == "tool"
                    ]
                    assert rejected_results[-1]["ok"] is False
                    # UI 恢复到任务前快照，验证用户原有 dirty 内容仍在。
                    page.locator('[data-tab="git"]').click()
                    page.get_by_role("button", name="手工快照", exact=True).wait_for()
                    card = page.locator(".git-snapshot").filter(has_text=baseline["id"])
                    card.get_by_label("快照中的文件相对路径").fill("calc.py")
                    card.get_by_role("button", name="预览恢复", exact=True).click()
                    page.locator("#gitRestorePreviewDiff").wait_for()
                    assert "# 用户已有的说明" in page.locator("#gitRestorePreviewDiff").inner_text()
                    page.locator("#confirmGitRestore").click()
                    page.locator("#gitRestoreModal").wait_for(state="hidden")
                    assert "# 用户已有的说明" in (project / "calc.py").read_text()
                    assert "return a - b" in (project / "calc.py").read_text()
                    # 恢复后仍是 dirty，而不是 HEAD；索引、提交没有被改写。
                    dirty = subprocess.run(
                        ["git", "diff", "--", "calc.py"],
                        cwd=project,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    assert "# 用户已有的说明" in dirty.stdout
                    page.screenshot(
                        path=str(ROOT / "artifacts/web/workbench-git.png"), full_page=True
                    )
                    # 通过模型工具创建真实沙箱 PTY，然后在另一个工具审批时确认仍存活。
                    page.locator("#messageInput").fill(
                        "持久后台测试：启动终端后提出修改，我会拒绝修改"
                    )
                    page.locator("#sendButton").click()
                    page.get_by_role("button", name="允许", exact=True).first.wait_for()
                    page.get_by_role("button", name="允许", exact=True).first.click()
                    deadline = time.monotonic() + 15
                    tasks = []
                    while time.monotonic() < deadline:
                        tasks = api(f"/api/sessions/{identifier}/tasks")["tasks"]
                        latest = api("/api/runs")[-1]
                        pending = api(f"/api/runs/{latest['id']}/approvals")
                        if tasks and pending and pending[0]["action"].startswith("edit_file"):
                            break
                        page.wait_for_timeout(100)
                    page.get_by_role("button", name="拒绝", exact=True).first.wait_for()
                    assert tasks and tasks[0]["state"] == "running", tasks
                    background_id = tasks[0]["task_id"]
                    live_background = api(f"/api/sessions/{identifier}/tasks/{background_id}")
                    assert live_background["state"] == "running", live_background
                    page.get_by_role("button", name="拒绝", exact=True).first.click()
                    deadline = time.monotonic() + 20
                    while time.monotonic() < deadline:
                        if api("/api/runs")[-1]["status"] == "succeeded":
                            break
                        page.wait_for_timeout(100)
                    assert (
                        api(f"/api/sessions/{identifier}/tasks/{background_id}")["state"]
                        == "running"
                    )
                    # 后续新请求走同一个统一 Runtime 查询服务级任务。
                    page.locator("#messageInput").fill("查询后台 " + background_id)
                    page.locator("#sendButton").click()
                    deadline = time.monotonic() + 20
                    while time.monotonic() < deadline:
                        latest = api("/api/runs")[-1]
                        if (
                            latest["message"].startswith("查询后台")
                            and latest["status"] == "succeeded"
                        ):
                            break
                        page.wait_for_timeout(100)
                    assert latest["status"] == "succeeded"
                    # 浏览器面板发送输入与取消，而非直接接管宿主终端。
                    page.locator('[data-tab="tasks"]').click()
                    page.get_by_label("发送终端输入到任务 " + background_id).fill("persisted\n")
                    page.get_by_role("button", name="确认并发送输入", exact=True).first.click()
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline:
                        background = api(f"/api/sessions/{identifier}/tasks/{background_id}")
                        if "BACKGROUND_INPUT persisted" in background["output"]:
                            break
                        page.wait_for_timeout(100)
                    assert "BACKGROUND_INPUT persisted" in background["output"], background
                    other = api("/api/sessions", {"title": "隔离验收", "workspace": str(project)})
                    assert api(f"/api/sessions/{other['id']}/tasks/{background_id}")["ok"] is False
                    page.get_by_role("button", name="取消任务", exact=True).last.click()
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline:
                        background = api(f"/api/sessions/{identifier}/tasks/{background_id}")
                        if background["state"] == "finished":
                            break
                        page.wait_for_timeout(100)
                    assert (
                        background["state"] == "finished" and background["reason"] == "cancelled"
                    ), background
                    page.locator("#messageInput").fill("AI终端交互验收")
                    page.locator("#sendButton").click()
                    deadline = time.monotonic() + 25
                    ai_approvals = []
                    seen_ai_approvals = set()
                    while time.monotonic() < deadline:
                        ai_run = api("/api/runs")[-1]
                        if ai_run["message"] == "AI终端交互验收":
                            pending = api(f"/api/runs/{ai_run['id']}/approvals")
                            if pending and pending[0]["id"] not in seen_ai_approvals:
                                assert pending[0]["action"].startswith("start_pty\n"), pending
                                page.get_by_role("button", name="允许", exact=True).first.click()
                                seen_ai_approvals.add(pending[0]["id"])
                                ai_approvals.append("start_pty")
                            if ai_run["status"] in ("succeeded", "failed"):
                                break
                        page.wait_for_timeout(100)
                    assert ai_run["status"] == "succeeded", ai_run
                    ai_messages = api(f"/api/sessions/{identifier}/messages")
                    latest_user = max(i for i, m in enumerate(ai_messages) if m["role"] == "user")
                    ai_results = [m for m in ai_messages[latest_user:] if m["role"] == "tool"]
                    assert [m["tool_name"] for m in ai_results] == [
                        "list_tasks",
                        "start_pty",
                        "task_input",
                        "task_wait",
                    ], ai_results
                    ai_status = json.loads(ai_results[-1]["content"])
                    assert (
                        ai_status["exit_code"] == 0
                        and "AI_INPUT_RESULT from-agent" in ai_status["output"]
                    ), ai_status
                    assert ai_approvals == ["start_pty"], ai_approvals
                    before_child = (project / "calc.py").read_text()
                    page.locator("#messageInput").fill("可写子代理UI验收")
                    page.locator("#sendButton").click()
                    deadline = time.monotonic() + 20
                    child_seen = set()
                    while time.monotonic() < deadline:
                        child_run = api("/api/runs")[-1]
                        if child_run["message"] == "可写子代理UI验收":
                            pending = api(f"/api/runs/{child_run['id']}/approvals")
                            if pending and pending[0]["id"] not in child_seen:
                                assert pending[0]["action"].startswith("spawn_agent\n")
                                page.get_by_role("button", name="允许", exact=True).first.click()
                                child_seen.add(pending[0]["id"])
                            if child_run["status"] == "succeeded":
                                break
                        page.wait_for_timeout(100)
                    assert child_run["status"] == "succeeded", child_run
                    messages = api(f"/api/sessions/{identifier}/messages")
                    spawn = next(
                        m for m in reversed(messages) if m.get("tool_name") == "spawn_agent"
                    )
                    child_id = json.loads(spawn["content"])["task_id"]
                    deadline = time.monotonic() + 15
                    while time.monotonic() < deadline:
                        child = api(f"/api/sessions/{identifier}/tasks/{child_id}")
                        child_pending = child.get("pending_approvals", [])
                        if child_pending:
                            break
                        page.wait_for_timeout(100)
                    assert child_pending, child
                    assert (project / "calc.py").read_text() == before_child
                    child_approval = child_pending[0]["id"]
                    assert (
                        api(
                            f"/api/sessions/{other['id']}/tasks/{child_id}/approvals/{child_approval}",
                            {"allow": True},
                        )["ok"]
                        is False
                    )
                    page.locator('[data-tab="tasks"]').click()
                    button = page.get_by_label("允许子代理修改 " + child_approval)
                    button.wait_for()
                    button.click()
                    deadline = time.monotonic() + 15
                    while time.monotonic() < deadline:
                        child = api(f"/api/sessions/{identifier}/tasks/{child_id}")
                        if child["state"] == "finished":
                            break
                        page.wait_for_timeout(100)
                    assert child["state"] == "finished" and child["agent_result"]["ok"], child
                    assert any(
                        o["tool"] == "edit_file" and o["changed"]
                        for o in child["agent_result"]["operations"]
                    ), child
                    assert "# child-edit" in (project / "calc.py").read_text()
                    # 真正 HTTP 错误来自夹具；确认诊断分类且响应体没有进入记录。
                    page.locator("#messageInput").fill("诊断失败测试")
                    page.locator("#sendButton").click()
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline:
                        diagnostic_run = api("/api/runs")[-1]
                        if (
                            diagnostic_run["message"] == "诊断失败测试"
                            and diagnostic_run["status"] == "failed"
                        ):
                            break
                        page.wait_for_timeout(100)
                    diagnostics = api(f"/api/runs/{diagnostic_run['id']}/diagnostics")
                    assert diagnostics[-1]["code"] == "service_unavailable", diagnostics
                    assert "sensitive response body" not in json.dumps(diagnostics)
                    page.locator(".run-diagnostic-suggestion").filter(
                        has_text="稍后重试；若持续失败，检查服务状态。"
                    ).first.wait_for()
                    page.screenshot(
                        path=str(ROOT / "artifacts/web/workbench-tasks.png"), full_page=True
                    )
                    assert not errors, errors
                    browser.close()
                report = {
                    "fixture_only": True,
                    "real_model_called": False,
                    "run_status": run["status"],
                    "approvals": approvals,
                    "test_exit_code": results[-1]["exit_code"],
                    "index_files": index["files"],
                    "unchanged_index_reused_chunks": reused_index["reused_chunks"],
                    "retrieval_sources": [hit["path"] for hit in hits],
                    "memory_saved": bool(memory["id"]),
                    "browser_errors": errors,
                    "refresh_history_restored": True,
                    "tool_messages": len(results),
                    "reference_sent_to_model_fixture": True,
                    "rejected_write_preserved_file": True,
                    "approval_survived_server_restart": restarted,
                    "completed_tools_not_replayed": len(
                        [m for m in persisted if m.get("tool_name") == "read_file"]
                    )
                    == 1,
                    "git_restore_preserved_preexisting_dirty_content": True,
                }
                report.update(
                    background_survived_run_and_approval=True,
                    background_query_next_run=True,
                    terminal_input_and_cancel=True,
                    background_session_isolation=True,
                    agent_completed_pty_interaction=True,
                    child_wrote_after_own_diff_approval=True,
                    child_main_run_finished_before_write=True,
                    structured_diagnostic_code=diagnostics[-1]["code"],
                    error_response_body_hidden=True,
                )
                (ROOT / "artifacts/web/acceptance.json").write_text(
                    json.dumps(report, ensure_ascii=False, indent=2)
                )
                print(json.dumps(report, ensure_ascii=False))
            except Exception:
                from web.store import Store

                db = Store(Path(temporary) / ".ai-cli/web/workbench.sqlite")
                for failed_run in db.list_runs():
                    print("DEBUG RUN", failed_run)
                    print("DEBUG EVENTS", db.events(failed_run["id"]))
                raise
            finally:
                server.terminate()
                try:
                    server.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()
                fixture.shutdown()


if __name__ == "__main__":
    main()
