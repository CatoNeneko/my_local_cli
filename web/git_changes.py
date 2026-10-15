"""只读 Git 状态、任务前文本快照与单文件安全恢复。"""

from __future__ import annotations

import difflib
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import secrets
import shutil
import sqlite3
import stat
import subprocess
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any
import uuid


MAX_FILE_BYTES = 256 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024
MAX_FILES = 500
MAX_DIFF_CHARS = 2 * 1024 * 1024
GIT_TIMEOUT_SECONDS = 5

_TEXT_SUFFIXES = frozenset(
    {
        ".py",
        ".pyi",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".md",
        ".mdx",
        ".txt",
        ".rst",
        ".json",
        ".jsonc",
        ".toml",
        ".ini",
        ".cfg",
        ".yaml",
        ".yml",
        ".css",
        ".scss",
        ".html",
        ".htm",
        ".xml",
        ".sql",
        ".sh",
        ".bash",
        ".go",
        ".rs",
        ".java",
        ".kt",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".cs",
        ".php",
        ".rb",
        ".swift",
        ".vue",
        ".svelte",
    }
)
_PRIVATE_NAMES = frozenset(
    {
        ".git",
        ".aws",
        ".codex",
        ".agents",
        ".idea",
        ".conda-env",
        ".venv",
        ".venv.windows",
        ".browser-runtime",
        ".browser-artifacts",
        ".env",
        ".ai-cli",
        "artifacts",
        "sessions",
        "node_modules",
        "__pycache__",
        "history.json",
        "history.jsonl",
        "tool_events.jsonl",
        "webstate",
        "web_state",
        "web-state",
        "skills",
    }
)
_PRIVATE_SUFFIXES = frozenset({".jsonl", ".pem", ".key", ".p12", ".pfx"})
_DIRECTORY_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class _GitCommandError(RuntimeError):
    pass


class _UnsafeFile(ValueError):
    pass


