import os
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import permissions
import sandbox
import tools
import tool_runtime


@pytest.fixture
def isolated_project(tmp_path, monkeypatch):
    monkeypatch.setattr(permissions, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(sandbox, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(permissions, "confirm_tool", lambda *args: True)
    monkeypatch.setattr(tool_runtime, "record_tool_event", Mock())
    return tmp_path


def test_reject_before_confirm(isolated_project, monkeypatch):
    confirm = Mock(side_effect=AssertionError("不应进入确认"))
    monkeypatch.setattr(permissions, "confirm_tool", confirm)
    for path in ("../outside.py", "missing.py", [], ""):
        assert not sandbox.run_tests(path)["ok"]
    confirm.assert_not_called()


def test_rejection_never_starts_process(isolated_project, monkeypatch):
    (isolated_project / "test_demo.py").write_text("def test_demo(): pass\n")
    monkeypatch.setattr(permissions, "confirm_tool", lambda *args: False)
    runner = Mock(side_effect=AssertionError("拒绝后不得启动"))
    monkeypatch.setattr(sandbox, "collect_output", runner)
    assert not tools.execute_tool("run_tests", {"path": "test_demo.py"})["ok"]
    runner.assert_not_called()


def test_missing_bwrap_has_no_fallback(isolated_project, monkeypatch):
    monkeypatch.setattr(sandbox.shutil, "which", lambda name: None)
    runner = Mock(side_effect=AssertionError("不能回退"))
    monkeypatch.setattr(sandbox, "collect_output", runner)
    assert not sandbox.run_tests(".")["ok"]
    runner.assert_not_called()


def test_command_is_fixed_argv(isolated_project):
    target = isolated_project / "test_a;echo.py"
    command = sandbox.build_test_command(target, "/usr/bin/bwrap")
    assert "--unshare-net" in command
    assert "--clearenv" in command
    assert command[-1] == "/workspace/test_a;echo.py"
    limited = command[command.index("--") + 1 :]
    assert limited[:3] == ["/usr/bin/python3", "-I", "-c"]
    assert limited[3] == sandbox.LIMIT_BOOTSTRAP
    assert limited[5:] == [
        "/runtime/bin/python",
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "--",
        "/workspace/test_a;echo.py",
    ]
    assert "--ro-bind" in command
    assert not any(item in command for item in ("sh", "bash"))


def test_output_and_time_bounds():
    result = sandbox.collect_output(
        [
            sys.executable,
            "-c",
            "import os; os.write(1, b'x' * 100000); import time; time.sleep(10)",
        ],
        3,
        1024,
    )
    assert result["output_limit_exceeded"]
    assert len(result["output"]) == 1024
    result = sandbox.collect_output(
        [sys.executable, "-c", "import time; time.sleep(10)"], 0.2, 1024
    )
    assert result["timed_out"]
    assert result["exit_code"] != 0


integration = pytest.mark.skipif(
    os.environ.get("CLI_SANDBOX_INTEGRATION") != "1",
    reason="真实 bubblewrap 集成测试需显式设置 CLI_SANDBOX_INTEGRATION=1",
)


@integration
def test_real_sandbox_boundaries(isolated_project):
    file = isolated_project / "test_boundaries.py"
    source = """import os
import socket
from pathlib import Path
import pytest

def test_boundaries():
    assert not Path("/home/perrylong").exists()
    assert "CLI_HOST_SECRET" not in os.environ
    with pytest.raises(OSError):
        Path("/workspace/should_not_write.py").write_text("x")
    with pytest.raises(OSError):
        Path("/usr/should_not_write").write_text("x")
    Path("/tmp/scratch").write_text("temporary")
    try:
        visible_history = Path("/workspace/history.jsonl").read_text()
    except PermissionError:
        pass
    else:
        assert visible_history == ""
    assert list(Path("/workspace/.git").iterdir()) == []
    try:
        nested_secret = Path("/workspace/sub/.env").read_text()
    except PermissionError:
        pass
    else:
        assert nested_secret == ""
    with socket.socket() as connection:
        connection.settimeout(1)
        with pytest.raises(OSError):
            connection.connect(("127.0.0.1", 11434))
"""
    file.write_text(source)
    (isolated_project / "history.jsonl").write_text("private history")
    (isolated_project / "sub").mkdir()
    (isolated_project / "sub" / ".env").write_text("nested private environment")
    (isolated_project / ".git").mkdir()
    (isolated_project / ".git" / "secret").write_text("private metadata")
    result = sandbox.run_tests("test_boundaries.py")
    assert result["ok"], result
    assert result["exit_code"] == 0 and "1 passed" in result["output"]
    assert file.read_text() == source
    assert not (isolated_project / "should_not_write.py").exists()


@integration
def test_real_test_failure(isolated_project):
    (isolated_project / "test_fail.py").write_text("def test_failure():\n    assert 1 == 2\n")
    result = sandbox.run_tests("test_fail.py")
    assert not result["ok"]
    assert result["exit_code"] == 1
    assert "1 failed" in result["output"]


@integration
def test_real_timeout(isolated_project, monkeypatch):
    (isolated_project / "test_slow.py").write_text(
        "import time\ndef test_slow():\n    time.sleep(20)\n"
    )
    monkeypatch.setitem(sandbox.sandbox_config, "timeout_seconds", 1)
    result = sandbox.run_tests("test_slow.py")
    assert not result["ok"] and result["timed_out"]


@integration
def test_real_output_limit(isolated_project, monkeypatch):
    (isolated_project / "test_output.py").write_text(
        "import os\ndef test_output():\n    os.write(1, b'x' * 200000)\n    assert False\n"
    )
    monkeypatch.setitem(sandbox.sandbox_config, "max_output_bytes", 1024)
    result = sandbox.run_tests("test_output.py")
    assert not result["ok"] and result["output_limit_exceeded"]
    assert result["output_truncated"]


@integration
def test_broken_sandbox_does_not_run_host(isolated_project, monkeypatch):
    (isolated_project / "test_example.py").write_text("def test_example(): pass\n")
    monkeypatch.setattr(sandbox.shutil, "which", lambda name: "/usr/bin/false")
    result = sandbox.run_tests("test_example.py")
    assert not result["ok"] and result["exit_code"] == 1
