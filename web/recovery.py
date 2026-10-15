"""副作用日志：完成的不重放，状态不明的调用不假定未发生。"""

from contextvars import ContextVar
from contextlib import contextmanager
import json
import sqlite3

CURRENT_TOOL = ContextVar("web_current_tool", default=None)


class ToolPause(BaseException):
    """穿过旧 Runtime 的普通 Exception 处理，到图节点才恢复 GraphInterrupt。"""

    def __init__(self, interrupt):
        self.interrupt = interrupt


class Recovery:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        with self.connection() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS tool_receipts (
                run_id TEXT NOT NULL, call_key TEXT NOT NULL, signature TEXT NOT NULL,
                stage TEXT NOT NULL, result TEXT, approval_id TEXT,
                PRIMARY KEY(run_id,call_key))""")
            db.execute("""CREATE TABLE IF NOT EXISTS persisted_batches (
                run_id TEXT NOT NULL, batch_key TEXT NOT NULL, PRIMARY KEY(run_id,batch_key))""")

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.db_path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, run_id, key):
        with self.connection() as db:
            row = db.execute(
                "SELECT * FROM tool_receipts WHERE run_id=? AND call_key=?", (run_id, key)
            ).fetchone()
        return dict(row) if row else None

    def begin(self, run_id, key, signature):
        with self.connection() as db:
            row = db.execute(
                "SELECT * FROM tool_receipts WHERE run_id=? AND call_key=?", (run_id, key)
            ).fetchone()
            if row is not None:
                if row["signature"] != signature:
                    raise ValueError("恢复工具参数与记录不一致")
                return dict(row)
            db.execute(
                "INSERT INTO tool_receipts VALUES (?,?,?,'started',NULL,NULL)",
                (run_id, key, signature),
            )
        return None

    def awaiting(self, run_id, key, approval_id):
        with self.connection() as db:
            db.execute(
                "UPDATE tool_receipts SET stage='awaiting',approval_id=? WHERE run_id=? AND call_key=?",
                (approval_id, run_id, key),
            )

    def complete(self, run_id, key, result):
        with self.connection() as db:
            db.execute(
                "UPDATE tool_receipts SET stage='completed',result=? WHERE run_id=? AND call_key=?",
                (json.dumps(result, ensure_ascii=False), run_id, key),
            )

    def paused(self, run_id):
        with self.connection() as db:
            db.execute(
                "UPDATE tool_receipts SET stage='paused' WHERE run_id=? AND stage='awaiting'",
                (run_id,),
            )

    def executing(self, run_id, key):
        with self.connection() as db:
            db.execute(
                "UPDATE tool_receipts SET stage='started' WHERE run_id=? AND call_key=?",
                (run_id, key),
            )

    def append_once(self, run_id, key, session_id, messages):
        with self.connection() as db:
            inserted = db.execute(
                "INSERT OR IGNORE INTO persisted_batches VALUES (?,?)", (run_id, key)
            )
            if not inserted.rowcount:
                return False
            ordinal = db.execute(
                "SELECT COALESCE(MAX(ordinal),0) FROM messages WHERE session_id=?", (session_id,)
            ).fetchone()[0]
            db.executemany(
                "INSERT INTO messages VALUES (?,?,?)",
                [
                    (session_id, ordinal + i + 1, json.dumps(m, ensure_ascii=False))
                    for i, m in enumerate(messages)
                ],
            )
        return True

    def recover_runs(self, store):
        """只有图在审批前确认已停下，才能保留旧审批；其余状态标为中断。"""
        count = 0
        for run in store.list_runs():
            if run["status"] not in ("queued", "running", "waiting_approval"):
                continue
            with self.connection() as db:
                paused = db.execute(
                    "SELECT 1 FROM tool_receipts WHERE run_id=? AND stage='paused'", (run["id"],)
                ).fetchone()
            if run["status"] == "waiting_approval" and paused:
                continue
            for approval in store.pending_approvals(run["id"]):
                store.resolve_approval(approval["id"], False)
            store.set_run(run["id"], status="interrupted", error="服务重启；恢复前必须核对实际状态")
            count += 1
        return count
