import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import file_tools
import patches
import permissions
import sandbox
import tool_registry
import tool_runtime
import tools


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(permissions, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(sandbox, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(sandbox, "RUNTIME_ENV", Path(sys.prefix))
    monkeypatch.setattr(tool_runtime, "record_tool_event", Mock())
    monkeypatch.setattr(permissions, "confirm_tool", Mock(return_value=True))
    (tmp_path / "sample.py").write_text("value = 1\n", encoding="utf-8")
    return tmp_path


def arguments_for(name, path):
    if name in ("search_file", "search_project"):
        return {"path": path, "keyword": "value"}
    if name in ("edit_file", "create_skill", "create_file"):
        return {"path": path, "new_content": "value = 2\n"}
    if name == "start_pty":
        return {"path": path, "argv": ["python", "-V"]}
    if name == "spawn_agent":
        return {"path": path, "task": "分析代码"}
    return {"path": path}


@pytest.mark.parametrize("name", [name for name, spec in tool_registry.TOOL_REGISTRY.items() if spec.get("kind") != "task"])
def test_every_tool_rejects_escape_before_prompt(project, name):
    result = tools.execute_tool(name, arguments_for(name, "../outside.py"))
    assert not result["ok"] and "项目目录之外" in result["error"]
    permissions.confirm_tool.assert_not_called()
    tool_runtime.record_tool_event.assert_called_once()


@pytest.mark.parametrize("name", [name for name, spec in tool_registry.TOOL_REGISTRY.items() if spec.get("kind") != "task"])
def test_every_tool_rejects_private_paths(project, name):
    result = tools.execute_tool(name, arguments_for(name, ".git/private.py"))
    assert not result["ok"] and "私有记录" in result["error"]
    permissions.confirm_tool.assert_not_called()


def test_symlink_to_private_and_external_targets_is_blocked(project):
    private = project / ".git"
    private.mkdir()
    (private / "private.py").write_text("secret")
    (project / "alias.py").symlink_to(private / "private.py")
    assert not tools.read_file("alias.py")["ok"]
    assert not file_tools.read_file("alias.py")["ok"]
    (project / "outside.py").symlink_to(project.parent / "outside.py")
    assert not tools.read_file("outside.py")["ok"]
    permissions.confirm_tool.assert_not_called()


def test_manual_and_model_read_do_not_require_confirmation(project):
    permissions.confirm_tool.return_value = False
    assert tools.execute_tool("read_file", {"path": "sample.py"})["ok"]
    assert tools.read_file("sample.py")["content"] == "value = 1\n"
    permissions.confirm_tool.assert_not_called()
    assert tool_runtime.record_tool_event.call_count == 2


def test_model_cannot_supply_source_or_policy(project):
    for extra in ({"source": "user"}, {"operation": "read"}, {"approved": True}):
        result = tools.execute_tool("read_file", {"path": "sample.py", **extra})
        assert not result["ok"]
    permissions.confirm_tool.assert_not_called()


def test_unknown_source_or_missing_policy_never_prepares_or_executes(project, monkeypatch):
    spec = dict(tool_registry.TOOL_REGISTRY["edit_file"])
    prepare = Mock(side_effect=AssertionError("不能进入准备"))
    spec["prepare"] = prepare
    spec.pop("operation")
    monkeypatch.setitem(tool_registry.TOOL_REGISTRY, "edit_file", spec)
    assert not tools.execute_tool("edit_file", arguments_for("edit_file", "sample.py"))["ok"]
    assert not tools.execute_tool("read_file", {"path": "sample.py"}, source="unknown")["ok"]
    prepare.assert_not_called()
    permissions.confirm_tool.assert_not_called()


def test_edit_diff_precedes_one_confirmation_and_refusal_preserves_file(project, capsys):
    def refuse(*args):
        output = capsys.readouterr().out
        assert "-value = 1" in output and "+value = 2" in output
        return False
    permissions.confirm_tool.side_effect = refuse
    result = tools.execute_tool("edit_file", arguments_for("edit_file", "sample.py"))
    assert not result["ok"]
    assert (project / "sample.py").read_text() == "value = 1\n"
    permissions.confirm_tool.assert_called_once()
    tool_runtime.record_tool_event.assert_called_once()


def test_direct_edit_still_uses_gate_and_conflict_protection(project):
    def conflict(*args):
        (project / "sample.py").write_text("user changed\n")
        return True
    permissions.confirm_tool.side_effect = conflict
    assert not patches.edit_file("sample.py", "value = 2\n")["ok"]
    assert (project / "sample.py").read_text() == "user changed\n"
    permissions.confirm_tool.assert_called_once()


def test_accepted_edit_writes_once_and_logs_once(project):
    assert tools.execute_tool("edit_file", arguments_for("edit_file", "sample.py"))["ok"]
    assert (project / "sample.py").read_text() == "value = 2\n"
    permissions.confirm_tool.assert_called_once()
    tool_runtime.record_tool_event.assert_called_once()
    assert not list(project.glob(".cli-edit-*"))


def test_path_retargeted_during_confirmation_is_rejected(project):
    (project / "alias.py").symlink_to(project / "sample.py")
    def change(*args):
        (project / "alias.py").unlink()
        (project / "alias.py").symlink_to(project.parent / "outside.py")
        return True
    permissions.confirm_tool.side_effect = change
    assert not tools.execute_tool("edit_file", {"path": "alias.py", "new_content": "value = 2\n"})["ok"]


def test_invalid_parameters_do_not_prompt(project):
    for name, args in [
        ("read_file", {}), ("read_file", {"path": None}),
        ("search_file", {"path": "sample.py", "keyword": ""}),
        ("edit_file", {"path": "sample.py"}), ("run_tests", {"path": 3}),
        ("read_file", []), ("unknown", {})
    ]:
        assert not tools.execute_tool(name, args)["ok"]
    permissions.confirm_tool.assert_not_called()


def test_exception_and_bad_result_are_logged_once(project, monkeypatch):
    spec = dict(tool_registry.TOOL_REGISTRY["read_file"])
    spec["handler"] = Mock(side_effect=OSError("模拟故障"))
    monkeypatch.setitem(tool_registry.TOOL_REGISTRY, "read_file", spec)
    result = tools.execute_tool("read_file", {"path": "sample.py"})
    assert not result["ok"] and "OSError" in result["error"]
    tool_runtime.record_tool_event.assert_called_once()
    tool_runtime.record_tool_event.reset_mock()
    spec["handler"] = lambda **args: {"ok": "false"}
    assert not tools.execute_tool("read_file", {"path": "sample.py"})["ok"]
    tool_runtime.record_tool_event.assert_called_once()


def test_directory_listing_hides_private_entries(project):
    (project / ".git").mkdir()
    (project / ".env").write_text("secret")
    (project / "history.jsonl").write_text("private history")
    result = tools.list_files(".")
    assert result["ok"] and [entry["name"] for entry in result["entries"]] == ["sample.py"]


def test_test_execution_confirms_once_after_preflight(project, monkeypatch):
    (project / "test_example.py").write_text("def test_example(): pass\n")
    runner = Mock(return_value={"exit_code": 0, "output": "passed", "timed_out": False, "output_limit_exceeded": False})
    monkeypatch.setattr(sandbox, "collect_output", runner)
    assert sandbox.run_tests("test_example.py")["ok"]
    runner.assert_called_once()
    permissions.confirm_tool.assert_called_once()
    tool_runtime.record_tool_event.assert_called_once()


def test_registry_drives_model_definitions(project):
    definitions = tools.get_tool_definitions()
    assert {d["function"]["name"] for d in definitions} == set(tool_registry.TOOL_REGISTRY)
    definitions[0]["function"]["parameters"]["properties"].clear()
    assert tool_registry.TOOL_REGISTRY["read_file"]["parameters"]["properties"]
