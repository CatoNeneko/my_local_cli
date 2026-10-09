import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent
import history
import tool_runtime


@pytest.fixture
def conversation(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "HISTORY_PATH", tmp_path / "history.jsonl")
    monkeypatch.setattr(tool_runtime, "record_tool_event", Mock())
    messages = [{"role": "user", "content": "读取 sample.py"}]
    history.append_messages(messages)
    return messages


def tool_request(count=1):
    return {
        "role": "assistant", "content": "",
        "tool_calls": [{"function": {"name": "read_file", "arguments": {"path": "sample.py"}}} for _ in range(count)]
    }


def test_tool_content_survives_followup_and_reload(conversation, monkeypatch):
    responses = iter([tool_request(), {"role": "assistant", "content": "文件已读取"}])
    snapshots = []
    def respond(messages):
        snapshots.append(json.loads(json.dumps(messages)))
        return next(responses)
    monkeypatch.setattr(agent, "request_message", respond)
    monkeypatch.setattr(agent, "execute_tool", lambda *args: {"ok": True, "content": "answer = 42\n"})
    reply = agent.run_agent(conversation)
    final = {"role": "assistant", "content": reply}
    conversation.append(final)
    history.append_message(final)
    assert [m["role"] for m in conversation] == ["user", "assistant", "tool", "assistant"]
    assert json.loads(snapshots[1][-1]["content"])["content"] == "answer = 42\n"
    assert history.load_history() == conversation
    followup = history.load_history()
    followup.append({"role": "user", "content": "刚才文件的变量值是什么？"})
    def answer(messages):
        assert any(m["role"] == "tool" and "answer = 42" in m["content"] for m in messages)
        return {"role": "assistant", "content": "42"}
    monkeypatch.setattr(agent, "request_message", answer)
    assert agent.run_agent(followup) == "42"


def test_denial_is_persisted(conversation, monkeypatch):
    responses = iter([tool_request(), {"content": "用户拒绝"}])
    monkeypatch.setattr(agent, "request_message", lambda messages: next(responses))
    monkeypatch.setattr(agent, "execute_tool", lambda *args: {"ok": False, "error": "用户拒绝"})
    assert agent.run_agent(conversation) == "用户拒绝"
    assert history.load_history() == conversation
    assert json.loads(conversation[-1]["content"])["ok"] is False


def test_malformed_batch_never_partially_executes(conversation, monkeypatch):
    response = tool_request()
    response["tool_calls"].append({})
    monkeypatch.setattr(agent, "request_message", lambda messages: response)
    execute = Mock()
    monkeypatch.setattr(agent, "execute_tool", execute)
    assert "格式错误" in agent.run_agent(conversation)
    execute.assert_not_called()
    assert history.load_history() == conversation
    assert len(conversation) == 1


def test_budget_preserves_complete_results(conversation, monkeypatch):
    monkeypatch.setattr(agent, "request_message", lambda messages: tool_request(13))
    execute = Mock(return_value={"ok": False, "error": "模拟拒绝"})
    monkeypatch.setattr(agent, "execute_tool", execute)
    assert "总次数上限" in agent.run_agent(conversation)
    assert execute.call_count == 12
    assert len([m for m in conversation if m["role"] == "tool"]) == 13
    assert "工具未执行" in conversation[-1]["content"]
    assert history.load_history() == conversation


def test_exception_result_is_persisted(conversation, monkeypatch):
    responses = iter([tool_request(), {"content": "处理完成"}])
    monkeypatch.setattr(agent, "request_message", lambda messages: next(responses))
    monkeypatch.setattr(tool_runtime, "_execute_tool", Mock(side_effect=OSError("模拟异常")))
    assert agent.run_agent(conversation) == "处理完成"
    assert "OSError" in conversation[-1]["content"]
    assert history.load_history() == conversation


def test_plain_reply_is_not_saved_twice(conversation, monkeypatch):
    monkeypatch.setattr(agent, "request_message", lambda messages: {"content": "你好"})
    assert agent.run_agent(conversation) == "你好"
    assert len(conversation) == 1
    assert len(history.load_history()) == 1


def test_tool_history_validation(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "HISTORY_PATH", tmp_path / "history.jsonl")
    history.append_messages([
        {"role": "tool", "content": "missing name"},
        {"role": "tool", "tool_name": "read_file", "content": "valid"},
        {"role": "assistant", "content": "", "tool_calls": []}
    ])
    assert len(history.load_history()) == 2
