import concurrent.futures
import hashlib
import os
import sqlite3
import threading

import pytest

from harness.tasks.approvals import TaskApprovalStore


@pytest.fixture
def database_path(tmp_path):
    return tmp_path / "task-approvals.sqlite3"


@pytest.fixture
def store(database_path):
    return TaskApprovalStore(database_path)


def _registered(store, task_id="task-1", token="secret-task-token"):
    store.register(task_id, token, "/workspace/project")
    return task_id, token


def test_tokens_are_hashed_and_wrong_or_cross_task_tokens_are_rejected(store):
    task_id, token = _registered(store)
    second_id, second_token = _registered(store, "task-2", "another-secret-token")
    approval = store.create(task_id, token, "write_file", "src/app.py", "+value = 2")

    with sqlite3.connect(store.db_path) as connection:
        stored_hash = connection.execute(
            "SELECT token_hash FROM task_owners WHERE task_id = ?", (task_id,)
        ).fetchone()[0]
    assert stored_hash == hashlib.sha256(token.encode()).hexdigest()
    assert token not in stored_hash

    with pytest.raises(ValueError):
        store.create(task_id, "wrong-token", "write_file", "src/app.py", "+value = 2")
    with pytest.raises(ValueError):
        store.poll(task_id, second_token, approval["id"])
    with pytest.raises(ValueError):
        store.poll(second_id, second_token, approval["id"])


def test_public_results_never_contain_token_and_duplicate_pending_request_is_idempotent(store):
    task_id, token = _registered(store)
    first = store.create(task_id, token, "edit", "file.py", "change")
    duplicate = store.create(task_id, token, "edit", "file.py", "change")

    assert duplicate == first
    assert token not in repr(first)
    assert token not in repr(store.poll(task_id, token, first["id"]))
    assert token not in repr(store.pending(task_id))


def test_approval_decision_and_consumption_are_each_one_shot(store):
    task_id, token = _registered(store)
    approval = store.create(task_id, token, "run", "tests", "run the test suite")

    resolved = store.resolve(task_id, approval["id"], True)
    assert resolved["status"] == "approved"
    with pytest.raises(ValueError):
        store.resolve(task_id, approval["id"], False)
    assert store.consume(task_id, token, approval["id"]) is True
    assert store.poll(task_id, token, approval["id"])["status"] == "consumed"
    with pytest.raises(ValueError):
        store.consume(task_id, token, approval["id"])

    rejected = store.create(task_id, token, "delete", "old.py", "remove old file")
    assert store.resolve(task_id, rejected["id"], False)["status"] == "rejected"
    assert store.consume(task_id, token, rejected["id"]) is False
    with pytest.raises(ValueError):
        store.consume(task_id, token, rejected["id"])


def test_close_cancels_pending_and_unconsumed_approved_requests(store):
    task_id, token = _registered(store)
    pending = store.create(task_id, token, "edit", "pending.py", "pending change")
    approved = store.create(task_id, token, "edit", "approved.py", "approved change")
    store.resolve(task_id, approved["id"], True)

    store.close(task_id)
    assert store.pending(task_id) == []
    with sqlite3.connect(store.db_path) as connection:
        statuses = dict(
            connection.execute(
                "SELECT id, status FROM task_approval_requests WHERE task_id = ?", (task_id,)
            )
        )
    assert statuses == {pending["id"]: "cancelled", approved["id"]: "cancelled"}
    with pytest.raises(ValueError):
        store.consume(task_id, token, approved["id"])
    with pytest.raises(ValueError):
        store.create(task_id, token, "edit", "new.py", "new change")


def test_two_concurrent_resolutions_can_only_commit_one_decision(store):
    task_id, _ = _registered(store)
    approval = store.create(task_id, "secret-task-token", "edit", "file.py", "change")
    barrier = threading.Barrier(2)

    def resolve(allow):
        barrier.wait()
        try:
            return store.resolve(task_id, approval["id"], allow)
        except ValueError:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(resolve, (True, False)))

    assert sum(result is not None for result in results) == 1
    assert store.pending(task_id) == []
    assert store.poll(task_id, "secret-task-token", approval["id"])["status"] in {
        "approved",
        "rejected",
    }


def test_limits_and_private_filesystem_permissions_are_enforced(database_path):
    store = TaskApprovalStore(database_path)
    task_id, token = _registered(store)
    for action, target, details in (
        ("", "target", "details"),
        ("a" * 101, "target", "details"),
        ("action", "", "details"),
        ("action", "t" * 4097, "details"),
        ("action", "target", "d" * 20001),
    ):
        with pytest.raises(ValueError):
            store.create(task_id, token, action, target, details)

    for index in range(3):
        store.create(task_id, token, "action", f"target-{index}", "details")
    with pytest.raises(ValueError):
        store.create(task_id, token, "action", "target-4", "details")

    assert os.stat(database_path.parent).st_mode & 0o777 == 0o700
    assert os.stat(database_path).st_mode & 0o777 == 0o600


def test_database_and_parent_symlinks_are_rejected(tmp_path):
    database_path = tmp_path / "actual.sqlite3"
    TaskApprovalStore(database_path)
    symlink_db = tmp_path / "linked.sqlite3"
    symlink_db.symlink_to(database_path)
    with pytest.raises(ValueError):
        TaskApprovalStore(symlink_db)

    real_parent = tmp_path / "private"
    real_parent.mkdir()
    symlink_parent = tmp_path / "linked-parent"
    symlink_parent.symlink_to(real_parent, target_is_directory=True)
    with pytest.raises(ValueError):
        TaskApprovalStore(symlink_parent / "approvals.sqlite3")
