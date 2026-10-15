import io
import json
import pytest
from api_adapter import collect_sse, normalize, wire_messages
from streaming import ModelResponseError


def event(value):
    return ("data: " + json.dumps(value) + "\n\n").encode()


def test_fragmented_calls_and_history_ids():
    raw = event(
        {
            "choices": [
                {
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "abc",
                                "function": {"name": "read_file", "arguments": '{"pa'},
                            }
                        ]
                    }
                }
            ]
        }
    )
    raw += event(
        {
            "choices": [
                {
                    "delta": {
                        "tool_calls": [{"index": 0, "function": {"arguments": 'th":"a.py"}'}}]
                    },
                    "finish_reason": "tool_calls",
                }
            ]
        }
    )
    message = collect_sse(io.BytesIO(raw + b"data: [DONE]\n\n"), 10000)
    assert message["tool_calls"][0]["function"]["arguments"] == {"path": "a.py"}
    history = [
        message,
        {"role": "tool", "tool_name": "read_file", "tool_call_id": "abc", "content": "{}"},
    ]
    wire = wire_messages(history)
    assert wire[1]["tool_call_id"] == wire[0]["tool_calls"][0]["id"] == "abc"
    assert json.loads(wire[0]["tool_calls"][0]["function"]["arguments"]) == {"path": "a.py"}


@pytest.mark.parametrize("ending", [b"", b"data: [DONE]\n\n"])
def test_incomplete_stream_never_returns_calls(ending):
    raw = event(
        {
            "choices": [
                {
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "x",
                                "function": {"name": "read_file", "arguments": "{}"},
                            }
                        ]
                    }
                }
            ]
        }
    )
    with pytest.raises(ModelResponseError):
        collect_sse(io.BytesIO(raw + ending), 10000)


def test_old_ollama_history_gets_matching_ids():
    wire = wire_messages(
        [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "list_files", "arguments": {"path": "."}}}],
            },
            {"role": "tool", "tool_name": "list_files", "content": "{}"},
        ]
    )
    assert wire[0]["tool_calls"][0]["id"] == wire[1]["tool_call_id"]


@pytest.mark.parametrize("arguments", ["{", "[]", "null"])
def test_malformed_arguments(arguments):
    with pytest.raises(ModelResponseError):
        normalize(
            {"tool_calls": [{"id": "x", "function": {"name": "read_file", "arguments": arguments}}]}
        )


def test_authenticated_request_uses_env_and_no_redirect(monkeypatch):
    import model_client
    from config import model_config
    from unittest.mock import Mock

    monkeypatch.setitem(model_config, "provider", "openai")
    monkeypatch.setitem(model_config, "base_url", "https://example.invalid/v1/")
    monkeypatch.setitem(model_config, "api_key_env", "CLI_TEST_KEY")
    monkeypatch.setenv("CLI_TEST_KEY", "test-key")
    body = {"choices": [{"finish_reason": "stop", "message": {"content": "ok"}}]}

    class Response(io.BytesIO):
        pass

    opened = Mock(return_value=Response(json.dumps(body).encode()))
    monkeypatch.setattr(
        model_client.urllib.request,
        "build_opener",
        lambda handler: type("Opener", (), {"open": staticmethod(opened)})(),
    )
    assert (
        model_client.request_message(
            [{"role": "user", "content": "hello"}], use_tools=False, include_context=False
        )["content"]
        == "ok"
    )
    request = opened.call_args.args[0]
    assert request.full_url == "https://example.invalid/v1/chat/completions"
    assert request.get_header("Authorization") == "Bearer test-key"
    assert "tools" not in json.loads(request.data)
    assert "test-key" not in request.data.decode()
    with pytest.raises(ModelResponseError):
        model_client.NoAuthRedirect().redirect_request(
            request, None, 302, "", {}, "https://other.invalid"
        )
