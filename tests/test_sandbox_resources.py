import json
import signal
import subprocess
import sys

import pytest

import sandbox
from config import sandbox_config


def run_limited(code, **changes):
    limits = sandbox.resource_limits()
    limits.update(changes)
    return subprocess.run(
        sandbox.limited_program([sys.executable, "-c", code], limits),
        capture_output=True,
        text=True,
        timeout=6,
    )


@pytest.mark.parametrize("value", [False, 0, -1, "256", None])
def test_invalid_resource_config_refused(value, monkeypatch):
    monkeypatch.setitem(sandbox_config, "open_files", value)
    with pytest.raises(ValueError):
        sandbox.resource_limits()


def test_limits_inherited_and_hard_limit_cannot_be_raised():
    code = """import resource,subprocess,sys,json
assert resource.getrlimit(resource.RLIMIT_CORE)==(0,0)
try:
    resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
except (ValueError,PermissionError):
    pass
else:
    raise AssertionError('hard limit raised')
print(subprocess.check_output([sys.executable,'-c',
    'import resource,json; print(json.dumps(resource.getrlimit(resource.RLIMIT_NOFILE)))']).decode())
"""
    result = run_limited(code, RLIMIT_NOFILE=32)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == [32, 32]


def test_address_space_rejects_large_allocation():
    result = run_limited(
        "try:\n x=bytearray(128*1024*1024)\nexcept MemoryError:\n print('memory-limited')",
        RLIMIT_AS=96 * 1024 * 1024,
    )
    assert result.returncode == 0, result.stderr
    assert "memory-limited" in result.stdout


def test_open_files_limit_rejects_extra_descriptors():
    result = run_limited(
        "import os\nfiles=[]\ntry:\n while True: files.append(os.open('/dev/null',os.O_RDONLY))\nexcept OSError as e:\n assert e.errno==24\n print('fd-limited')",
        RLIMIT_NOFILE=32,
    )
    assert result.returncode == 0, result.stderr
    assert "fd-limited" in result.stdout


def test_single_file_limit(tmp_path):
    target = tmp_path / "limited-file"
    code = f"""import os,signal
signal.signal(signal.SIGXFSZ,signal.SIG_IGN)
try:
 with open({str(target)!r},'wb',buffering=0) as file:
  file.write(b'x'*4096)
  file.write(b'x')
except OSError as error:
 assert error.errno==27
 print('file-limited')
"""
    result = run_limited(code, RLIMIT_FSIZE=1024)
    assert result.returncode == 0, result.stderr
    assert "file-limited" in result.stdout
    assert target.stat().st_size <= 1024


def test_cpu_loop_stopped_by_kernel():
    result = run_limited("while True: pass", RLIMIT_CPU=2)
    assert result.returncode in (-signal.SIGXCPU, -signal.SIGKILL), result


def test_pty_and_tests_share_resource_bootstrap(tmp_path, monkeypatch):
    from harness.tasks.runtime import prepare_pty
    import permissions

    monkeypatch.setattr(permissions, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(sandbox, "PROJECT_ROOT", tmp_path)
    prepared = prepare_pty(".", ["python", "-c", "print(1)"])
    assert prepared["ok"], prepared
    command = prepared["command"]
    assert command.count(sandbox.LIMIT_BOOTSTRAP) == 1
    assert prepared["resource_limits"] == sandbox.resource_limits()
