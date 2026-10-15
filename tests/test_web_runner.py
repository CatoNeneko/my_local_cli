import sys
import time

import pytest
from web.runner import Runner
from web.settings import Settings
from web.store import Store


def wait(predicate, timeout=8):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.02)
    raise AssertionError("task did not reach expected state")


@pytest.fixture
def runner(tmp_path, monkeypatch):
    monkeypatch.setenv("WEB_TEST_KEY", "fixture-not-a-real-key")
    settings = Settings(
        tmp_path / ".ai-cli/web",
        tmp_path,
        model="fixture",
        api_key_env="WEB_TEST_KEY",
        max_workers=1,
    )
    store = Store(settings.state_dir / "workbench.sqlite")
    value = Runner(settings, store)
    yield value, store
    value.close()


def stub_process(monkeypatch, code):
    import web.runner as module

    real = module.subprocess.Popen
    monkeypatch.setattr(
        module.subprocess,
        "Popen",
        lambda argv, **kwargs: real([sys.executable, "-c", code], **kwargs),
    )


def test_unwritable_diagnostic_log_does_not_prevent_failure_status(runner, monkeypatch, tmp_path):
    from web.diagnostics import DiagnosticLog

    def fail_log(*args, **kwargs):
        raise OSError("private logging unavailable")

    monkeypatch.setattr(DiagnosticLog, "append", fail_log)
    stub_process(monkeypatch, "import sys; sys.stdin.readline(); sys.exit(2)")
    value, store = runner
    session = store.create_session("diagnostic", str(tmp_path))
    run = value.submit(session["id"], "check failure")
    wait(lambda: store.get_run(run["id"])["status"] == "failed")
    assert any(event["kind"] == "diagnostic" for event in store.events(run["id"]))


def test_real_process_events_and_session_serialization(runner, monkeypatch, tmp_path):
    value, store = runner
    code = """import sys,json,time
p=json.loads(sys.stdin.readline())
time.sleep(.15)
print(json.dumps({'kind':'token','payload':{'text':p['run_id']}}),flush=True)
print(json.dumps({'kind':'done','payload':{'status':'succeeded','answer':'fixture','error':''}}),flush=True)
"""
    stub_process(monkeypatch, code)
    s = store.create_session("one", str(tmp_path))
    run = value.submit(s["id"], "hello")
    with pytest.raises(ValueError):
        value.submit(s["id"], "double")
    wait(lambda: store.get_run(run["id"])["status"] == "succeeded")
    assert any(e["kind"] == "token" for e in store.events(run["id"]))
    assert store.get_run(run["id"])["answer"] == "fixture"


def test_cancel_queued_run_never_starts(runner, monkeypatch, tmp_path):
    value, store = runner
    stub_process(monkeypatch, "import sys,time; sys.stdin.readline(); time.sleep(30)")
    first = store.create_session("one", str(tmp_path))
    second = store.create_session("two", str(tmp_path))
    one = value.submit(first["id"], "first")
    wait(lambda: store.get_run(one["id"])["status"] == "running")
    two = value.submit(second["id"], "second")
    assert value.cancel(two["id"])
    assert store.get_run(two["id"])["status"] == "cancelled"
    assert store.get_run(two["id"])["pid"] is None
    assert value.cancel(one["id"])


def test_browser_approval_is_bound_to_persisted_pending_decision(runner, monkeypatch, tmp_path):
    value, store = runner
    code = """import sys,json
from web.store import Store
p=json.loads(sys.stdin.readline()); s=Store(p['db_path'])
a=s.create_approval(p['run_id'],'edit_file','-old\\n+new')
s.set_run(p['run_id'],status='waiting_approval')
print(json.dumps({'kind':'approval','payload':a}),flush=True)
r=json.loads(sys.stdin.readline())
accepted=s.get_approval(a['id'])['status']=='approved' and r['approval_id']==a['id']
print(json.dumps({'kind':'done','payload':{'status':'succeeded','answer':str(accepted),'error':''}}),flush=True)
"""
    stub_process(monkeypatch, code)
    session = store.create_session("approval", str(tmp_path))
    run = value.submit(session["id"], "edit")
    approval = wait(lambda: store.pending_approvals(run["id"]))[0]
    assert value.approve(approval["id"], True)["status"] == "approved"
    assert value.approve(approval["id"], True) is None
    wait(lambda: store.get_run(run["id"])["status"] == "succeeded")
    assert store.get_run(run["id"])["answer"] == "True"


def test_paused_task_releases_single_worker_and_resumes(runner, monkeypatch, tmp_path):
    value, store = runner
    code = """import sys,json
from web.store import Store
from web.recovery import Recovery
p=json.loads(sys.stdin.readline()); s=Store(p['db_path'])
if p.get('resume') or s.get_run(p['run_id'])['message']=='second':
 print(json.dumps({'kind':'done','payload':{'status':'succeeded','answer':'continued','error':''}}),flush=True)
else:
 a=s.create_approval(p['run_id'],'edit','diff')
 r=Recovery(s.db_path); r.begin(p['run_id'],'1:0','hash'); r.awaiting(p['run_id'],'1:0',a['id'])
 s.set_run(p['run_id'],status='waiting_approval')
 print(json.dumps({'kind':'approval','payload':a}),flush=True)
 print(json.dumps({'kind':'paused','payload':{'status':'waiting_approval'}}),flush=True)
"""
    stub_process(monkeypatch, code)
    one = store.create_session("one", str(tmp_path))
    two = store.create_session("two", str(tmp_path))
    first = value.submit(one["id"], "first")
    wait(
        lambda: (
            store.get_run(first["id"])["status"] == "waiting_approval"
            and first["id"] not in value.jobs
        )
    )
    second = value.submit(two["id"], "second")
    wait(lambda: store.get_run(second["id"])["status"] == "succeeded")
    approval = store.pending_approvals(first["id"])[0]
    assert value.approve(approval["id"], True)
    wait(lambda: store.get_run(first["id"])["status"] == "succeeded")
