import json
import os
import signal
import sys
import threading
from unittest.mock import Mock

import pytest

import agent
import history
import permissions
import sandbox
import skill_generation
import tool_registry
import tool_runtime
from context_window import prepare_context


def test_runtime_interrupt_returns_cancelled_and_audits_once(monkeypatch):
    spec = dict(tool_registry.TOOL_REGISTRY["read_file"])
    spec["handler"] = Mock(side_effect=KeyboardInterrupt)
    monkeypatch.setitem(tool_registry.TOOL_REGISTRY, "read_file", spec)
    audit = Mock()
    monkeypatch.setattr(tool_runtime, "record_tool_event", audit)
    result = tool_runtime.execute_tool("read_file", {"path": "sample.py"})
    assert not result["ok"] and result["cancelled"]
    audit.assert_called_once()


def test_agent_cancellation_stops_batch_and_preserves_complete_chain(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "HISTORY_PATH", tmp_path / "history.jsonl")
    messages = [{"role": "user", "content": "do work"}]
    history.append_messages(messages)
    calls = [
        {"function": {"name": "read_file", "arguments": {"path": "sample.py"}}} for _ in range(3)
    ]
    request = Mock(side_effect=[{"content": "", "tool_calls": calls}, {"content": "next works"}])
    execute = Mock(
        side_effect=[
            {"ok": True, "content": "done"},
            {"ok": False, "cancelled": True, "error": "cancelled"},
        ]
    )
    monkeypatch.setattr(agent, "request_message", request)
    monkeypatch.setattr(agent, "execute_tool", execute)
    reply = agent.run_agent(messages)
    assert "已取消当前任务" in reply and execute.call_count == 2
    results = [json.loads(row["content"]) for row in messages if row["role"] == "tool"]
    assert results[0]["ok"] and results[1]["cancelled"] and results[2]["cancelled"]
    assert history.load_history() == messages
    messages.append({"role": "assistant", "content": reply})
    messages.append({"role": "user", "content": "next"})
    assert prepare_context(messages, [])["sent_turns"] == 2
    assert agent.run_agent(messages) == "next works"


def test_skill_generation_cancellation_returns_result(tmp_path, monkeypatch):
    monkeypatch.setattr(permissions, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(skill_generation, "request_message", Mock(side_effect=KeyboardInterrupt))
    result = skill_generation.generate_skill("example", "review")
    assert not result["ok"] and result["cancelled"]
    assert not (tmp_path / "skills").exists()


@pytest.mark.skipif(
    os.environ.get("CLI_SANDBOX_INTEGRATION") != "1", reason="真实 SIGINT 与进程组清理"
)
def test_sigint_cancels_and_reaps_test_process(tmp_path):
    pid_log = tmp_path / "pid.txt"
    code = (
        "import os,time; from pathlib import Path; Path("
        + repr(str(pid_log))
        + ").write_text(str(os.getpid())); time.sleep(30)"
    )
    timer = threading.Timer(0.4, os.kill, args=(os.getpid(), signal.SIGINT))
    timer.start()
    try:
        result = sandbox.collect_output([sys.executable, "-c", code], 20, 10000)
    finally:
        timer.cancel()
        timer.join()
    assert result["cancelled"] and not result["timed_out"]
    with pytest.raises(ProcessLookupError):
        os.kill(int(pid_log.read_text()), 0)
