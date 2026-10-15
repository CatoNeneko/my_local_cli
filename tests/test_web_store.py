import pytest

from web.store import Store


@pytest.fixture
def database_path(tmp_path):
    return tmp_path / "web.sqlite3"


@pytest.fixture
def store(database_path):
    return Store(database_path)


def test_sessions_validate_titles_and_return_none_for_missing_ids(store):
    session = store.create_session("A title", "/workspace/project")

    assert session["title"] == "A title"
    assert session["workspace"] == "/workspace/project"
    assert store.get_session(session["id"]) == session
    assert store.list_sessions() == [session]
    assert store.get_session("missing") is None
    assert store.rename_session("missing", "Renamed") is None
    assert store.rename_session(session["id"], "Renamed")["title"] == "Renamed"

    for title in ("", "   ", "x" * 121):
        with pytest.raises(ValueError):
            store.create_session(title, "/workspace/project")
    with pytest.raises(ValueError):
        store.rename_session(session["id"], "x" * 121)


def test_messages_preserve_full_json_and_survive_reopening(database_path):
    store = Store(database_path)
    session = store.create_session("Conversation", "/workspace")
    original_messages = [
        {
            "id": "message-1",
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"id": "call-1", "function": {"name": "read_file", "arguments": {"path": "a.py"}}}
            ],
            "checkpoint": {"cursor": 7, "metadata": ["kept", {"nested": True}]},
        },
        {"id": "message-2", "role": "tool", "tool_name": "read_file", "content": "内容"},
    ]

    store.append_messages(session["id"], original_messages[:1])
    store.append_messages(session["id"], original_messages[1:])
    reopened = Store(database_path)

    assert reopened.messages(session["id"]) == original_messages
    assert reopened.messages("missing") == []
    with pytest.raises(KeyError):
        reopened.append_messages("missing", [{"role": "user", "content": "hello"}])


def test_runs_validate_state_fields_and_persist(database_path):
    store = Store(database_path)
    session = store.create_session("Runs", "/workspace")
    run = store.create_run(session["id"], {"id": "prompt-1", "content": "run this"})

    assert run["status"] == "queued"
    assert store.get_run(run["id"]) == run
    assert store.list_runs() == [run]
    assert store.get_run("missing") is None
    assert store.set_run("missing", status="running") is None

    updated = store.set_run(run["id"], status="running", pid=4321)
    assert updated["status"] == "running" and updated["pid"] == 4321
    updated = store.set_run(run["id"], status="succeeded", answer="done")
    assert updated["answer"] == "done"
    with pytest.raises(ValueError):
        store.set_run(run["id"], status="running")
    with pytest.raises(ValueError):
        store.set_run(run["id"], status="queued")
    with pytest.raises(ValueError):
        store.set_run(run["id"], extra="unsupported")

    reopened = Store(database_path)
    assert reopened.get_run(run["id"]) == updated
    with pytest.raises(KeyError):
        reopened.create_run("missing-session", "prompt")


def test_events_have_monotonic_per_run_ids_and_after_filter_survives_reopen(database_path):
    store = Store(database_path)
    session = store.create_session("Events", "/workspace")
    first_run = store.create_run(session["id"], "first")
    second_run = store.create_run(session["id"], "second")

    first = store.add_event(first_run["id"], "token", {"text": "你好", "index": 1})
    second = store.add_event(first_run["id"], "approval", {"approval_id": "approval-1"})
    independent = store.add_event(second_run["id"], "started", None)
    assert [first["id"], second["id"], independent["id"]] == [1, 2, 1]

    reopened = Store(database_path)
    assert reopened.events(first_run["id"]) == [first, second]
    assert reopened.events(first_run["id"], after=1) == [second]
    assert reopened.events(second_run["id"]) == [independent]


def test_approval_resolution_is_exactly_once_and_requires_an_active_run(store):
    session = store.create_session("Approvals", "/workspace")
    run = store.create_run(session["id"], "prompt")
    approval = store.create_approval(run["id"], "edit_file", "+value = 2")

    assert approval["status"] == "pending"
    assert store.pending_approvals(run["id"]) == [approval]
    resolved = store.resolve_approval(approval["id"], allow=True)
    assert resolved["status"] == "approved"
    assert store.resolve_approval(approval["id"], allow=False) is None
    assert store.get_approval(approval["id"]) == resolved
    assert store.pending_approvals(run["id"]) == []

    another = store.create_approval(run["id"], "run_tests", "test.py")
    store.set_run(run["id"], status="failed", error="execution failed")
    assert store.resolve_approval(another["id"], allow=True) is None
    assert store.get_approval(another["id"])["status"] == "pending"
    with pytest.raises(ValueError):
        store.create_approval(run["id"], "edit_file", "diff")


def test_interrupt_stale_runs_rejects_pending_approvals_and_is_idempotent(database_path):
    store = Store(database_path)
    session = store.create_session("Restart", "/workspace")
    queued = store.create_run(session["id"], "queued")
    running = store.create_run(session["id"], "running")
    waiting = store.create_run(session["id"], "waiting")
    succeeded = store.create_run(session["id"], "succeeded")
    store.set_run(running["id"], status="running")
    store.set_run(waiting["id"], status="waiting_approval")
    store.set_run(succeeded["id"], status="succeeded")
    approval = store.create_approval(waiting["id"], "edit_file", "+value")

    assert store.interrupt_stale_runs() == 3
    assert store.interrupt_stale_runs() == 0
    assert {run["id"]: run["status"] for run in store.list_runs()} == {
        queued["id"]: "interrupted",
        running["id"]: "interrupted",
        waiting["id"]: "interrupted",
        succeeded["id"]: "succeeded",
    }
    assert store.get_approval(approval["id"])["status"] == "rejected"
    assert store.pending_approvals(waiting["id"]) == []
