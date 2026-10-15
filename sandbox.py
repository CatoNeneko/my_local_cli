"""Linux bubblewrap 中的只读项目测试执行器，不提供宿主回退。"""

import os
import json
import selectors
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from config import sandbox_config
from permissions import PROJECT_ROOT, protected_project_paths, resolve_project_path


def runtime_environment(value=None):
    """默认使用当前解释器环境；工作区切换不会改变运行环境。"""
    return Path(value if value is not None else sys.prefix).resolve()


# 在沙箱内的独立解释器设置限制，不在线程中的 Popen 使用 preexec_fn。
LIMIT_BOOTSTRAP = """import json,os,resource,sys
limits=json.loads(sys.argv[1])
for name,value in limits.items():
    kind=getattr(resource,name)
    _,inherited_hard=resource.getrlimit(kind)
    hard=value if inherited_hard==resource.RLIM_INFINITY else min(value,inherited_hard)
    soft=max(1,hard-1) if name=='RLIMIT_CPU' else hard
    resource.setrlimit(kind,(soft,hard))
os.execvpe(sys.argv[2],sys.argv[2:],os.environ)
"""


def resource_limits():
    mapping = {
        "cpu_seconds": "RLIMIT_CPU",
        "address_space_bytes": "RLIMIT_AS",
        "file_size_bytes": "RLIMIT_FSIZE",
        "open_files": "RLIMIT_NOFILE",
    }
    limits = {"RLIMIT_CORE": 0}
    for key, name in mapping.items():
        value = sandbox_config.get(key)
        if type(value) is not int or value <= 0:
            raise ValueError("沙箱资源限制必须是正整数: " + key)
        limits[name] = value
    return limits


def limited_program(argv, limits=None):
    limits = resource_limits() if limits is None else limits
    return ["/usr/bin/python3", "-I", "-c", LIMIT_BOOTSTRAP, json.dumps(limits), *argv]


def build_test_command(target, bwrap, limits=None, runtime_env=None):
    relative_path = target.relative_to(PROJECT_ROOT)
    sandbox_target = str(Path("/workspace") / relative_path)
    command = [
        bwrap,
        "--unshare-user",
        "--unshare-pid",
        "--unshare-net",
        "--unshare-ipc",
        "--unshare-uts",
        "--die-with-parent",
        "--new-session",
        "--ro-bind",
        "/usr",
        "/usr",
    ]
    for library in ("/lib", "/lib64"):
        if Path(library).exists():
            command.extend(["--ro-bind", library, library])

    command.extend(
        [
            "--ro-bind",
            str(runtime_environment(runtime_env)),
            "/runtime",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",
            "--chmod",
            "1777",
            "/tmp",
            "--ro-bind",
            str(PROJECT_ROOT),
            "/workspace",
        ]
    )
    # 项目内容可读；环境、控制配置及历史不暴露给测试进程。
    for relative_path, is_directory in protected_project_paths(PROJECT_ROOT):
        destination = str(Path("/workspace") / relative_path)
        if is_directory:
            command.extend(["--tmpfs", destination])
        else:
            command.extend(["--ro-bind", "/dev/null", destination])

    command.extend(
        [
            "--chdir",
            "/workspace",
            "--clearenv",
            "--setenv",
            "HOME",
            "/tmp",
            "--setenv",
            "PATH",
            "/runtime/bin:/usr/bin",
            "--setenv",
            "LANG",
            "C.UTF-8",
            "--setenv",
            "PYTHONDONTWRITEBYTECODE",
            "1",
            "--setenv",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
            "1",
            "--",
            *limited_program(
                [
                    "/runtime/bin/python",
                    "-m",
                    "pytest",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    "--",
                    sandbox_target,
                ],
                limits,
            ),
        ]
    )
    return command


def collect_output(command, timeout_seconds, max_output_bytes):
    """同时限制运行时间和捕获字节，超限时终止整个子进程组。"""
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
    )
    output_bytes = bytearray()
    timed_out = False
    output_limit_exceeded = False
    cancelled = False
    deadline = time.monotonic() + timeout_seconds

    try:
        with selectors.DefaultSelector() as selector:
            os.set_blocking(process.stdout.fileno(), False)
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                if time.monotonic() >= deadline:
                    timed_out = True
                    break
                for key, _ in selector.select(timeout=0.1):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    remaining = max_output_bytes - len(output_bytes)
                    output_bytes.extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        output_limit_exceeded = True
                        break
                if output_limit_exceeded:
                    break
                if process.poll() is not None and not selector.get_map():
                    break
    except KeyboardInterrupt:
        cancelled = True
    finally:
        if process.poll() is None or cancelled or timed_out or output_limit_exceeded:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait()
        process.stdout.close()

    return {
        "exit_code": process.returncode,
        "output": output_bytes.decode("utf-8", errors="replace"),
        "timed_out": timed_out,
        "output_limit_exceeded": output_limit_exceeded,
        "cancelled": cancelled,
    }


