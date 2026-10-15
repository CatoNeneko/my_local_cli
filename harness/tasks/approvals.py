"""Persistent, one-shot approvals for externally hosted tasks."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import hmac
import os
from pathlib import Path
import sqlite3
from typing import Iterator
import uuid


_TIMEOUT_SECONDS = 10.0
_DUMMY_TOKEN_HASH = "0" * 64


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _validate_identifier(value: str, field: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")


def _validate_token(token: str) -> str:
    if not isinstance(token, str):
        raise TypeError("token must be a string")
    if not token:
        raise ValueError("token must not be empty")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _validate_request_text(value: str, field: str, limit: int) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip() or len(value) > limit:
        raise ValueError(f"{field} must contain 1 to {limit} characters")


class TaskApprovalStore:
    """Store task credentials and approval requests in a private SQLite database."""

    def __init__(self, db_path: str | Path):
        path = Path(db_path).expanduser()
        if str(path) == ":memory:":
            raise ValueError("db_path must name a persistent database")
        self.db_path = path.absolute()
        self._prepare_path()
        with self._connection(write=True) as connection:
            self._create_schema(connection)
        os.chmod(self.db_path, 0o600, follow_symlinks=False)

    def _prepare_path(self) -> None:
        parent = self.db_path.parent
        if parent.is_symlink() or self.db_path.is_symlink():
            raise ValueError("database path must not be a symbolic link")
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if parent.is_symlink() or self.db_path.is_symlink():
            raise ValueError("database path must not be a symbolic link")
        os.chmod(parent, 0o700, follow_symlinks=False)

        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(self.db_path, flags, 0o600)
        except OSError:
            if self.db_path.is_symlink():
                raise ValueError("database path must not be a symbolic link") from None
            raise
        try:
            os.fchmod(descriptor, 0o600)
        finally:
            os.close(descriptor)

    @contextmanager
    def _connection(self, *, write: bool = False) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(
            self.db_path,
            timeout=_TIMEOUT_SECONDS,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(f"PRAGMA busy_timeout = {int(_TIMEOUT_SECONDS * 1000)}")
            connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _create_schema(connection: sqlite3.Connection) -> None:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS task_owners (
                task_id TEXT PRIMARY KEY,
                token_hash TEXT NOT NULL,
                workspace TEXT NOT NULL,
                state TEXT NOT NULL CHECK (state IN ('active', 'closed'))
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS task_approval_requests (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL REFERENCES task_owners(task_id) ON DELETE CASCADE,
                action TEXT NOT NULL,
                target TEXT NOT NULL,
                details TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN
                    ('pending', 'approved', 'rejected', 'consumed', 'cancelled')),
                created_at TEXT NOT NULL
            )"""
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS task_approvals_by_status "
            "ON task_approval_requests(task_id, status, created_at, id)"
        )

    @staticmethod
    def _public_approval(row: sqlite3.Row | None) -> dict[str, str] | None:
        if row is None:
            return None
        return {
            "id": row["id"],
            "task_id": row["task_id"],
            "action": row["action"],
            "target": row["target"],
            "details": row["details"],
            "status": row["status"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _authenticate(
        connection: sqlite3.Connection,
        task_id: str,
        token_hash: str,
        *,
        require_active: bool = False,
    ) -> sqlite3.Row:
        row = connection.execute(
            "SELECT task_id, token_hash, workspace, state FROM task_owners WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        expected = row["token_hash"] if row is not None else _DUMMY_TOKEN_HASH
        matches = hmac.compare_digest(token_hash, expected)
        if row is None or not matches or (require_active and row["state"] != "active"):
            raise ValueError("invalid task credentials or state")
        return row

    @staticmethod
    def _approval_row(
        connection: sqlite3.Connection, task_id: str, approval_id: str
    ) -> sqlite3.Row:
        row = connection.execute(
            "SELECT id, task_id, action, target, details, status, created_at "
            "FROM task_approval_requests WHERE task_id = ? AND id = ?",
            (task_id, approval_id),
        ).fetchone()
        if row is None:
            raise ValueError("approval request not found")
        return row

    def register(self, task_id: str, token: str, workspace: str) -> None:
        """Register a task once, storing only a digest of its access token."""
        _validate_identifier(task_id, "task_id")
        token_hash = _validate_token(token)
        _validate_identifier(workspace, "workspace")
        with self._connection(write=True) as connection:
            try:
                connection.execute(
                    "INSERT INTO task_owners (task_id, token_hash, workspace, state) "
                    "VALUES (?, ?, ?, 'active')",
                    (task_id, token_hash, workspace),
                )
            except sqlite3.IntegrityError:
                raise ValueError("task is already registered") from None

    def create(
        self, task_id: str, token: str, action: str, target: str, details: str
    ) -> dict[str, str]:
        """Create or return an identical pending approval for an active task."""
        _validate_identifier(task_id, "task_id")
        token_hash = _validate_token(token)
        _validate_request_text(action, "action", 100)
        _validate_request_text(target, "target", 4096)
        _validate_request_text(details, "details", 20000)
        with self._connection(write=True) as connection:
            self._authenticate(connection, task_id, token_hash, require_active=True)
            duplicate = connection.execute(
                "SELECT id, task_id, action, target, details, status, created_at "
                "FROM task_approval_requests WHERE task_id = ? AND action = ? AND target = ? "
                "AND details = ? AND status = 'pending' ORDER BY created_at, id LIMIT 1",
                (task_id, action, target, details),
            ).fetchone()
            if duplicate is not None:
                return self._public_approval(duplicate)  # type: ignore[return-value]

            pending_count = connection.execute(
                "SELECT COUNT(*) FROM task_approval_requests WHERE task_id = ? AND status = 'pending'",
                (task_id,),
            ).fetchone()[0]
            if pending_count >= 3:
                raise ValueError("task already has the maximum number of pending approvals")

            approval = {
                "id": str(uuid.uuid4()),
                "task_id": task_id,
                "action": action,
                "target": target,
                "details": details,
                "status": "pending",
                "created_at": _now(),
            }
            connection.execute(
                "INSERT INTO task_approval_requests "
                "(id, task_id, action, target, details, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                tuple(
                    approval[key]
                    for key in (
                        "id",
                        "task_id",
                        "action",
                        "target",
                        "details",
                        "status",
                        "created_at",
                    )
                ),
            )
        return approval

    def poll(self, task_id: str, token: str, approval_id: str) -> dict[str, str]:
        """Read one approval after verifying the task token."""
        _validate_identifier(task_id, "task_id")
        token_hash = _validate_token(token)
        _validate_identifier(approval_id, "approval_id")
        with self._connection() as connection:
            self._authenticate(connection, task_id, token_hash)
            return self._public_approval(self._approval_row(connection, task_id, approval_id))  # type: ignore[return-value]

    def consume(self, task_id: str, token: str, approval_id: str) -> bool:
        """Consume an approved or rejected decision exactly once."""
        _validate_identifier(task_id, "task_id")
        token_hash = _validate_token(token)
        _validate_identifier(approval_id, "approval_id")
        with self._connection(write=True) as connection:
            self._authenticate(connection, task_id, token_hash)
            row = self._approval_row(connection, task_id, approval_id)
            if row["status"] not in ("approved", "rejected"):
                raise ValueError("approval decision is not consumable")
            approved = row["status"] == "approved"
            connection.execute(
                "UPDATE task_approval_requests SET status = 'consumed' WHERE task_id = ? AND id = ?",
                (task_id, approval_id),
            )
            return approved

    def pending(self, task_id: str) -> list[dict[str, str]]:
        """List pending approval requests; the caller must authorize the task owner."""
        _validate_identifier(task_id, "task_id")
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT id, task_id, action, target, details, status, created_at "
                "FROM task_approval_requests WHERE task_id = ? AND status = 'pending' "
                "ORDER BY created_at, id",
                (task_id,),
            ).fetchall()
        return [self._public_approval(row) for row in rows]  # type: ignore[misc]

    def resolve(self, task_id: str, approval_id: str, allow: bool) -> dict[str, str]:
        """Approve or reject one pending request for an active task."""
        _validate_identifier(task_id, "task_id")
        _validate_identifier(approval_id, "approval_id")
        if type(allow) is not bool:
            raise TypeError("allow must be a bool")
        with self._connection(write=True) as connection:
            owner = connection.execute(
                "SELECT state FROM task_owners WHERE task_id = ?", (task_id,)
            ).fetchone()
            if owner is None or owner["state"] != "active":
                raise ValueError("task is not active")
            row = self._approval_row(connection, task_id, approval_id)
            if row["status"] != "pending":
                raise ValueError("approval request has already been resolved")
            status = "approved" if allow else "rejected"
            connection.execute(
                "UPDATE task_approval_requests SET status = ? WHERE task_id = ? AND id = ?",
                (status, task_id, approval_id),
            )
            updated = dict(row)
            updated["status"] = status
            return self._public_approval(updated)  # type: ignore[arg-type,return-value]

    def close(self, task_id: str) -> None:
        """Close a task and cancel any pending or approved decision it still holds."""
        _validate_identifier(task_id, "task_id")
        with self._connection(write=True) as connection:
            owner = connection.execute(
                "SELECT state FROM task_owners WHERE task_id = ?", (task_id,)
            ).fetchone()
            if owner is None:
                raise ValueError("task not found")
            connection.execute(
                "UPDATE task_owners SET state = 'closed' WHERE task_id = ?", (task_id,)
            )
            connection.execute(
                "UPDATE task_approval_requests SET status = 'cancelled' "
                "WHERE task_id = ? AND status IN ('pending', 'approved')",
                (task_id,),
            )
