import os

import pytest

import audit
import history
import permissions
import sandbox
import script
import tool_runtime
from project_instructions import instruction_state, load_project_instructions
from sessions import SessionManager
from workspace import APP_ROOT, use_workspace


def test_workspace_routes_tools_state_instructions_and_restores(tmp_path, monkeypatch):
    original = (
        permissions.PROJECT_ROOT,
        history.HISTORY_PATH,
        audit.LOG_PATH,
        sandbox.runtime_environment(),
    )
    (tmp_path / "AGENTS.md").write_text("外部项目规则")
    (tmp_path / "sample.py").write_text("value = 42")
    with use_workspace(tmp_path):
        assert permissions.PROJECT_ROOT == sandbox.PROJECT_ROOT == tmp_path
        assert sandbox.runtime_environment() == original[3]
        assert load_project_instructions()["status"] == "loaded"
        assert instruction_state["content"] == "外部项目规则"
        assert (
            tool_runtime.execute_tool("read_file", {"path": "sample.py"})["content"] == "value = 42"
        )
        assert not permissions.resolve_project_path(str(APP_ROOT / "config.py"))["ok"]
        history.append_message({"role": "user", "content": "external"})
        assert history.HISTORY_PATH == tmp_path / ".ai-cli/history.jsonl"
        assert audit.LOG_PATH == tmp_path / ".ai-cli/tool_events.jsonl"
        assert not permissions.resolve_project_path(".ai-cli/history.jsonl")["ok"]
        assert "value = 42" not in audit.LOG_PATH.read_text()
    assert (
        permissions.PROJECT_ROOT,
        history.HISTORY_PATH,
        audit.LOG_PATH,
        sandbox.runtime_environment(),
    ) == original


def test_project_histories_and_sessions_do_not_mix(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    for root, text in ((first, "one"), (second, "two")):
        with use_workspace(root):
            manager = SessionManager()
            assert manager.switch("work")["ok"]
            history.append_message({"role": "user", "content": text})
    with use_workspace(first):
        assert SessionManager().switch("work")["messages"][0]["content"] == "one"
    with use_workspace(second):
        assert SessionManager().switch("work")["messages"][0]["content"] == "two"


def test_invalid_workspace_and_symlinked_state_rejected(tmp_path):
    with pytest.raises(ValueError):
        with use_workspace(tmp_path / "missing"):
            pytest.fail("invalid root")
    (tmp_path / ".ai-cli").symlink_to(APP_ROOT)
    with pytest.raises(ValueError):
        with use_workspace(tmp_path):
            pytest.fail("symlinked state")


@pytest.mark.parametrize("invalid", [".ai-cli", ".ai-cli/history.jsonl", ".ai-cli/sessions"])
def test_invalid_state_types_rejected_before_startup(tmp_path, invalid):
    path = tmp_path / invalid
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.name == "history.jsonl":
        path.mkdir()
    else:
        path.write_text("invalid")
    with pytest.raises(ValueError):
        with use_workspace(tmp_path):
            pytest.fail("invalid state should not start")


def test_script_workspace_option_persists_only_selected_project(tmp_path, monkeypatch):
    class NoServices:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(script, "MCPManager", NoServices)
    inputs = iter(["hello", "/exit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    monkeypatch.setattr(script, "run_agent", lambda *args, **kwargs: "response")
    script.main(workspace=tmp_path, plain=True, no_mcp=True)
    assert [row["content"] for row in history.load_history(tmp_path / ".ai-cli/history.jsonl")] == [
        "hello",
        "response",
    ]


@pytest.mark.skipif(os.environ.get("CLI_SANDBOX_INTEGRATION") != "1", reason="外部项目真实沙箱")
def test_external_workspace_uses_assistant_runtime_in_real_sandbox(tmp_path, monkeypatch):
    (tmp_path / "test_external.py").write_text("def test_external():\n    assert 19 + 23 == 42\n")
    monkeypatch.setattr(permissions, "confirm_tool", lambda *args: True)
    with use_workspace(tmp_path):
        result = tool_runtime.execute_tool("run_tests", {"path": "test_external.py"})
        assert result["ok"], result
        assert "1 passed" in result["output"]
