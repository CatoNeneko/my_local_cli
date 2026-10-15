"""Parent-side client for the isolated task supervisor."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from typing import Any


_RPC_METHODS = frozenset(
    {
        "ping",
        "start_pty",
        "spawn_agent",
        "task_status",
        "task_input",
        "task_cancel",
        "task_wait",
        "list_tasks",
        "proposal",
        "mark_applied",
        "resolve_task_approval",
        "close",
    }
)
_CLIENT_METHODS = _RPC_METHODS - {"close"}
_MAX_RPC_BYTES = 1024 * 1024
_RPC_TIMEOUT_SECONDS = 40.0
_STARTUP_TIMEOUT_SECONDS = 3.0
_SOCKET_PATH_LIMIT = 100


def _token_path(socket_path: str | os.PathLike[str]) -> Path:
    path = Path(socket_path)
    return path.with_name(path.name + ".token")


def _read_private_token(path: Path) -> str:
    """Read the supervisor nonce only from an owner-only regular file."""
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise RuntimeError("任务 supervisor 凭据文件类型无效")
    if hasattr(os, "getuid") and info.st_uid != os.getuid():
        raise RuntimeError("任务 supervisor 凭据文件所有者无效")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise RuntimeError("任务 supervisor 凭据文件权限过宽")
    token = path.read_text(encoding="ascii").strip()
    if not token or len(token) > 256:
        raise RuntimeError("任务 supervisor 凭据文件内容无效")
    return token


def _rpc(
    socket_path: str | os.PathLike[str],
    token: str,
    session_id: str | None,
    method: str,
    arguments: dict[str, Any] | None = None,
    run_id: str | None = None,
    *,
    timeout: float = _RPC_TIMEOUT_SECONDS,
    agent_task_id: str | None = None,
) -> dict[str, Any]:
    if method not in _RPC_METHODS:
        raise ValueError("不支持的任务 supervisor 方法")
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        raise TypeError("arguments 必须是对象")

    payload = {
        "token": token,
        "session_id": session_id,
        "method": method,
        "arguments": arguments,
        "run_id": run_id,
        "agent_task_id": agent_task_id,
    }
    try:
        encoded = (
            json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode(
                "utf-8"
            )
            + b"\n"
        )
    except (TypeError, ValueError) as error:
        raise ValueError("任务 supervisor 请求必须可序列化为 JSON") from error
    if len(encoded) > _MAX_RPC_BYTES:
        raise ValueError("任务 supervisor 请求超过 1 MiB")

    response = bytearray()
    got_line = False
    deadline = time.monotonic() + timeout
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(max(0.001, deadline - time.monotonic()))
            connection.connect(os.fspath(socket_path))
            connection.settimeout(max(0.001, deadline - time.monotonic()))
            connection.sendall(encoded)
            while True:
                connection.settimeout(max(0.001, deadline - time.monotonic()))
                block = connection.recv(min(65536, _MAX_RPC_BYTES + 1 - len(response)))
                if not block:
                    break
                newline = block.find(b"\n")
                if newline >= 0:
                    if len(response) + newline > _MAX_RPC_BYTES:
                        raise RuntimeError("任务 supervisor 响应超过 1 MiB")
                    response.extend(block[:newline])
                    got_line = True
                    break
                response.extend(block)
                if len(response) > _MAX_RPC_BYTES:
                    raise RuntimeError("任务 supervisor 响应超过 1 MiB")
    except (OSError, TimeoutError) as error:
        # Avoid exposing OS error text, which may contain private filesystem paths.
        raise RuntimeError("任务 supervisor 请求失败") from error

    if not got_line or not response:
        raise RuntimeError("任务 supervisor 未返回响应")
    try:
        result = json.loads(response.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("任务 supervisor 返回了无效 JSON") from error
    if not isinstance(result, dict):
        raise RuntimeError("任务 supervisor 响应必须是对象")
    return result


def _select_socket_path(state_dir: Path) -> tuple[Path, Path | None]:
    preferred = state_dir / "tasks.sock"
    if len(os.fsencode(preferred)) < _SOCKET_PATH_LIMIT:
        return preferred, None

    identity = f"{os.getuid() if hasattr(os, 'getuid') else 'user'}:{state_dir.resolve()}"
    suffix = hashlib.sha256(identity.encode("utf-8", errors="surrogatepass")).hexdigest()[:20]
    fallback_dir = Path("/tmp") / f"ai-cli-task-{suffix}"
    return fallback_dir / "tasks.sock", None


class TaskService:
    """Own the supervisor process and expose its authenticated RPC API.

    Construction is intentionally lightweight. Call :meth:`start` from the
    server lifecycle after settings and the SQLite store are ready.
    """

    def __init__(self, settings: Any, store: Any):
        self.settings = settings
        self.store = store
        self.state_dir = Path(settings.state_dir).expanduser().resolve()
        self.socket_path, self._created_fallback_dir = _select_socket_path(self.state_dir)
        self.token_path = _token_path(self.socket_path)
        self._token: str | None = None
        self._process: subprocess.Popen[bytes] | None = None
        self._socket_identity: tuple[int, int] | None = None
        self._owns_token_file = False
        self._started = False
        self._lock = threading.RLock()

    def start(self) -> "TaskService":
        """Create the private nonce and launch the supervisor once."""
        with self._lock:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            self._prepare_fallback_directory()
            with self._startup_lock():
                if self._started:
                    if self._process is not None and self._process.poll() is None:
                        return self
                    raise RuntimeError("任务 supervisor 已停止")

                self._reject_or_remove_stale_socket()
                self._token = secrets.token_urlsafe(32)
                self._create_token_file(self._token)

                child_env = os.environ.copy()
                child_env.update(
                    {
                        "AI_CLI_MODEL": str(self.settings.model),
                        "AI_CLI_BASE_URL": str(self.settings.base_url),
                        "AI_CLI_API_KEY_ENV": str(self.settings.api_key_env),
                        "AI_CLI_WORKSPACE_ROOT": os.fspath(self.settings.workspace_root),
                        "AI_CLI_WEB_STATE": os.fspath(self.state_dir),
                        "AI_CLI_MAX_WORKERS": str(self.settings.max_workers),
                        "AI_CLI_RUN_TIMEOUT": str(self.settings.run_timeout),
                        "AI_CLI_APPROVAL_MODE": str(self.settings.approval_mode),
                        "AI_CLI_MCP": "1" if self.settings.mcp_enabled else "0",
                        "AI_CLI_TASK_TOKEN": self._token,
                        "LANGSMITH_TRACING": "false",
                        "LANGCHAIN_TRACING_V2": "false",
                    }
                )
                command = [
                    sys.executable,
                    "-m",
                    "web.task_host",
                    "--socket",
                    os.fspath(self.socket_path),
                    "--db",
                    os.fspath(self.store.db_path),
                ]
                project_root = Path(__file__).resolve().parent.parent
                try:
                    self._process = subprocess.Popen(
                        command,
                        cwd=project_root,
                        env=child_env,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )
                    self._wait_until_ready()
                    info = self.socket_path.lstat()
                    if not stat.S_ISSOCK(info.st_mode):
                        raise RuntimeError("任务 supervisor 未创建 Unix socket")
                    if hasattr(os, "getuid") and info.st_uid != os.getuid():
                        raise RuntimeError("任务 supervisor socket 所有者无效")
                    self._socket_identity = (info.st_dev, info.st_ino)
                    self._started = True
                    return self
                except BaseException:
                    self._stop_owned_process()
                    self._cleanup_owned_files()
                    raise

    def request(
        self,
        session_id: str | None,
        method: str,
        arguments: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        """Send one authenticated request over one socket connection."""
        if not self._started or self._token is None:
            raise RuntimeError("任务 supervisor 尚未启动")
        return _rpc(
            self.socket_path,
            self._token,
            session_id,
            method,
            arguments,
            run_id,
        )

    def close(self) -> None:
        """Ask the owned supervisor to stop, then reap only our process group."""
        with self._lock:
            if not self._started and self._process is None:
                self._cleanup_owned_files()
                return
            with self._startup_lock():
                try:
                    if self._started and self._token is not None:
                        _rpc(
                            self.socket_path,
                            self._token,
                            None,
                            "close",
                            {},
                            timeout=3.0,
                        )
                except (RuntimeError, ValueError):
                    pass

                process = self._process
                if process is not None:
                    try:
                        process.wait(timeout=3.0)
                    except subprocess.TimeoutExpired:
                        self._signal_owned_process_group(signal.SIGTERM)
                        try:
                            process.wait(timeout=1.0)
                        except subprocess.TimeoutExpired:
                            self._signal_owned_process_group(signal.SIGKILL)
                            process.wait(timeout=1.0)

                self._cleanup_owned_files()
                self._started = False
                self._process = None

    def _create_token_file(self, token: str) -> None:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(self.token_path, flags, 0o600)
        self._owns_token_file = True
        try:
            with os.fdopen(descriptor, "w", encoding="ascii") as token_file:
                token_file.write(token)
                token_file.flush()
                os.fsync(token_file.fileno())
        except BaseException:
            self._owns_token_file = False
            try:
                self.token_path.unlink()
            except FileNotFoundError:
                pass
            raise

    def _reject_or_remove_stale_socket(self) -> None:
        try:
            info = self.socket_path.lstat()
        except FileNotFoundError:
            self._remove_stale_token()
            return

        if not stat.S_ISSOCK(info.st_mode):
            raise RuntimeError("任务 supervisor socket 路径已被非 socket 文件占用")
        if hasattr(os, "getuid") and info.st_uid != os.getuid():
            raise RuntimeError("任务 supervisor socket 属于其他用户")

        active = False
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.settimeout(0.2)
                connection.connect(os.fspath(self.socket_path))
                active = True
                try:
                    probe = (
                        json.dumps(
                            {
                                "token": "",
                                "session_id": None,
                                "method": "ping",
                                "arguments": {},
                                "run_id": None,
                            },
                            separators=(",", ":"),
                        ).encode("ascii")
                        + b"\n"
                    )
                    connection.sendall(probe)
                except OSError:
                    pass
        except (OSError, TimeoutError):
            active = False
        if active:
            raise RuntimeError("任务 supervisor socket 已由活动进程占用")

        try:
            current = self.socket_path.lstat()
        except FileNotFoundError:
            current = None
        if current is not None:
            if (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino):
                raise RuntimeError("任务 supervisor socket 在启动期间发生变化")
            self.socket_path.unlink()
        self._remove_stale_token()

    def _remove_stale_token(self) -> None:
        try:
            info = self.token_path.lstat()
        except FileNotFoundError:
            return
        if stat.S_ISREG(info.st_mode) and (not hasattr(os, "getuid") or info.st_uid == os.getuid()):
            self.token_path.unlink()

    def _wait_until_ready(self) -> None:
        deadline = time.monotonic() + _STARTUP_TIMEOUT_SECONDS
        last_error: BaseException | None = None
        while time.monotonic() < deadline:
            if self._process is None or self._process.poll() is not None:
                raise RuntimeError("任务 supervisor 启动失败")
            try:
                result = _rpc(
                    self.socket_path,
                    self._token or "",
                    None,
                    "ping",
                    {},
                    timeout=min(0.2, max(0.01, deadline - time.monotonic())),
                )
                if result.get("ok") is True:
                    info = self.socket_path.lstat()
                    if stat.S_ISSOCK(info.st_mode):
                        self._socket_identity = (info.st_dev, info.st_ino)
                    return
            except RuntimeError as error:
                last_error = error
                time.sleep(0.03)
        if self._process is not None and self._process.poll() is None:
            self._stop_owned_process()
        raise RuntimeError("任务 supervisor 未能在 3 秒内响应 ping") from last_error

    def _signal_owned_process_group(self, signum: int) -> None:
        process = self._process
        if process is None or process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signum)
        except ProcessLookupError:
            pass

    def _stop_owned_process(self) -> None:
        process = self._process
        if process is None or process.poll() is not None:
            return
        self._signal_owned_process_group(signal.SIGTERM)
        try:
            process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            self._signal_owned_process_group(signal.SIGKILL)
            try:
                process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                pass

    def _prepare_fallback_directory(self) -> None:
        fallback_dir = self.socket_path.parent
        if fallback_dir == self.state_dir:
            return
        created = False
        try:
            fallback_dir.mkdir(mode=0o700)
            created = True
        except FileExistsError:
            pass
        info = fallback_dir.lstat()
        if not stat.S_ISDIR(info.st_mode):
            raise RuntimeError("任务 supervisor 临时目录类型无效")
        if hasattr(os, "getuid") and info.st_uid != os.getuid():
            raise RuntimeError("任务 supervisor 临时目录所有者无效")
        if stat.S_IMODE(info.st_mode) & 0o077:
            raise RuntimeError("任务 supervisor 临时目录权限过宽")
        if created:
            self._created_fallback_dir = fallback_dir

    @contextmanager
    def _startup_lock(self):
        lock_path = self.state_dir / "tasks.lock"
        flags = os.O_CREAT | os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(lock_path, flags, 0o600)
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode):
                raise RuntimeError("任务 supervisor 启动锁类型无效")
            if hasattr(os, "getuid") and info.st_uid != os.getuid():
                raise RuntimeError("任务 supervisor 启动锁所有者无效")
            if stat.S_IMODE(info.st_mode) & 0o077:
                raise RuntimeError("任务 supervisor 启动锁权限过宽")
            import fcntl

            fcntl.flock(descriptor, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)

    def _cleanup_owned_files(self) -> None:
        owns_nonce = False
        if self._owns_token_file and self._token is not None:
            try:
                current = _read_private_token(self.token_path)
                owns_nonce = hmac.compare_digest(current, self._token)
            except (OSError, RuntimeError):
                pass

        if owns_nonce and self._token is not None:
            try:
                info = self.socket_path.lstat()
            except FileNotFoundError:
                info = None
            if (
                info is not None
                and stat.S_ISSOCK(info.st_mode)
                and (not hasattr(os, "getuid") or info.st_uid == os.getuid())
                and (
                    self._socket_identity is None
                    or (info.st_dev, info.st_ino) == self._socket_identity
                )
            ):
                try:
                    self.socket_path.unlink()
                except FileNotFoundError:
                    pass

        if owns_nonce:
            try:
                self.token_path.unlink()
            except FileNotFoundError:
                pass
        self._owns_token_file = False
        self._token = None
        self._socket_identity = None

        fallback = self._created_fallback_dir
        if fallback is not None:
            try:
                fallback.rmdir()
            except OSError:
                pass
            self._created_fallback_dir = None


class TaskClient:
    """Worker-facing task API; the privileged ``close`` method is omitted."""

    def __init__(
        self,
        socket_path: str | os.PathLike[str],
        session_id: str,
        run_id: str,
        agent_task_id: str | None = None,
    ):
        self.socket_path = Path(socket_path)
        self.session_id = session_id
        self.run_id = run_id
        self.agent_task_id = agent_task_id
        self._token = _read_private_token(_token_path(self.socket_path))

    def _request(self, method: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if method not in _CLIENT_METHODS:
            raise ValueError("不支持的 worker 任务方法")
        try:
            return _rpc(
                self.socket_path,
                self._token,
                self.session_id,
                method,
                arguments,
                self.run_id,
                agent_task_id=self.agent_task_id,
            )
        except RuntimeError as error:
            from web.diagnostics import safe_diagnostic

            diagnostic = safe_diagnostic(error, "task_supervisor", self.run_id)
            return {
                "ok": False,
                "error": "后台任务服务不可用，请检查服务状态",
                "diagnostic": diagnostic,
            }

    def start_pty(self, prepared: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "start_pty",
            {
                "path": prepared["workspace_path"],
                "argv": prepared["argv"],
                "timeout": prepared["timeout"],
            },
        )

    def start_agent(self, path: str, task: str) -> dict[str, Any]:
        return self._request("spawn_agent", {"path": path, "task": task})

    def inspect_task(self, task_id: str, offset: int = 0) -> dict[str, Any]:
        return self.task_status(task_id, offset)

    def task_status(self, task_id: str, offset: int = 0) -> dict[str, Any]:
        return self._request("task_status", {"task_id": task_id, "offset": offset})

    def send_input(self, task_id: str, text: str) -> dict[str, Any]:
        return self._request("task_input", {"task_id": task_id, "text": text})

    def cancel_task(self, task_id: str) -> dict[str, Any]:
        return self._request("task_cancel", {"task_id": task_id})

    def wait_task(self, task_id: str, seconds: float = 30) -> dict[str, Any]:
        if (
            isinstance(seconds, bool)
            or not isinstance(seconds, (int, float))
            or not 0 <= seconds <= 30
        ):
            raise ValueError("任务等待时间应为 0–30 秒")
        arguments: dict[str, Any] = {"task_id": task_id, "seconds": seconds}
        return self._request("task_wait", arguments)

    def list_tasks(self) -> dict[str, Any]:
        return self._request("list_tasks", {})

    def owns_task(self, task_id: str) -> bool:
        return self.task_status(task_id).get("ok") is True

    def job_kind(self, task_id: str) -> str | None:
        kind = self.task_status(task_id).get("kind")
        return kind if isinstance(kind, str) else None

    def proposal(self, task_id: str, proposal_id: str) -> dict[str, Any]:
        return self._request("proposal", {"task_id": task_id, "proposal_id": proposal_id})

    def mark_applied(self, task_id: str, proposal_id: str) -> dict[str, Any]:
        return self._request("mark_applied", {"task_id": task_id, "proposal_id": proposal_id})

    def resolve_approval(self, task_id, approval_id, allow):
        return self._request(
            "resolve_task_approval",
            {"task_id": task_id, "approval_id": approval_id, "allow": allow},
        )
