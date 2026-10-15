import os
from unittest.mock import Mock
import pytest
import permissions
import sandbox
import tool_runtime
from harness.tasks import runtime as tasks, processes


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(permissions, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(sandbox, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(permissions, "confirm_tool", Mock(return_value=True))
    monkeypatch.setattr(tool_runtime, "record_tool_event", Mock())
    yield tmp_path
    tasks.close_tasks()


def test_unknown_task_rejected_before_confirmation(project):
    for name in ("task_status", "task_input", "task_cancel", "task_wait"):
        args = {"task_id": "missing"}
        if name == "task_input":
            args["text"] = "hello"
        assert not tool_runtime.execute_tool(name, args)["ok"]
    permissions.confirm_tool.assert_not_called()


def test_model_can_discover_tasks_without_manual_prompt(project):
    result = tool_runtime.execute_tool("list_tasks", {})
    assert result["ok"] and result["tasks"] == []
    permissions.confirm_tool.assert_not_called()


def test_owned_pty_input_and_cancel_do_not_prompt_again(project, monkeypatch):
    from config import approval_config
    from approval import authorize_action

    monkeypatch.setitem(approval_config, "mode", "manual")
    processes.JOBS["owned"] = {"kind": "pty"}
    try:
        for name in ("task_input", "task_cancel"):
            assert authorize_action(name, "execute", "owned", "model")["ok"]
        permissions.confirm_tool.assert_not_called()
    finally:
        processes.JOBS.pop("owned")


def test_start_denial_does_not_launch(project, monkeypatch):
    permissions.confirm_tool.return_value = False
    launch = Mock(side_effect=AssertionError("不得启动"))
    monkeypatch.setattr(processes, "launch", launch)
    assert not tool_runtime.execute_tool("start_pty", {"argv": ["python", "-V"]})["ok"]
    assert not tool_runtime.execute_tool("spawn_agent", {"task": "分析"})["ok"]
    launch.assert_not_called()


@pytest.mark.skipif(os.environ.get("CLI_SANDBOX_INTEGRATION") != "1", reason="需要真实 Linux 沙箱")
def test_real_pty_input_readonly_and_no_secrets(project):
    code = "import os; print('TTY',os.isatty(0),os.isatty(1),flush=True); print('INPUT',input(),flush=True); print('SECRET',os.getenv('CLI_HOST_SECRET')); open('/workspace/forbidden','w')"
    result = tool_runtime.execute_tool("start_pty", {"argv": ["python", "-u", "-c", code]})
    assert result["ok"]
    identifier = result["task_id"]
    assert tool_runtime.execute_tool("task_input", {"task_id": identifier, "text": "hello\n"})["ok"]
    output = tasks.wait_task(identifier, 5)
    assert output["state"] == "finished"
    assert "TTY True True" in output["output"]
    assert "INPUT hello" in output["output"]
    assert "SECRET None" in output["output"]
    assert not (project / "forbidden").exists()
    assert output["exit_code"] != 0


@pytest.mark.skipif(os.environ.get("CLI_SANDBOX_INTEGRATION") != "1", reason="需要真实 Linux 沙箱")
def test_real_timeout_cancel_and_output_limit(project):
    first = tool_runtime.execute_tool(
        "start_pty", {"argv": ["python", "-c", "import time; time.sleep(20)"], "timeout": 1}
    )
    result = tasks.wait_task(first["task_id"], 5)
    assert result["reason"] == "timeout" and result["state"] == "finished"
    second = tool_runtime.execute_tool(
        "start_pty", {"argv": ["python", "-c", "import time; time.sleep(20)"]}
    )
    result = tool_runtime.execute_tool("task_cancel", {"task_id": second["task_id"]})
    assert result["reason"] == "cancelled" and result["state"] == "finished"
    third = tool_runtime.execute_tool("start_pty", {"argv": ["python", "-c", "print('x'*100000)"]})
    result = tasks.wait_task(third["task_id"], 5)
    assert result["reason"] == "output_limit"
    assert len(processes.JOBS[third["task_id"]]["output"]) <= processes.MAX_OUTPUT


@pytest.mark.skipif(os.environ.get("CLI_SANDBOX_INTEGRATION") != "1", reason="需要真实 Linux 沙箱")
def test_pty_has_controlling_terminal_and_ctrl_c(project):
    import time

    code = (
        "import os,time; print('CONTROL',os.tcgetpgrp(0)==os.getpgrp(),flush=True); time.sleep(20)"
    )
    started = tool_runtime.execute_tool("start_pty", {"argv": ["python", "-u", "-c", code]})
    identifier = started["task_id"]
    for _ in range(50):
        if "CONTROL True" in tasks.inspect_task(identifier)["output"]:
            break
        time.sleep(0.02)
    assert "CONTROL True" in tasks.inspect_task(identifier)["output"]
    assert tasks.send_input(identifier, "\x03")["ok"]
    finished = tasks.wait_task(identifier, 5)
    assert finished["state"] == "finished"
    assert finished["exit_code"] != 0


@pytest.mark.skipif(
    os.environ.get("CLI_TERMINAL_INTEGRATION") != "1", reason="需要本地 HTTP 服务及真实工作进程"
)
def test_subagent_isolated_config_and_rejected_write_preserves_file(project, monkeypatch):
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from config import model_config

    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(data)
            if not any(message["role"] == "tool" for message in data["messages"]):
                message = {
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "deny",
                            "function": {
                                "name": "create_file",
                                "arguments": json.dumps(
                                    {"path": "forbidden.txt", "new_content": "bad"}
                                ),
                            },
                        }
                    ],
                }
                reason = "tool_calls"
            else:
                assert json.loads(data["messages"][-1]["content"])["ok"] is False
                message, reason = {"content": "write denied"}, "stop"
            encoded = json.dumps(
                {"choices": [{"message": message, "finish_reason": reason}]}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setitem(model_config, "provider", "openai")
    monkeypatch.setitem(model_config, "base_url", f"http://127.0.0.1:{server.server_port}/v1")
    monkeypatch.setitem(model_config, "api_key_env", "CLI_UNUSED_TEST_KEY")
    monkeypatch.setitem(model_config, "model", "snapshot-model")
    try:
        jobs = [tool_runtime.execute_tool("spawn_agent", {"task": "analyze"}) for _ in range(2)]
        model_config["model"] = "changed-parent"
        for job in jobs:
            import time

            deadline = time.monotonic() + 10
            pending = []
            while time.monotonic() < deadline:
                pending = tasks.inspect_task(job["task_id"]).get("pending_approvals", [])
                if pending:
                    break
                time.sleep(0.05)
            assert pending
            assert tasks.resolve_task_approval(job["task_id"], pending[0]["id"], False)["ok"]
            result = tasks.wait_task(job["task_id"], 10)
            assert result["agent_result"]["reply"] == "write denied"
        assert len(requests) == 4
        assert all(data["model"] == "snapshot-model" for data in requests)
        names = [{tool["function"]["name"] for tool in data["tools"]} for data in requests]
        assert all(
            {"read_file", "edit_file", "create_file", "run_tests", "start_pty", "propose_edit"}
            <= available
            for available in names
        )
        assert all("spawn_agent" not in available for available in names)
        assert not (project / "forbidden.txt").exists()
    finally:
        server.shutdown()
        server.server_close()


def test_launch_payload_failure_reaps_process_and_removes_job(project, monkeypatch):
    process = Mock(pid=999999)
    process.stdin.write.side_effect = BrokenPipeError
    process.stdout.fileno.return_value = 123
    monkeypatch.setattr(processes.subprocess, "Popen", Mock(return_value=process))
    kill = Mock()
    monkeypatch.setattr(processes, "_kill", kill)
    with pytest.raises(BrokenPipeError):
        processes.launch(
            ["trusted-worker"], payload={"task": "test", "workspace": str(project)}, kind="agent"
        )
    assert not processes.JOBS
    process.wait.assert_called_once()
    process.stdout.close.assert_called_once()
    kill.assert_called_once()


def test_cancel_finished_job_preserves_result_without_signalling(project, monkeypatch):
    process = Mock()
    process.poll.return_value = 0
    processes.JOBS["finished"] = {
        "process": process,
        "done": True,
        "kind": "pty",
        "output": b"complete",
        "reason": "",
        "lock": __import__("threading").RLock(),
    }
    kill = Mock(side_effect=AssertionError("结束任务不应再次发送信号"))
    monkeypatch.setattr(processes, "_kill", kill)
    result = tasks.cancel_task("finished")
    assert result["state"] == "finished" and result["reason"] == "" and result["exit_code"] == 0
    kill.assert_not_called()


def test_invalid_worker_payload_never_starts_process(project, monkeypatch):
    start = Mock(side_effect=AssertionError("无效数据不能启动进程"))
    monkeypatch.setattr(processes.subprocess, "Popen", start)
    with pytest.raises(ValueError):
        processes.launch(["trusted-worker"], payload={"task": "missing workspace"}, kind="agent")
    start.assert_not_called()