class GitManager:
    """管理 Git 仓库工作区的受限状态查看、快照与单文件恢复。

    快照数据库与内容寻址 blob 位于 ``state_dir/git_snapshot``。Git 操作只
    读取仓库状态，不会修改索引、HEAD 或执行 reset、clean、stash。
    """

    _SQL_TIMEOUT = 5.0

    def __init__(self, state_dir: str | os.PathLike[str]):
        self.state_dir = Path(state_dir).expanduser().resolve()
        self.snapshot_dir = self.state_dir / "git_snapshot"
        self.blob_dir = self.snapshot_dir / "blobs"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.blob_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            self.snapshot_dir.chmod(0o700)
            self.blob_dir.chmod(0o700)
        except OSError:
            pass
        self.db_path = self.snapshot_dir / "snapshots.sqlite3"
        self._lock = threading.RLock()
        with self._connection(write=True) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    id TEXT PRIMARY KEY,
                    workspace TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    file_count INTEGER NOT NULL,
                    total_bytes INTEGER NOT NULL,
                    skipped_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS snapshots_by_workspace
                    ON snapshots(workspace, created_at DESC, id DESC);
                CREATE TABLE IF NOT EXISTS snapshot_files (
                    snapshot_id TEXT NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
                    path TEXT NOT NULL,
                    present INTEGER NOT NULL CHECK (present IN (0, 1)),
                    sha256 TEXT,
                    size INTEGER NOT NULL,
                    mode INTEGER NOT NULL,
                    PRIMARY KEY (snapshot_id, path)
                );
                """
            )
        try:
            self.db_path.chmod(0o600)
        except OSError:
            pass

    @contextmanager
    def _connection(self, *, write: bool = False):
        connection = sqlite3.connect(self.db_path, timeout=self._SQL_TIMEOUT, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {int(self._SQL_TIMEOUT * 1000)}")
        connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        try:
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _workspace_path(workspace: str | os.PathLike[str]) -> Path:
        try:
            value = os.fspath(workspace)
        except TypeError as error:
            raise TypeError("workspace 必须是路径") from error
        if not value.strip():
            raise ValueError("workspace 不能为空")
        try:
            root = Path(value).expanduser().resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise ValueError("workspace 必须是存在的目录") from error
        if not root.is_dir():
            raise ValueError("workspace 必须是目录")
        return root

    @staticmethod
    def _git_environment() -> dict[str, str]:
        # 移除继承的 GIT_* 变量，防止调用者注入 alternate index、worktree 或配置。
        environment = {
            key: value for key, value in os.environ.items() if not key.startswith("GIT_")
        }
        environment.update(
            {
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_SYSTEM": os.devnull,
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_PAGER": "cat",
                "GIT_OPTIONAL_LOCKS": "0",
                "LC_ALL": "C",
            }
        )
        return environment

    @classmethod
    def _run_git(cls, root: Path, arguments: list[str], *, check: bool = True) -> bytes:
        executable = shutil.which("git")
        if not executable:
            raise RuntimeError("找不到 Git 可执行程序")
        command = [
            executable,
            "--no-pager",
            "--literal-pathspecs",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.pager=cat",
            "-c",
            "core.hooksPath=" + os.devnull,
            "-c",
            "diff.external=",
            *arguments,
        ]
        try:
            result = subprocess.run(
                command,
                cwd=root,
                env=cls._git_environment(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=GIT_TIMEOUT_SECONDS,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError("Git 操作超过 5 秒") from error
        except OSError as error:
            raise RuntimeError("无法启动 Git") from error
        if check and result.returncode:
            detail = result.stderr.decode("utf-8", "replace").strip()
            raise _GitCommandError(detail or "Git 操作失败")
        return result.stdout

    @classmethod
    def _repo_root(cls, workspace: str | os.PathLike[str]) -> Path:
        root = cls._workspace_path(workspace)
        try:
            output = cls._run_git(root, ["rev-parse", "--show-toplevel"])
        except _GitCommandError as error:
            raise ValueError("workspace 不是 Git 仓库") from error
        top = Path(os.fsdecode(output.rstrip(b"\r\n"))).resolve()
        if top != root:
            raise ValueError("workspace 必须是 Git 仓库根目录")
        return root

    @staticmethod
    def _path_parts(relative: str) -> tuple[str, ...]:
        if not isinstance(relative, str) or not relative or "\x00" in relative:
            raise ValueError("文件路径无效")
        if relative.startswith("/") or "\\" in relative:
            raise ValueError("只允许仓库内的相对路径")
        parts = PurePosixPath(relative).parts
        if not parts or any(part in ("", ".", "..") for part in parts):
            raise ValueError("文件路径无效")
        if any(part.startswith(".") or part.casefold() in _PRIVATE_NAMES for part in parts):
            raise ValueError("禁止访问隐藏或私有文件")
        if PurePosixPath(relative).suffix.casefold() in _PRIVATE_SUFFIXES:
            raise ValueError("禁止访问私有文件类型")
        if PurePosixPath(relative).suffix.casefold() not in _TEXT_SUFFIXES:
            raise ValueError("只支持受限文本文件类型")
        return parts

    @classmethod
    def _eligible_path(cls, relative: str) -> bool:
        try:
            cls._path_parts(relative)
            return True
        except ValueError:
            return False

    @staticmethod
    def _open_parent(root: Path, parts: tuple[str, ...]) -> tuple[int | None, str]:
        descriptor = os.open(root, _DIRECTORY_FLAGS)
        try:
            for part in parts[:-1]:
                try:
                    child = os.open(part, _DIRECTORY_FLAGS | _NOFOLLOW, dir_fd=descriptor)
                except FileNotFoundError:
                    os.close(descriptor)
                    return None, parts[-1]
                except OSError as error:
                    if error.errno in (errno.ELOOP, errno.ENOTDIR):
                        raise _UnsafeFile("文件路径包含符号链接") from error
                    raise
                os.close(descriptor)
                descriptor = child
            return descriptor, parts[-1]
        except BaseException:
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise

    @classmethod
    def _read_current(cls, root: Path, relative: str) -> dict[str, Any]:
        parts = cls._path_parts(relative)
        parent_fd, name = cls._open_parent(root, parts)
        if parent_fd is None:
            return {"exists": False, "kind": "missing", "data": None, "mode": 0, "hash": None}
        try:
            try:
                info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            except FileNotFoundError:
                return {"exists": False, "kind": "missing", "data": None, "mode": 0, "hash": None}
            if stat.S_ISLNK(info.st_mode):
                return {"exists": False, "kind": "symlink", "data": None, "mode": 0, "hash": None}
            if not stat.S_ISREG(info.st_mode):
                return {
                    "exists": False,
                    "kind": "non_regular",
                    "data": None,
                    "mode": 0,
                    "hash": None,
                }
            if info.st_size > MAX_FILE_BYTES:
                return {
                    "exists": True,
                    "kind": "large",
                    "data": None,
                    "mode": stat.S_IMODE(info.st_mode),
                    "hash": None,
                }
            try:
                file_fd = os.open(
                    name, os.O_RDONLY | _NOFOLLOW | getattr(os, "O_CLOEXEC", 0), dir_fd=parent_fd
                )
            except FileNotFoundError:
                return {"exists": False, "kind": "missing", "data": None, "mode": 0, "hash": None}
            except OSError as error:
                if error.errno == errno.ELOOP:
                    return {
                        "exists": False,
                        "kind": "symlink",
                        "data": None,
                        "mode": 0,
                        "hash": None,
                    }
                raise
            try:
                opened = os.fstat(file_fd)
                if not stat.S_ISREG(opened.st_mode):
                    return {
                        "exists": False,
                        "kind": "non_regular",
                        "data": None,
                        "mode": 0,
                        "hash": None,
                    }
                if opened.st_size > MAX_FILE_BYTES:
                    return {
                        "exists": True,
                        "kind": "large",
                        "data": None,
                        "mode": stat.S_IMODE(opened.st_mode),
                        "hash": None,
                    }
                chunks = bytearray()
                while len(chunks) <= MAX_FILE_BYTES:
                    block = os.read(file_fd, min(65536, MAX_FILE_BYTES + 1 - len(chunks)))
                    if not block:
                        break
                    chunks.extend(block)
                data = bytes(chunks)
            finally:
                os.close(file_fd)
            if len(data) > MAX_FILE_BYTES:
                return {
                    "exists": True,
                    "kind": "large",
                    "data": None,
                    "mode": stat.S_IMODE(opened.st_mode),
                    "hash": None,
                }
            return {
                "exists": True,
                "kind": "regular",
                "data": data,
                "mode": stat.S_IMODE(opened.st_mode),
                "hash": _sha256(data),
            }
        finally:
            os.close(parent_fd)

    @classmethod
    def _status_entries(cls, root: Path) -> tuple[list[tuple[str, str]], int]:
        output = cls._run_git(
            root,
            [
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
                "--no-renames",
                "--ignore-submodules=all",
                "-z",
            ],
        )
        entries = []
        raw_count = 0
        for record in output.split(b"\0"):
            if not record:
                continue
            raw_count += 1
            if len(record) < 4 or record[2:3] != b" ":
                continue
            status_code = record[:2].decode("ascii", "replace")
            relative = os.fsdecode(record[3:])
            if cls._eligible_path(relative):
                try:
                    current = cls._read_current(root, relative)
                except _UnsafeFile:
                    continue
                if current["kind"] not in ("symlink", "non_regular", "large"):
                    entries.append((relative, status_code))
        return entries, raw_count

    def status(self, workspace: str | os.PathLike[str]) -> dict[str, Any]:
        root = self._repo_root(workspace)
        entries, raw_count = self._status_entries(root)
        branch_output = self._run_git(
            root, ["symbolic-ref", "--quiet", "--short", "HEAD"], check=False
        )
        branch = os.fsdecode(branch_output.rstrip(b"\r\n")) or None
        files = [
            {
                "path": relative,
                "status": code,
                "staged": code[0] not in (" ", "?"),
                "unstaged": code[1] not in (" ", "?"),
                "untracked": code == "??",
            }
            for relative, code in entries
        ]
        return {
            "workspace": str(root),
            "branch": branch,
            "clean": raw_count == 0,
            "suppressed_changes": raw_count > len(files),
            "files": files,
        }

    def diff(self, workspace: str | os.PathLike[str]) -> dict[str, Any]:
        root = self._repo_root(workspace)
        entries, raw_count = self._status_entries(root)
        pieces: list[str] = []
        skipped: list[dict[str, str]] = []
        consumed_bytes = 0
        for relative, code in entries:
            current = self._read_current(root, relative)
            if current["kind"] == "large":
                skipped.append({"path": relative, "reason": "文件超过 256 KiB 限制"})
                continue
            if current["kind"] in ("symlink", "non_regular"):
                continue
            if code == "??":
                data = current["data"] or b""
                if b"\x00" in data:
                    skipped.append({"path": relative, "reason": "二进制文件不展示 diff"})
                    continue
                try:
                    content = data.decode("utf-8")
                except UnicodeError:
                    skipped.append({"path": relative, "reason": "文件不是 UTF-8 文本"})
                    continue
                if consumed_bytes + len(data) > MAX_TOTAL_BYTES:
                    skipped.append({"path": relative, "reason": "diff 总大小超过 8 MiB 限制"})
                    continue
                consumed_bytes += len(data)
                lines = difflib.unified_diff(
                    [],
                    content.splitlines(keepends=True),
                    fromfile="/dev/null",
                    tofile=f"b/{relative}",
                    lineterm="\n",
                )
                pieces.append("".join(lines))
                continue

            if current["kind"] == "regular":
                data = current["data"] or b""
                if b"\x00" in data:
                    skipped.append({"path": relative, "reason": "二进制文件不展示 diff"})
                    continue
                try:
                    data.decode("utf-8")
                except UnicodeError:
                    skipped.append({"path": relative, "reason": "文件不是 UTF-8 文本"})
                    continue
                if consumed_bytes + len(data) > MAX_TOTAL_BYTES:
                    skipped.append({"path": relative, "reason": "diff 总大小超过 8 MiB 限制"})
                    continue
                consumed_bytes += len(data)
            # ``--literal-pathspecs`` 已由 _run_git 作为全局选项启用，路径原样传入。
            literal_path = relative
            cached = self._run_git(
                root,
                [
                    "diff",
                    "--cached",
                    "--no-ext-diff",
                    "--no-textconv",
                    "--no-renames",
                    "--no-color",
                    "--no-relative",
                    "--",
                    literal_path,
                ],
            )
            unstaged = self._run_git(
                root,
                [
                    "diff",
                    "--no-ext-diff",
                    "--no-textconv",
                    "--no-renames",
                    "--no-color",
                    "--no-relative",
                    "--",
                    literal_path,
                ],
            )
            pieces.extend(value.decode("utf-8", "replace") for value in (cached, unstaged) if value)
        text = "".join(pieces)
        truncated = len(text) > MAX_DIFF_CHARS
        if truncated:
            text = text[:MAX_DIFF_CHARS] + "\n… diff 输出已截断 …\n"
        return {
            "workspace": str(root),
            "diff": text,
            "files": [relative for relative, _ in entries],
            "skipped": skipped,
            "suppressed_changes": raw_count > len(entries),
            "truncated": truncated,
        }

    @staticmethod
    def _nul_paths(output: bytes) -> list[str]:
        return [os.fsdecode(value) for value in output.split(b"\0") if value]

    def _store_blob(self, digest: str, data: bytes) -> None:
        target = self.blob_dir / digest
        if target.exists():
            if _sha256(target.read_bytes()) != digest:
                raise RuntimeError("快照 blob 校验失败")
            return
        temporary = self.blob_dir / ("." + uuid.uuid4().hex + ".tmp")
        try:
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                view = memoryview(data)
                while view:
                    written = os.write(descriptor, view)
                    view = view[written:]
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            os.replace(temporary, target)
            target.chmod(0o600)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass

    def snapshot(self, workspace: str | os.PathLike[str], run_id: str) -> dict[str, Any]:
        root = self._repo_root(workspace)
        if not isinstance(run_id, str) or not run_id.strip() or len(run_id) > 200:
            raise ValueError("run_id 必须是 1 至 200 个字符")
        tracked = set(self._nul_paths(self._run_git(root, ["ls-files", "--cached", "-z"])))
        untracked = self._nul_paths(
            self._run_git(root, ["ls-files", "--others", "--exclude-standard", "-z"])
        )
        candidate_paths = sorted(tracked | set(untracked))
        skipped: dict[str, int] = {"private": 0, "symlink": 0, "non_text": 0}
        files: list[dict[str, Any]] = []
        blobs: list[tuple[str, bytes]] = []
        total_bytes = 0
        for relative in candidate_paths:
            if not self._eligible_path(relative):
                skipped["private"] += 1
                continue
            try:
                current = self._read_current(root, relative)
            except _UnsafeFile:
                skipped["symlink"] += 1
                continue
            if current["kind"] == "symlink":
                skipped["symlink"] += 1
                continue
            if current["kind"] == "non_regular":
                skipped["non_text"] += 1
                continue
            if current["kind"] == "large":
                raise ValueError(f"快照文件超过 256 KiB 限制：{relative}")
            if not current["exists"]:
                if relative in tracked:
                    if len(files) >= MAX_FILES:
                        raise ValueError("快照文件数超过 500 个限制")
                    files.append(
                        {"path": relative, "present": 0, "sha256": None, "size": 0, "mode": 0}
                    )
                continue
            data = current["data"] or b""
            if b"\x00" in data:
                skipped["non_text"] += 1
                continue
            try:
                data.decode("utf-8")
            except UnicodeError:
                skipped["non_text"] += 1
                continue
            if len(files) >= MAX_FILES:
                raise ValueError("快照文件数超过 500 个限制")
            if total_bytes + len(data) > MAX_TOTAL_BYTES:
                raise ValueError("快照总大小超过 8 MiB 限制")
            digest = _sha256(data)
            files.append(
                {
                    "path": relative,
                    "present": 1,
                    "sha256": digest,
                    "size": len(data),
                    "mode": current["mode"] & 0o777,
                }
            )
            blobs.append((digest, data))
            total_bytes += len(data)

        identifier = str(uuid.uuid4())
        created_at = _now()
        for digest, data in blobs:
            self._store_blob(digest, data)
        with self._lock, self._connection(write=True) as connection:
            connection.execute(
                "INSERT INTO snapshots (id, workspace, run_id, created_at, file_count, total_bytes, skipped_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    identifier,
                    str(root),
                    run_id,
                    created_at,
                    len(files),
                    total_bytes,
                    json.dumps(skipped, sort_keys=True),
                ),
            )
            connection.executemany(
                "INSERT INTO snapshot_files (snapshot_id, path, present, sha256, size, mode) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        identifier,
                        item["path"],
                        item["present"],
                        item["sha256"],
                        item["size"],
                        item["mode"],
                    )
                    for item in files
                ],
            )
        return {
            "id": identifier,
            "workspace": str(root),
            "run_id": run_id,
            "created_at": created_at,
            "file_count": len(files),
            "total_bytes": total_bytes,
            "skipped": skipped,
        }

    def list_snapshots(self, workspace: str | os.PathLike[str]) -> list[dict[str, Any]]:
        root = self._repo_root(workspace)
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT id, workspace, run_id, created_at, file_count, total_bytes, skipped_json "
                "FROM snapshots WHERE workspace = ? ORDER BY created_at DESC, id DESC",
                (str(root),),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "workspace": row["workspace"],
                "run_id": row["run_id"],
                "created_at": row["created_at"],
                "file_count": row["file_count"],
                "total_bytes": row["total_bytes"],
                "skipped": json.loads(row["skipped_json"]),
            }
            for row in rows
        ]

    def _snapshot_file(self, root: Path, snapshot_id: str, relative: str) -> sqlite3.Row:
        with self._connection() as connection:
            snapshot = connection.execute(
                "SELECT id FROM snapshots WHERE id = ? AND workspace = ?", (snapshot_id, str(root))
            ).fetchone()
            if snapshot is None:
                raise ValueError("快照不存在或不属于当前 workspace")
            row = connection.execute(
                "SELECT path, present, sha256, size, mode FROM snapshot_files "
                "WHERE snapshot_id = ? AND path = ?",
                (snapshot_id, relative),
            ).fetchone()
        if row is None:
            raise ValueError("该文件不在此快照中")
        return row

    def _blob(self, digest: str) -> bytes:
        path = self.blob_dir / digest
        try:
            data = path.read_bytes()
        except OSError as error:
            raise RuntimeError("快照内容不可用") from error
        if _sha256(data) != digest:
            raise RuntimeError("快照内容校验失败")
        return data

    def preview_restore(
        self,
        workspace: str | os.PathLike[str],
        snapshot_id: str,
        path: str,
    ) -> dict[str, Any]:
        root = self._repo_root(workspace)
        self._path_parts(path)
        saved = self._snapshot_file(root, snapshot_id, path)
        current = self._read_current(root, path)
        if current["kind"] in ("symlink", "non_regular", "large"):
            raise ValueError("当前路径是符号链接、非普通文件或超过 256 KiB，拒绝预览")
        if not saved["present"]:
            return {
                "snapshot_id": snapshot_id,
                "path": path,
                "current_hash": current["hash"],
                "snapshot_hash": None,
                "diff": "快照时文件不存在；当前实现不支持删除新文件。",
                "can_restore": False,
            }
        saved_data = self._blob(saved["sha256"])
        current_data = current["data"] if current["exists"] else b""
        if current["exists"] and (b"\x00" in current_data or b"\x00" in saved_data):
            diff_text = "文件包含二进制内容，无法生成文本 diff。"
        else:
            try:
                current_text = current_data.decode("utf-8").splitlines(keepends=True)
                saved_text = saved_data.decode("utf-8").splitlines(keepends=True)
                diff_text = "".join(
                    difflib.unified_diff(
                        current_text,
                        saved_text,
                        fromfile=f"current/{path}",
                        tofile=f"snapshot/{path}",
                        lineterm="\n",
                    )
                )
            except UnicodeError:
                diff_text = "当前文件不是 UTF-8 文本，无法生成文本 diff。"
        if len(diff_text) > MAX_DIFF_CHARS:
            diff_text = diff_text[:MAX_DIFF_CHARS] + "\n… diff 输出已截断 …\n"
        return {
            "snapshot_id": snapshot_id,
            "path": path,
            "current_hash": current["hash"],
            "snapshot_hash": saved["sha256"],
            "diff": diff_text,
            "can_restore": True,
        }

    @staticmethod
    def _atomic_replace(root: Path, relative: str, data: bytes, mode: int) -> None:
        parts = GitManager._path_parts(relative)
        parent_fd, name = GitManager._open_parent(root, parts)
        if parent_fd is None:
            raise ValueError("目标文件的父目录不存在")
        temporary = ".git-restore-" + secrets.token_hex(12)
        descriptor = None
        try:
            try:
                descriptor = os.open(
                    temporary,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | _NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
                    0o600,
                    dir_fd=parent_fd,
                )
                view = memoryview(data)
                while view:
                    written = os.write(descriptor, view)
                    view = view[written:]
                os.fchmod(descriptor, mode & 0o777)
                os.fsync(descriptor)
            finally:
                if descriptor is not None:
                    os.close(descriptor)
                    descriptor = None
            os.replace(temporary, name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
            os.fsync(parent_fd)
        finally:
            try:
                os.unlink(temporary, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
            os.close(parent_fd)

    def restore(
        self,
        workspace: str | os.PathLike[str],
        snapshot_id: str,
        path: str,
        expected_hash: str | None,
    ) -> dict[str, Any]:
        root = self._repo_root(workspace)
        self._path_parts(path)
        if expected_hash is not None and (
            not isinstance(expected_hash, str)
            or len(expected_hash) != 64
            or any(character not in "0123456789abcdef" for character in expected_hash)
        ):
            raise ValueError("expected_hash 必须是预览返回的 SHA-256 或 null")
        saved = self._snapshot_file(root, snapshot_id, path)
        current = self._read_current(root, path)
        if current["kind"] in ("symlink", "non_regular", "large"):
            raise ValueError("当前路径是符号链接、非普通文件或超过 256 KiB，拒绝恢复")
        if not saved["present"]:
            raise ValueError("快照时文件不存在；当前实现不支持删除新文件")
        if current["hash"] != expected_hash:
            return {
                "restored": False,
                "conflict": True,
                "path": path,
                "expected_hash": expected_hash,
                "current_hash": current["hash"],
                "message": "文件在预览后发生变化，请重新预览再恢复。",
            }
        saved_data = self._blob(saved["sha256"])
        if current["hash"] == saved["sha256"]:
            return {
                "restored": True,
                "changed": False,
                "conflict": False,
                "path": path,
                "current_hash": current["hash"],
            }
        with self._lock:
            # 在写临时文件前再核对一次，降低同进程并发修改造成的覆盖风险。
            latest = self._read_current(root, path)
            if (
                latest["kind"] in ("symlink", "non_regular", "large")
                or latest["hash"] != expected_hash
            ):
                return {
                    "restored": False,
                    "conflict": True,
                    "path": path,
                    "expected_hash": expected_hash,
                    "current_hash": latest["hash"],
                    "message": "文件在预览后发生变化，请重新预览再恢复。",
                }
            self._atomic_replace(root, path, saved_data, saved["mode"])
        return {
            "restored": True,
            "changed": True,
            "conflict": False,
            "path": path,
            "current_hash": saved["sha256"],
        }
