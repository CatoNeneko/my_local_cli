import json

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command, interrupt
from langgraph.errors import GraphInterrupt

from web.recovery import Recovery, CURRENT_TOOL, ToolPause
from web.store import Store
from web.workflow import build_graph
from web.knowledge import KnowledgeStore, HashTokenEmbeddings


def test_pause_resume_does_not_repeat_completed_tools(tmp_path, monkeypatch):
    import web.workflow as workflow
    from workspace import use_workspace
    from config import approval_config
    import permissions
    from approval import task_scope

    store = Store(tmp_path / ".ai-cli/web/workbench.sqlite")
    knowledge = KnowledgeStore(
        tmp_path / ".ai-cli/web/knowledge.sqlite", embeddings=HashTokenEmbeddings()
    )
    session = store.create_session("resume", str(tmp_path))
    run = store.create_run(session["id"], "改成加法")
    store.set_run(run["id"], status="running")
    store.append_messages(session["id"], [{"role": "user", "content": "改成加法"}])
    target = tmp_path / "calc.py"
    target.write_text("return a-b\n")
    replies = iter(
        [
            {
                "content": "",
                "tool_calls": [
                    {
                        "id": "read",
                        "function": {"name": "read_file", "arguments": {"path": "calc.py"}},
                    },
                    {
                        "id": "edit",
                        "function": {
                            "name": "edit_file",
                            "arguments": {"path": "calc.py", "new_content": "return a+b\n"},
                        },
                    },
                ],
            },
            {"content": "done"},
        ]
    )
    monkeypatch.setattr(workflow, "request_message", lambda *a, **k: next(replies))
    monkeypatch.setattr("compaction.maybe_compact", lambda *a: None)
    monkeypatch.setitem(approval_config, "mode", "manual")
    recovery = Recovery(store.db_path)
    calls = []
    actual = workflow.execute_tool

    def execute(name, args):
        calls.append(name)
        return actual(name, args)

    monkeypatch.setattr(workflow, "execute_tool", execute)

    def confirm(name, path, details=""):
        current = CURRENT_TOOL.get()
        receipt = recovery.get(*current)
        approval = store.get_approval(receipt["approval_id"]) if receipt["approval_id"] else None
        if not approval:
            approval = store.create_approval(run["id"], name, "diff")
            recovery.awaiting(*current, approval["id"])
            store.set_run(run["id"], status="waiting_approval")
        try:
            value = interrupt({"approval_id": approval["id"]})
        except GraphInterrupt as interruption:
            raise ToolPause(interruption)
        return value["allow"] and store.get_approval(approval["id"])["status"] == "approved"

    monkeypatch.setattr(permissions, "confirm_tool", confirm)
    config = {"configurable": {"thread_id": run["id"]}}
    checkpoint = str(tmp_path / ".ai-cli/web/checkpoints.sqlite")
    with use_workspace(tmp_path), task_scope("改成加法"):
        with SqliteSaver.from_conn_string(checkpoint) as saver:
            graph = build_graph(store, knowledge, run, session, lambda *a: None, saver)
            paused = graph.invoke(
                {"messages": store.messages(session["id"]), "rounds": 0, "tool_count": 0}, config
            )
            assert paused["__interrupt__"]
            assert target.read_text() == "return a-b\n"
            assert calls == ["read_file", "edit_file"]
        # 模拟图重建与新进程：不是保留内存图对象继续执行。
        with SqliteSaver.from_conn_string(checkpoint) as saver:
            approval = store.pending_approvals(run["id"])[0]
            store.resolve_approval(approval["id"], True)
            result = build_graph(store, knowledge, run, session, lambda *a: None, saver).invoke(
                Command(resume={"approval_id": approval["id"], "allow": True}), config
            )
        assert result["answer"] == "done"
        assert target.read_text() == "return a+b\n"
        assert calls.count("read_file") == 1
        assert [m["role"] for m in store.messages(session["id"])] == [
            "user",
            "assistant",
            "tool",
            "tool",
            "assistant",
        ]


def test_restart_preserves_only_durable_paused_approval(tmp_path):
    store = Store(tmp_path / "state.sqlite")
    recovery = Recovery(store.db_path)
    session = store.create_session("restart", str(tmp_path))
    durable = store.create_run(session["id"], "durable")
    unsafe = store.create_run(session["id"], "unsafe")
    for run in (durable, unsafe):
        store.set_run(run["id"], status="waiting_approval")
    good = store.create_approval(durable["id"], "edit", "diff")
    bad = store.create_approval(unsafe["id"], "edit", "diff")
    recovery.begin(durable["id"], "1:0", "hash")
    recovery.awaiting(durable["id"], "1:0", good["id"])
    recovery.paused(durable["id"])
    assert recovery.recover_runs(store) == 1
    assert store.get_run(durable["id"])["status"] == "waiting_approval"
    assert store.get_approval(good["id"])["status"] == "pending"
    assert store.get_run(unsafe["id"])["status"] == "interrupted"
    assert store.get_approval(bad["id"])["status"] == "rejected"


def test_receipt_and_history_batch_are_idempotent(tmp_path):
    store = Store(tmp_path / "state.sqlite")
    recovery = Recovery(store.db_path)
    session = store.create_session("one", str(tmp_path))
    run = store.create_run(session["id"], "task")
    assert recovery.begin(run["id"], "1:0", "hash") is None
    assert recovery.begin(run["id"], "1:0", "hash")["stage"] == "started"
    recovery.complete(run["id"], "1:0", {"ok": True})
    assert json.loads(recovery.get(run["id"], "1:0")["result"])["ok"]
    messages = [{"role": "assistant", "content": "done"}]
    assert recovery.append_once(run["id"], "final", session["id"], messages)
    assert not recovery.append_once(run["id"], "final", session["id"], messages)
    assert len(store.messages(session["id"])) == 1
