from unittest.mock import Mock

import pytest

import permissions
import project_search
import tool_registry
import tool_runtime
import tools


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(permissions, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(tool_runtime, "record_tool_event", Mock())
    monkeypatch.setattr(permissions, "confirm_tool", Mock(return_value=False))
    monkeypatch.setattr(project_search, "search_config", dict(project_search.search_config))
    (tmp_path / "src").mkdir()
    (tmp_path / "src/a.py").write_text("first\nneedle in source\n", encoding="utf-8")
    (tmp_path / "notes.md").write_text("needle in notes\n")
    return tmp_path


def test_recursive_results_include_paths_lines_and_glob(project):
    result = tools.execute_tool("search_project", {"keyword": "needle", "glob": "*.py"})
    assert result["ok"] and result["matches"] == [
        {
            "path": "src/a.py",
            "line_number": 2,
            "content": "needle in source",
            "content_truncated": False,
        }
    ]
    assert not result["truncated"]
    permissions.confirm_tool.assert_not_called()
    tool_runtime.record_tool_event.assert_called_once()
    assert "search_project" in [
        entry["function"]["name"] for entry in tool_registry.get_tool_definitions()
    ]


def test_protected_paths_dependencies_and_symlinks_are_skipped(project):
    for directory in [".git", ".conda-env", "sessions", "node_modules"]:
        (project / directory).mkdir()
        (project / directory / "private.txt").write_text("needle secret")
    (project / ".env").write_text("needle secret")
    (project / "history.jsonl").write_text("needle secret")
    (project / "linked.py").symlink_to(project / "src/a.py")
    (project / "outside.py").symlink_to(project.parent / "outside.py")
    (project / "linked-directory").symlink_to(project / "src", target_is_directory=True)
    result = tools.search_project(".", "needle")
    assert {match["path"] for match in result["matches"]} == {"notes.md", "src/a.py"}
    assert result["skipped"]["protected_or_link"] >= 8


def test_non_text_large_and_long_lines_are_reported(project):
    (project / "invalid.bin").write_bytes(b"\xffneedle")
    (project / "binary.bin").write_bytes(b"needle\x00")
    (project / "large.txt").write_text("x" * 2000)
    (project / "long.txt").write_text("x" * 600 + "needle" + "y" * 600)
    project_search.search_config["max_file_bytes"] = 1500
    result = tools.search_project(".", "needle")
    assert result["skipped"]["non_text"] == 2 and result["skipped"]["large"] == 1
    long = next(match for match in result["matches"] if match["path"] == "long.txt")
    assert long["content_truncated"] and len(long["content"]) == 500 and "needle" in long["content"]


@pytest.mark.parametrize(
    "key,value",
    [("max_matches", 1), ("max_files", 1), ("max_total_bytes", 1), ("max_output_chars", 1)],
)
def test_limits_are_explicit_and_do_not_claim_complete_results(project, key, value):
    project_search.search_config[key] = value
    result = tools.search_project(".", "needle")
    assert result["ok"] and result["truncated"] and result["limit_reason"]


def test_timeout_returns_partial_status(project, monkeypatch):
    times = iter([0, 100])
    monkeypatch.setattr(project_search.time, "monotonic", lambda: next(times))
    result = tools.search_project(".", "needle")
    assert result["truncated"] and result["limit_reason"] == "搜索时间上限"


def test_literal_search_and_invalid_inputs(project):
    (project / "pattern.txt").write_text("a.b\naXb\nNEEDLE\n")
    result = tools.search_project(".", "a.b")
    assert [match["content"] for match in result["matches"]] == ["a.b"]
    assert not tools.search_project("../outside", "needle")["ok"]
    assert not tools.search_project("src/a.py", "needle")["ok"]
    assert not tools.search_project(".", "")["ok"]


def test_file_read_error_returns_warning_without_hiding_other_results(project, monkeypatch):
    original_open = open

    def fail_one(path, *args, **kwargs):
        if str(path).endswith("notes.md"):
            raise PermissionError("test")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(project_search, "open", fail_one, raising=False)
    result = tools.search_project(".", "needle")
    assert result["ok"] and result["warnings"] and result["skipped"]["unreadable"] == 1
    assert [match["path"] for match in result["matches"]] == ["src/a.py"]
