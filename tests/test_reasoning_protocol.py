"""OpenAI reasoning_content 字段的协议回归测试。"""

import io
import json

import pytest

import api_adapter
import context_window
import history
from config import model_config
from streaming import ModelResponseError


SENTINEL = "reasoning-protocol-sentinel"


@pytest.fixture
def openai_protocol(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "HISTORY_PATH", tmp_path / "history.jsonl")
    monkeypatch.setitem(model_config, "provider", "openai")
    monkeypatch.setitem(model_config, "model", "modelfixture")


@pytest.mark.parametrize("value", [SENTINEL, ""])
def test_normalize_preserves_string_reasoning_content(openai_protocol, value):
    message = api_adapter.normalize({"content": "answer", "reasoning_content": value})

    assert message["reasoning_content"] == value


def test_normalize_omits_null_reasoning_content(openai_protocol):
    message = api_adapter.normalize({"content": "answer", "reasoning_content": None})

    assert "reasoning_content" not in message


@pytest.mark.parametrize("value", [1, False, [], {}])
def test_normalize_rejects_non_string_reasoning_content(openai_protocol, value):
    with pytest.raises(ModelResponseError):
        api_adapter.normalize({"content": "answer", "reasoning_content": value})


def test_wire_messages_preserves_only_assistant_reasoning_content(openai_protocol):
    messages = [
        {"role": "user", "content": "question", "reasoning_content": SENTINEL},
        {"role": "assistant", "content": "earlier answer", "reasoning_content": SENTINEL},
        {
            "role": "assistant",
            "content": "",
            "reasoning_content": "",
            "tool_calls": [
                {
                    "id": "call-1",
                    "function": {"name": "read_file", "arguments": {"path": "sample.py"}},
                }
            ],
        },
        {
            "role": "tool",
            "content": "{}",
            "tool_name": "read_file",
            "tool_call_id": "call-1",
            "reasoning_content": SENTINEL,
        },
    ]

    wire = api_adapter.wire_messages(messages)

    assert wire[1]["reasoning_content"] == SENTINEL
    assert wire[2]["reasoning_content"] == ""
    assert "reasoning_content" not in wire[0]
    assert "reasoning_content" not in wire[3]


def _sse(value):
    return ("data: " + json.dumps(value) + "\n\n").encode()


def test_collect_sse_joins_reasoning_but_displays_only_content(openai_protocol):
    raw = (
        b"".join(
            _sse(value)
            for value in [
                {
                    "choices": [
                        {
                            "delta": {
                                "content": "visible ",
                                "reasoning_content": "reasoning-protocol-",
                            }
                        }
                    ]
                },
                {"choices": [{"delta": {"content": "text", "reasoning_content": "sentinel"}}]},
                {"choices": [{"delta": None, "finish_reason": "stop"}]},
            ]
        )
        + b"data: [DONE]\n\n"
    )
    displayed = []

    result = api_adapter.collect_sse(io.BytesIO(raw), 10000, displayed.append)

    assert result["reasoning_content"] == SENTINEL
    assert result["content"] == "visible text"
    assert displayed == ["visible ", "text"]


@pytest.mark.parametrize("value", [1, False, [], {}])
def test_collect_sse_rejects_non_string_reasoning_delta(openai_protocol, value):
    raw = (
        _sse({"choices": [{"delta": {"reasoning_content": value}, "finish_reason": "stop"}]})
        + b"data: [DONE]\n\n"
    )

    with pytest.raises(ModelResponseError):
        api_adapter.collect_sse(io.BytesIO(raw), 10000)


def test_collect_sse_still_requires_a_finish_reason(openai_protocol):
    raw = _sse({"choices": [{"delta": {"reasoning_content": SENTINEL}}]})
    raw += b"data: [DONE]\n\n"

    with pytest.raises(ModelResponseError, match="完成原因"):
        api_adapter.collect_sse(io.BytesIO(raw), 10000)


def test_collect_sse_disconnect_does_not_return_an_incomplete_tool(openai_protocol):
    raw = _sse(
        {
            "choices": [
                {
                    "delta": {
                        "reasoning_content": SENTINEL,
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "call-1",
                                "function": {"name": "read_file", "arguments": "{"},
                            }
                        ],
                    }
                }
            ]
        }
    )

    with pytest.raises(ModelResponseError):
        api_adapter.collect_sse(io.BytesIO(raw), 10000)


