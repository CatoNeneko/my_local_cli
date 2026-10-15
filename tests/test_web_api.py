from fastapi.testclient import TestClient
import pytest

from web.app import create_app
from web.settings import Settings


@pytest.fixture
def settings(tmp_path):
    return Settings(state_dir=tmp_path / ".ai-cli" / "web", workspace_root=tmp_path, model="")


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def create_session(client, title, workspace):
    response = client.post("/api/sessions", json={"title": title, "workspace": str(workspace)})
    assert response.status_code == 201, response.text
    return response.json()


def test_health_session_rename_and_full_messages(client, settings):
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["model_ready"] is False

    session = create_session(client, "Initial title", settings.workspace_root)
    assert client.get("/api/sessions").json() == [session]

    renamed = client.post(f"/api/sessions/{session['id']}/rename", json={"title": "Updated title"})
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Updated title"

    original_message = {
        "id": "message-1",
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {"id": "call-1", "function": {"name": "read_file", "arguments": {"path": "a.py"}}}
        ],
        "checkpoint": {"node": "model", "cursor": 3},
    }
    client.app.state.store.append_messages(session["id"], [original_message])
    messages = client.get(f"/api/sessions/{session['id']}/messages")
    assert messages.status_code == 200
    assert messages.json() == [original_message]


def test_run_requires_configured_model_and_rejects_escaping_workspace(client, settings):
    session = create_session(client, "No model", settings.workspace_root)
    response = client.post(
        f"/api/sessions/{session['id']}/runs", json={"message": "Explain the project"}
    )
    assert response.status_code == 503

    escaped = client.post(
        "/api/sessions",
        json={"title": "Outside", "workspace": str(settings.workspace_root.parent)},
    )
    assert escaped.status_code == 400


def test_external_origin_cannot_write(client, settings):
    response = client.post(
        "/api/sessions",
        json={"title": "Blocked", "workspace": str(settings.workspace_root)},
        headers={"Origin": "https://attacker.example"},
    )
    assert response.status_code == 403


def test_memories_support_crud_and_are_isolated_by_session_workspace(client, settings):
    first_workspace = settings.workspace_root / "first"
    second_workspace = settings.workspace_root / "second"
    first_workspace.mkdir()
    second_workspace.mkdir()
    first = create_session(client, "First", first_workspace)
    second = create_session(client, "Second", second_workspace)

    created = client.post(
        f"/api/sessions/{first['id']}/memories", json={"content": "Remember the cobalt build rule"}
    )
    assert created.status_code == 201
    memory = created.json()
    assert memory["content"] == "Remember the cobalt build rule"

    first_memories = client.get(f"/api/sessions/{first['id']}/memories")
    second_memories = client.get(f"/api/sessions/{second['id']}/memories")
    assert [item["id"] for item in first_memories.json()] == [memory["id"]]
    assert second_memories.json() == []

    updated = client.patch(
        f"/api/memories/{memory['id']}", json={"content": "Updated cobalt build rule"}
    )
    assert updated.status_code == 200
    assert updated.json()["content"] == "Updated cobalt build rule"
    assert (
        client.get(f"/api/sessions/{first['id']}/memories").json()[0]["content"]
        == "Updated cobalt build rule"
    )

    deleted = client.delete(f"/api/memories/{memory['id']}")
    assert deleted.status_code == 200 and deleted.json()["ok"] is True
    assert client.get(f"/api/sessions/{first['id']}/memories").json() == []


def test_index_search_and_file_routes_keep_sources_inside_workspace(client, settings):
    workspace = settings.workspace_root / "project"
    workspace.mkdir()
    (workspace / "helper.py").write_text(
        "# cobalt_anchor\ndef build():\n    return 'safe'\n", encoding="utf-8"
    )
    (workspace / ".env").write_text("SECRET=value\n", encoding="utf-8")
    session = create_session(client, "Project", workspace)

    indexed = client.post(f"/api/sessions/{session['id']}/index")
    assert indexed.status_code == 200
    assert indexed.json()["files"] == 1

    search = client.post(f"/api/sessions/{session['id']}/search", json={"query": "cobalt_anchor"})
    assert search.status_code == 200
    hits = search.json()
    assert hits and hits[0]["path"] == "helper.py"
    assert hits[0]["citation"].startswith("helper.py:")

    listing = client.get(f"/api/sessions/{session['id']}/files")
    assert listing.status_code == 200
    assert listing.json()["files"] == ["helper.py"]

    file_contents = client.get(f"/api/sessions/{session['id']}/file", params={"path": "helper.py"})
    assert file_contents.status_code == 200
    assert "cobalt_anchor" in file_contents.json()["content"]

    traversal = client.get(f"/api/sessions/{session['id']}/file", params={"path": "../outside.txt"})
    assert traversal.status_code == 400
    hidden = client.get(f"/api/sessions/{session['id']}/file", params={"path": ".env"})
    assert hidden.status_code == 400


def test_restart_interrupts_active_run_rejects_approval_and_allow_requires_bool(settings):
    with TestClient(create_app(settings)) as first_client:
        store = first_client.app.state.store
        session = store.create_session("Restart", str(settings.workspace_root))
        run = store.create_run(session["id"], "resume after restart")
        store.set_run(run["id"], status="waiting_approval")
        approval = store.create_approval(run["id"], "edit_file", "+value = 2")

    with TestClient(create_app(settings)) as restarted_client:
        status = restarted_client.get(f"/api/runs/{run['id']}")
        assert status.status_code == 200
        assert status.json()["status"] == "interrupted"
        assert restarted_client.app.state.store.get_approval(approval["id"])["status"] == "rejected"
        assert restarted_client.app.state.store.pending_approvals(run["id"]) == []

        invalid = restarted_client.post(f"/api/approvals/{approval['id']}", json={"allow": "true"})
        assert invalid.status_code == 422
