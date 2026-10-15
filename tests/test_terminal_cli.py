import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import agent
import cli
import history
import script
import terminal_input
from command_help import COMMANDS, show_help
from console_output import ConsoleOutput


def test_startup_flags_and_help_exit_without_loading_services(capsys):
    parser = cli.build_parser()
    args = parser.parse_args(["--session", "work", "--plain", "--no-mcp", "--model", "test"])
    assert args.session == "work" and args.plain and args.no_mcp and args.model == "test"
    with pytest.raises(SystemExit) as error:
        cli.main(["--help"])
    assert error.value.code == 0
    assert "--no-mcp" in capsys.readouterr().out


def test_plain_mode_uses_input_and_help_contains_commands(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt: "hello")
    assert terminal_input.TerminalInput(plain=True).read("work") == "hello"
    show_help()
    help_text = capsys.readouterr().out
    assert all(name in help_text for name in COMMANDS)


def test_non_tty_uses_plain_input(monkeypatch):
    monkeypatch.setattr(terminal_input.sys, "stdin", SimpleNamespace(isatty=lambda: False))
    monkeypatch.setattr("builtins.input", lambda prompt: "pipe text")
    terminal = terminal_input.TerminalInput()
    assert terminal.session is None and terminal.read("default") == "pipe text"


def test_completion_lists_matching_commands():
    from prompt_toolkit.completion import CompleteEvent, WordCompleter
    from prompt_toolkit.document import Document

    completer = WordCompleter(list(COMMANDS), sentence=True)
    choices = {entry.text for entry in completer.get_completions(Document("/se"), CompleteEvent())}
    assert {"/session", "/sessions", "/session rename"} <= choices


@pytest.mark.skipif(
    os.environ.get("CLI_TERMINAL_INTEGRATION") != "1", reason="宿主环境验证真实输入应用"
)
def test_alt_enter_newline_enter_submit_with_real_prompt_application():
    from prompt_toolkit import PromptSession
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput

    with create_pipe_input() as pipe:
        session = PromptSession(
            input=pipe,
            output=DummyOutput(),
            multiline=True,
            key_bindings=terminal_input.create_key_bindings(),
        )
        pipe.send_text("first line\x1b\rsecond line\r")
        assert session.prompt("> ") == "first line\nsecond line"


def test_cancel_chat_generation_keeps_history_and_next_request_works(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "HISTORY_PATH", tmp_path / "history.jsonl")
    messages = [{"role": "user", "content": "first"}]
    history.append_messages(messages)
    request = Mock(side_effect=[KeyboardInterrupt, {"content": "second completed"}])
    monkeypatch.setattr(agent, "request_message", request)
    execute = Mock()
    monkeypatch.setattr(agent, "execute_tool", execute)
    result = agent.run_agent(messages, output=ConsoleOutput())
    assert "已取消" in result
    execute.assert_not_called()
    assert history.load_history() == messages
    messages.append({"role": "assistant", "content": result})
    messages.append({"role": "user", "content": "second"})
    assert agent.run_agent(messages, output=ConsoleOutput()) == "second completed"


def test_cli_cancellation_returns_to_input_and_saves_complete_diagnostic(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(history, "HISTORY_PATH", tmp_path / "history.jsonl")

    class NoServices:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def load_configured(self):
            pytest.fail("MCP must be disabled")

    monkeypatch.setattr(script, "MCPManager", NoServices)
    inputs = iter(["first", "second", "/help", "/exit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    monkeypatch.setattr(
        agent, "request_message", Mock(side_effect=[KeyboardInterrupt, {"content": "finished"}])
    )
    script.main(plain=True, no_mcp=True)
    messages = history.load_history()
    assert [message["role"] for message in messages] == ["user", "assistant", "user", "assistant"]
    assert "已取消" in messages[1]["content"] and messages[3]["content"] == "finished"
    assert "finished" in capsys.readouterr().out


def test_startup_session_and_disabled_mcp_refresh(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(history, "HISTORY_PATH", tmp_path / "history.jsonl")

    class NoServices:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def load_configured(self):
            pytest.fail("MCP must be disabled")

    monkeypatch.setattr(script, "MCPManager", NoServices)
    inputs = iter(["/session", "/mcp refresh", "/exit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    script.main(initial_session="work", plain=True, no_mcp=True)
    assert history.HISTORY_PATH == tmp_path / "sessions/work.jsonl"
    assert "--no-mcp" in capsys.readouterr().out


def test_user_can_switch_approval_mode_without_model_request(tmp_path, monkeypatch, capsys):
    from config import approval_config

    monkeypatch.setitem(approval_config, "mode", "manual")
    monkeypatch.setattr(history, "HISTORY_PATH", tmp_path / "history.jsonl")

    class NoServices:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(script, "MCPManager", NoServices)
    generate = Mock(side_effect=AssertionError("审批命令不能发送模型请求"))
    monkeypatch.setattr(script, "run_agent", generate)
    inputs = iter(
        ["/approval", "/approval auto", "/approval bad-mode", "/approval manual", "/exit"]
    )
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    script.main(plain=True, no_mcp=True)
    assert approval_config["mode"] == "manual"
    text = capsys.readouterr().out
    assert "审批模式已切换: auto" in text and "审批模式已切换: manual" in text
    assert "用法: /approval" in text
    generate.assert_not_called()
    assert history.load_history() == []