def prepare_tests(path=".", *, runtime_env=None):
    if not isinstance(path, str) or not path:
        return {"ok": False, "error": "测试路径必须是非空字符串"}
    if sys.platform != "linux":
        return {"ok": False, "error": "此沙箱仅支持 Linux/WSL，不会在宿主回退执行"}

    path_result = resolve_project_path(path)
    if not path_result["ok"]:
        return path_result
    target = Path(path_result["path"])
    if not target.exists():
        return {"ok": False, "error": "测试路径不存在"}
    if not target.is_dir() and (not target.is_file() or target.suffix != ".py"):
        return {"ok": False, "error": "请选择目录或 Python 测试文件"}
    # 即使调用者指定运行时/隐藏控制目录，也不能拿它们作为测试目标。
    relative_path = target.relative_to(PROJECT_ROOT)
    if any(part.startswith(".") for part in relative_path.parts):
        return {"ok": False, "error": "不能以隐藏目录或隐藏文件作为测试目标"}

    bwrap = shutil.which("bwrap")
    runtime_env = runtime_environment(runtime_env)
    if not bwrap or not (runtime_env / "bin/python").is_file():
        return {"ok": False, "error": "缺少 bubblewrap 或项目解释器；拒绝回退到宿主"}

    timeout_seconds = sandbox_config["timeout_seconds"]
    max_output_bytes = sandbox_config["max_output_bytes"]
    max_output_chars = sandbox_config["max_output_chars"]
    for value in (timeout_seconds, max_output_bytes, max_output_chars):
        if type(value) is not int or value <= 0:
            return {"ok": False, "error": "沙箱限制必须是正整数"}
    try:
        limits = resource_limits()
    except ValueError as error:
        return {"ok": False, "error": str(error)}

    return {
        "ok": True,
        "path": str(target),
        "bwrap": bwrap,
        "timeout_seconds": timeout_seconds,
        "max_output_bytes": max_output_bytes,
        "max_output_chars": max_output_chars,
        "resource_limits": limits,
        "runtime_env": str(runtime_env),
        "details": "运行 pytest；项目只读、默认禁网；超时 "
        + str(timeout_seconds)
        + " 秒；资源上限 "
        + json.dumps(limits),
    }


def execute_prepared_tests(prepared):
    """内部执行实现；调用前须经过统一授权入口。"""
    checked = resolve_project_path(prepared["path"])
    if not checked["ok"]:
        return checked
    if checked["path"] != prepared["path"]:
        return {"ok": False, "error": "测试目标已变化，请重新提交"}
    target = Path(checked["path"])
    bwrap = prepared["bwrap"]
    timeout_seconds = prepared["timeout_seconds"]
    max_output_bytes = prepared["max_output_bytes"]
    max_output_chars = prepared["max_output_chars"]
    command = build_test_command(
        target, bwrap, prepared["resource_limits"], prepared["runtime_env"]
    )
    try:
        result = collect_output(command, timeout_seconds, max_output_bytes)
    except OSError as error:
        return {"ok": False, "error": "无法启动沙箱: " + str(error)}

    result["output_truncated"] = (
        len(result["output"]) > max_output_chars or result["output_limit_exceeded"]
    )
    result["resource_limits"] = prepared["resource_limits"]
    result["output"] = result["output"][:max_output_chars]
    result["ok"] = (
        result["exit_code"] == 0
        and not result["timed_out"]
        and not result["output_limit_exceeded"]
        and not result.get("cancelled")
    )
    if result.get("cancelled"):
        result["error"] = "测试已取消，沙箱子进程组已终止"
    elif result["timed_out"]:
        result["error"] = "测试超时，沙箱进程已终止"
    elif result["output_limit_exceeded"]:
        result["error"] = "测试输出超限，沙箱进程已终止"
    elif result["exit_code"] != 0:
        result["error"] = "测试未通过或沙箱启动失败，请查看 output 和 exit_code"
    return result


def run_tests(path="."):
    # 对 Python 调用也保留同一授权路径，不能绕过确认。
    from tool_runtime import execute_tool

    return execute_tool("run_tests", {"path": path})