def test_history_round_trips_opaque_reasoning_content(openai_protocol):
    messages = [{"role": "assistant", "content": "answer", "reasoning_content": SENTINEL}]

    history.append_messages(messages)

    assert history.load_history() == messages


def test_openai_request_size_counts_reasoning_content(openai_protocol):
    messages = [{"role": "assistant", "content": "answer", "reasoning_content": SENTINEL * 8}]
    without_reasoning = [{"role": "assistant", "content": "answer"}]

    wire = api_adapter.wire_messages(messages)

    assert wire[0]["reasoning_content"] == SENTINEL * 8
    assert context_window.request_size(messages, []) > context_window.request_size(
        without_reasoning, []
    )


def test_run_agent_callback_keeps_full_assistant_and_legacy_return(monkeypatch):
    import agent

    response = {"role": "assistant", "content": "visible answer", "reasoning_content": SENTINEL}
    monkeypatch.setattr(agent, "request_message", lambda messages: dict(response))
    messages = [{"role": "user", "content": "question"}]
    final_messages = []

    reply = agent.run_agent(messages, on_final=final_messages.append)
    legacy_reply = agent.run_agent(messages)

    assert isinstance(reply, str)
    assert reply == legacy_reply == "visible answer"
    assert final_messages == [response]


def test_cli_saves_reasoning_in_temporary_workspace_without_displaying_it(
    tmp_path, monkeypatch, capsys
):
    import agent
    import script

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    class NoServices:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def load_configured(self):
            pytest.fail("MCP must be disabled")

    inputs = iter(["question", "/exit"])
    monkeypatch.setattr(script, "MCPManager", NoServices)
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    monkeypatch.setattr(
        agent,
        "request_message",
        lambda messages, **kwargs: {
            "role": "assistant",
            "content": "visible answer",
            "reasoning_content": SENTINEL,
        },
    )

    script.main(plain=True, no_mcp=True, workspace=workspace)

    saved = history.load_history(workspace / ".ai-cli" / "history.jsonl")
    output = capsys.readouterr().out
    assert saved[-1] == {
        "role": "assistant",
        "content": "visible answer",
        "reasoning_content": SENTINEL,
    }
    assert SENTINEL not in output


def test_web_graph_persists_reasoning_without_emitting_it(tmp_path, monkeypatch):
    from langgraph.checkpoint.sqlite import SqliteSaver

    import web.workflow as workflow
    from web.knowledge import KnowledgeStore
    from web.store import Store
    from web.workflow import build_graph

    store = Store(tmp_path / "state/workbench.sqlite")
    knowledge = KnowledgeStore(tmp_path / "state/knowledge.sqlite")
    session = store.create_session("reasoning", str(tmp_path))
    run = store.create_run(session["id"], "answer this")
    store.append_messages(session["id"], [{"role": "user", "content": run["message"]}])
    events = []

    def request(messages, *, on_content, **kwargs):
        on_content("visible answer")
        return {
            "role": "assistant",
            "content": "visible answer",
            "reasoning_content": SENTINEL,
        }

    monkeypatch.setattr(workflow, "request_message", request)
    monkeypatch.setattr("compaction.maybe_compact", lambda *args: None)
    with SqliteSaver.from_conn_string(str(tmp_path / "checkpoint.sqlite")) as saver:
        graph = build_graph(
            store,
            knowledge,
            run,
            session,
            lambda kind, payload: events.append((kind, payload)),
            saver,
        )
        result = graph.invoke(
            {"messages": store.messages(session["id"]), "rounds": 0, "tool_count": 0},
            {"configurable": {"thread_id": run["id"]}},
        )

    saved_assistant = store.messages(session["id"])[-1]
    emitted = json.dumps(events, ensure_ascii=False)
    assert saved_assistant == {
        "role": "assistant",
        "content": "visible answer",
        "reasoning_content": SENTINEL,
    }
    assert result["answer"] == "visible answer"
    assert [(kind, payload) for kind, payload in events if kind == "token"] == [
        ("token", {"text": "visible answer"})
    ]
    assert SENTINEL not in emitted
    assert SENTINEL not in result["answer"]
