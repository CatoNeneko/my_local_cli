"""SQLite-backed persistence for the local web interface."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


_ACTIVE_RUN_STATUSES = ("queued", "running", "waiting_approval")
_SETTABLE_RUN_STATUSES = frozenset(
    (*_ACTIVE_RUN_STATUSES[1:], "succeeded", "failed", "cancelled", "interrupted")
)
_TERMINAL_RUN_STATUSES = frozenset(("succeeded", "failed", "cancelled", "interrupted"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _dump_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise ValueError("value must be JSON serializable") from exc


def _load_json(value: str) -> Any:
    return json.loads(value)


class Store:
    """Persist web sessions, messages, runs, events, and approvals in SQLite."""

    _TIMEOUT_SECONDS = 10.0

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._uri = self.db_path.startswith("file:")
        if self.db_path != ":memory:" and not self._uri:
            Path(self.db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        with self._connection(write=True) as connection:
            self._create_schema(connection)

    @contextmanager
    def _connection(self, *, write: bool = False) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(
            self.db_path,
            timeout=self._TIMEOUT_SECONDS,
            isolation_level=None,
            uri=self._uri,
        )
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(f"PRAGMA busy_timeout = {int(self._TIMEOUT_SECONDS * 1000)}")
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
        statements = (
            """CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 120),
                workspace TEXT NOT NULL,
                created_at TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS messages (
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                ordinal INTEGER NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (session_id, ordinal)
            )""",
            """CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                message TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN
                    ('queued', 'running', 'waiting_approval', 'succeeded', 'failed', 'cancelled', 'interrupted')),
                created_at TEXT NOT NULL,
                answer TEXT NOT NULL DEFAULT '',
                error TEXT NOT NULL DEFAULT '',
                pid INTEGER
            )""",
            """CREATE TABLE IF NOT EXISTS events (
                run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                sequence INTEGER NOT NULL CHECK (sequence > 0),
                kind TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (run_id, sequence)
            )""",
            """CREATE TABLE IF NOT EXISTS approvals (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                action TEXT NOT NULL,
                diff TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
                created_at TEXT NOT NULL,
                resolved_at TEXT
            )""",
            "CREATE INDEX IF NOT EXISTS runs_by_created_at ON runs(created_at, id)",
            "CREATE INDEX IF NOT EXISTS approvals_by_run_status ON approvals(run_id, status)",
        )
        for statement in statements:
            connection.execute(statement)

    @staticmethod
    def _validate_title(title: str) -> None:
        if not isinstance(title, str):
            raise TypeError("title must be a string")
        if not title.strip() or len(title) > 120:
            raise ValueError("title must contain 1 to 120 characters")

    @staticmethod
    def _session_from_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return {
            "id": row["id"],
            "title": row["title"],
            "workspace": row["workspace"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _run_from_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return {
            "id": row["id"],
            "session_id": row["session_id"],
            "message": _load_json(row["message"]),
            "status": row["status"],
            "created_at": row["created_at"],
            "answer": row["answer"],
            "error": row["error"],
            "pid": row["pid"],
        }

    @staticmethod
    def _approval_from_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return {
            "id": row["id"],
            "run_id": row["run_id"],
            "action": row["action"],
            "diff": row["diff"],
            "status": row["status"],
        }

    def create_session(self, title: str, workspace: str) -> dict[str, Any]:
        self._validate_title(title)
        if not isinstance(workspace, str):
            raise TypeError("workspace must be a string")
        session = {
            "id": str(uuid.uuid4()),
            "title": title,
            "workspace": workspace,
            "created_at": _now(),
        }
        with self._connection(write=True) as connection:
            connection.execute(
                "INSERT INTO sessions (id, title, workspace, created_at) VALUES (?, ?, ?, ?)",
                (session["id"], session["title"], session["workspace"], session["created_at"]),
            )
        return session

    def list_sessions(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM sessions ORDER BY created_at, id").fetchall()
        return [self._session_from_row(row) for row in rows]  # type: ignore[misc]

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return self._session_from_row(row)

    def rename_session(self, session_id: str, title: str) -> dict[str, Any] | None:
        self._validate_title(title)
        with self._connection(write=True) as connection:
            connection.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))
            row = connection.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return self._session_from_row(row)

    def messages(self, session_id: str) -> list[dict[str, Any]]:
        with self._connection() as connection:
            exists = connection.execute(
                "SELECT 1 FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if exists is None:
                return []
            rows = connection.execute(
                "SELECT payload FROM messages WHERE session_id = ? ORDER BY ordinal", (session_id,)
            ).fetchall()
        return [_load_json(row["payload"]) for row in rows]

    def append_messages(self, session_id: str, messages: list[dict[str, Any]]) -> None:
        if not isinstance(messages, list):
            raise TypeError("messages must be a list")
        payloads = []
        for message in messages:
            if not isinstance(message, dict):
                raise TypeError("each message must be a dictionary")
            payloads.append(_dump_json(message))
        with self._connection(write=True) as connection:
            if (
                connection.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,)).fetchone()
                is None
            ):
                raise KeyError(f"unknown session: {session_id}")
            row = connection.execute(
                "SELECT COALESCE(MAX(ordinal), 0) AS last_ordinal FROM messages WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            first_ordinal = int(row["last_ordinal"]) + 1
            connection.executemany(
                "INSERT INTO messages (session_id, ordinal, payload) VALUES (?, ?, ?)",
                (
                    (session_id, first_ordinal + offset, payload)
                    for offset, payload in enumerate(payloads)
                ),
            )

    def create_run(self, session_id: str, message: Any) -> dict[str, Any]:
        encoded_message = _dump_json(message)
        run = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "message": message,
            "status": "queued",
            "created_at": _now(),
            "answer": "",
            "error": "",
            "pid": None,
        }
        with self._connection(write=True) as connection:
            if (
                connection.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,)).fetchone()
                is None
            ):
                raise KeyError(f"unknown session: {session_id}")
            connection.execute(
                "INSERT INTO runs (id, session_id, message, status, created_at, answer, error, pid) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run["id"],
                    session_id,
                    encoded_message,
                    run["status"],
                    run["created_at"],
                    run["answer"],
                    run["error"],
                    run["pid"],
                ),
            )
        return run

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return self._run_from_row(row)

    def list_runs(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM runs ORDER BY created_at, id").fetchall()
        return [self._run_from_row(row) for row in rows]  # type: ignore[misc]

    def set_run(self, run_id: str, **fields: Any) -> dict[str, Any] | None:
        allowed_fields = {"status", "answer", "error", "pid"}
        unknown_fields = set(fields) - allowed_fields
        if unknown_fields:
            raise ValueError(f"unsupported run fields: {', '.join(sorted(unknown_fields))}")
        if "status" in fields and fields["status"] not in _SETTABLE_RUN_STATUSES:
            raise ValueError("unsupported run status")
        for field in ("answer", "error"):
            if field in fields and not isinstance(fields[field], str):
                raise TypeError(f"{field} must be a string")
        if (
            "pid" in fields
            and fields["pid"] is not None
            and (isinstance(fields["pid"], bool) or not isinstance(fields["pid"], int))
        ):
            raise TypeError("pid must be an integer or None")

        with self._connection(write=True) as connection:
            row = connection.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
            if row is None:
                return None
            if (
                "status" in fields
                and row["status"] in _TERMINAL_RUN_STATUSES
                and fields["status"] != row["status"]
            ):
                raise ValueError("terminal runs cannot change status")
            if fields:
                assignments = ", ".join(f"{field} = ?" for field in fields)
                connection.execute(
                    f"UPDATE runs SET {assignments} WHERE id = ?",
                    (*fields.values(), run_id),
                )
                row = connection.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return self._run_from_row(row)

    def add_event(self, run_id: str, kind: str, payload: Any) -> dict[str, Any]:
        if not isinstance(kind, str) or not kind:
            raise ValueError("kind must be a non-empty string")
        encoded_payload = _dump_json(payload)
        with self._connection(write=True) as connection:
            if connection.execute("SELECT 1 FROM runs WHERE id = ?", (run_id,)).fetchone() is None:
                raise KeyError(f"unknown run: {run_id}")
            row = connection.execute(
                "SELECT COALESCE(MAX(sequence), 0) + 1 AS next_sequence FROM events WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            sequence = int(row["next_sequence"])
            connection.execute(
                "INSERT INTO events (run_id, sequence, kind, payload, created_at) VALUES (?, ?, ?, ?, ?)",
                (run_id, sequence, kind, encoded_payload, _now()),
            )
        return {"id": sequence, "kind": kind, "payload": payload}

    def events(self, run_id: str, after: int = 0) -> list[dict[str, Any]]:
        if isinstance(after, bool) or not isinstance(after, int) or after < 0:
            raise ValueError("after must be a non-negative integer")
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT sequence, kind, payload FROM events WHERE run_id = ? AND sequence > ? ORDER BY sequence",
                (run_id, after),
            ).fetchall()
        return [
            {"id": row["sequence"], "kind": row["kind"], "payload": _load_json(row["payload"])}
            for row in rows
        ]

    def create_approval(self, run_id: str, action: str, diff: str) -> dict[str, Any]:
        if not isinstance(action, str) or not isinstance(diff, str):
            raise TypeError("action and diff must be strings")
        approval = {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "action": action,
            "diff": diff,
            "status": "pending",
        }
        with self._connection(write=True) as connection:
            row = connection.execute("SELECT status FROM runs WHERE id = ?", (run_id,)).fetchone()
            if row is None:
                raise KeyError(f"unknown run: {run_id}")
            if row["status"] not in _ACTIVE_RUN_STATUSES:
                raise ValueError("approval requires an active run")
            connection.execute(
                "INSERT INTO approvals (id, run_id, action, diff, status, created_at) "
                "VALUES (?, ?, ?, ?, 'pending', ?)",
                (approval["id"], run_id, action, diff, _now()),
            )
        return approval

    def resolve_approval(self, approval_id: str, allow: bool) -> dict[str, Any] | None:
        if not isinstance(allow, bool):
            raise TypeError("allow must be a boolean")
        with self._connection(write=True) as connection:
            row = connection.execute(
                "SELECT a.*, r.status AS run_status FROM approvals AS a "
                "JOIN runs AS r ON r.id = a.run_id WHERE a.id = ?",
                (approval_id,),
            ).fetchone()
            if (
                row is None
                or row["status"] != "pending"
                or row["run_status"] not in _ACTIVE_RUN_STATUSES
            ):
                return None
            new_status = "approved" if allow else "rejected"
            connection.execute(
                "UPDATE approvals SET status = ?, resolved_at = ? WHERE id = ? AND status = 'pending'",
                (new_status, _now(), approval_id),
            )
            updated = connection.execute(
                "SELECT * FROM approvals WHERE id = ?", (approval_id,)
            ).fetchone()
        return self._approval_from_row(updated)

    def get_approval(self, approval_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM approvals WHERE id = ?", (approval_id,)
            ).fetchone()
        return self._approval_from_row(row)

    def pending_approvals(self, run_id: str) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM approvals WHERE run_id = ? AND status = 'pending' ORDER BY rowid",
                (run_id,),
            ).fetchall()
        return [self._approval_from_row(row) for row in rows]  # type: ignore[misc]

    def interrupt_stale_runs(self) -> int:
        placeholders = ", ".join("?" for _ in _ACTIVE_RUN_STATUSES)
        active = tuple(_ACTIVE_RUN_STATUSES)
        with self._connection(write=True) as connection:
            now = _now()
            connection.execute(
                "UPDATE approvals SET status = 'rejected', resolved_at = ? "
                f"WHERE status = 'pending' AND run_id IN (SELECT id FROM runs WHERE status IN ({placeholders}))",
                (now, *active),
            )
            cursor = connection.execute(
                f"UPDATE runs SET status = 'interrupted' WHERE status IN ({placeholders})", active
            )
            return cursor.rowcount
