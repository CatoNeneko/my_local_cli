from concurrent.futures import ThreadPoolExecutor
import sqlite3
from types import ModuleType
import sys

import pytest
from langchain_core.embeddings import Embeddings

from web.knowledge import HashTokenEmbeddings, KnowledgeStore


@pytest.fixture
def knowledge(tmp_path):
    return KnowledgeStore(tmp_path / "knowledge.sqlite3", embeddings=HashTokenEmbeddings())


class StubEmbeddings(Embeddings):
    def __init__(self, model_id):
        self.model_id = model_id
        self.kind = "test"
        self.model_name = model_id
        self.query_calls = 0

    def embed_documents(self, texts):
        return [[1.0, 0.0] for _ in texts]

    def embed_query(self, text):
        self.query_calls += 1
        return [1.0, 0.0]


class CountingStub(StubEmbeddings):
    def __init__(self, model_id="counting-v1", dimensions=2, fail_documents=False):
        super().__init__(model_id)
        self.dimensions = dimensions
        self.fail_documents = fail_documents
        self.document_calls = []

    def embed_documents(self, texts):
        self.document_calls.append(list(texts))
        if self.fail_documents:
            raise RuntimeError("embedding failed")
        return [[1.0] + [0.0] * (self.dimensions - 1) for _ in texts]

    def embed_query(self, text):
        self.query_calls += 1
        return [1.0] + [0.0] * (self.dimensions - 1)


def test_index_search_returns_utf8_chunks_with_citable_line_ranges(knowledge, tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    lines = [f"{number}: 普通项目说明与配置内容" for number in range(1, 90)]
    lines[72] = "73: 这里有独特知识锚点，可以从中文检索找到来源。"
    (workspace / "notes.md").write_text("\n".join(lines), encoding="utf-8")

    indexed = knowledge.index(workspace)
    results = knowledge.search(workspace, "独特知识锚点")

    assert indexed["files"] == 1
    assert indexed["chunks"] > 1
    assert indexed["embedding_kind"] == "deterministic_hash"
    assert results
    match = results[0]
    assert match["path"] == "notes.md"
    assert match["start_line"] <= 73 <= match["end_line"]
    assert match["citation"] == f"notes.md:{match['start_line']}-{match['end_line']}"
    assert match["untrusted"] is True
    assert match["embedding_kind"] == "deterministic_hash"
    assert "独特知识锚点" in match["text"]


def test_reindex_replaces_changed_and_deleted_files(knowledge, tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    (workspace / "remove.py").write_text("removed stale phrase", encoding="utf-8")
    (workspace / "change.md").write_text("old unique marker", encoding="utf-8")

    first = knowledge.index(workspace)
    assert first["files"] == 2
    assert knowledge.search(workspace, "removed stale phrase")

    (workspace / "remove.py").unlink()
    (workspace / "change.md").write_text("new distinct topic", encoding="utf-8")
    second = knowledge.index(workspace)

    assert second["files"] == 1
    assert knowledge.search(workspace, "removed stale phrase") == []
    assert knowledge.search(workspace, "old unique marker") == []
    assert knowledge.search(workspace, "new distinct topic")[0]["path"] == "change.md"


def test_index_skips_private_directories_secrets_jsonl_and_symlinks(knowledge, tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    (workspace / "public.py").write_text("public searchable token", encoding="utf-8")
    for name in (
        ".git",
        ".aws",
        ".codex",
        ".agents",
        ".ai-cli",
        ".venv",
        ".conda-env",
        ".browser-runtime",
        ".browser-artifacts",
        "artifacts",
        "node_modules",
        "sessions",
        "__pycache__",
        "skills",
    ):
        directory = workspace / name
        directory.mkdir()
        (directory / "secret.py").write_text("private searchable token", encoding="utf-8")
    (workspace / ".env").write_text("SECRET_TOKEN=hidden", encoding="utf-8")
    (workspace / "history.jsonl").write_text('{"content":"conversation"}\n', encoding="utf-8")
    (workspace / "webstate.json").write_text('{"state":"private"}', encoding="utf-8")
    outside = tmp_path / "outside.py"
    outside.write_text("outside secret", encoding="utf-8")
    (workspace / "linked.py").symlink_to(outside)

    result = knowledge.index(workspace)
    paths = {
        match["path"] for match in knowledge.search(workspace, "public searchable token", limit=20)
    }

    assert result["files"] == 1
    assert result["skipped"]["private"] >= 16
    assert result["skipped"]["symlink"] == 1
    assert paths == {"public.py"}


def test_index_rejects_binary_invalid_utf8_large_and_unsupported_files(knowledge, tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    (workspace / "binary.py").write_bytes(b"abc\x00def")
    (workspace / "invalid.py").write_bytes(b"\xff\xfe")
    (workspace / "large.py").write_bytes(b"x" * (256 * 1024 + 1))
    (workspace / "events.jsonl").write_text('{"event":"skip"}\n', encoding="utf-8")
    (workspace / "image.png").write_bytes(b"\x89PNG\r\n")

    result = knowledge.index(workspace)

    assert result["files"] == 0
    assert result["chunks"] == 0
    assert result["skipped"]["binary"] == 1
    assert result["skipped"]["invalid_utf8"] == 1
    assert result["skipped"]["large"] == 1
    assert result["skipped"]["private"] == 1
    assert result["skipped"]["unsupported"] == 1


def test_index_honors_file_total_byte_and_chunk_limits(knowledge, tmp_path, monkeypatch):
    import web.knowledge as knowledge_module

    workspace = tmp_path / "project"
    workspace.mkdir()
    (workspace / "a.py").write_text("a" * 1500, encoding="utf-8")
    (workspace / "b.py").write_text("b" * 1500, encoding="utf-8")
    (workspace / "c.py").write_text("c" * 1500, encoding="utf-8")
    (workspace / "d.py").write_text("small file", encoding="utf-8")
    (workspace / "e.py").write_text("another file", encoding="utf-8")
    monkeypatch.setattr(knowledge_module, "MAX_FILES", 4)
    monkeypatch.setattr(knowledge_module, "MAX_TOTAL_BYTES", 1600)
    monkeypatch.setattr(knowledge_module, "MAX_CHUNKS", 1)

    result = knowledge.index(workspace)

    assert result["files"] <= 2
    assert result["chunks"] <= 1
    assert result["skipped"]["file_limit"] >= 1
    assert result["skipped"]["total_limit"] >= 1
    assert result["skipped"]["chunk_limit"] >= 1


def test_memories_are_explicit_persistent_and_retrievable(knowledge, tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    (workspace / "notes.md").write_text("The user likes green tea.", encoding="utf-8")
    knowledge.index(workspace)
    assert knowledge.list_memories(workspace) == []

    memory = knowledge.add_memory(
        workspace,
        "用户明确说喜欢绿茶。",
        source="user",
        session_id="session-7",
    )
    reopened = KnowledgeStore(knowledge.db_path, embeddings=HashTokenEmbeddings())
    memories = reopened.list_memories(workspace)
    retrieved = reopened.retrieve_memories(workspace, "喜欢绿茶")

    assert memory["id"] == memories[0]["id"]
    assert memory["workspace"] == str(workspace.resolve())
    assert memory["source"] == "user"
    assert memory["session_id"] == "session-7"
    assert retrieved[0]["id"] == memory["id"]
    assert retrieved[0]["citation"] == f"memory:{memory['id']}"
    assert retrieved[0]["untrusted"] is True
    assert reopened.delete_memory(memory["id"]) is True
    assert reopened.delete_memory(memory["id"]) is False


def test_update_memory_replaces_content_and_preserves_provenance(knowledge, tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    memory = knowledge.add_memory(
        workspace,
        "用户明确保存了原始规则。",
        source="user",
        session_id="session-8",
    )

    updated = knowledge.update_memory(memory["id"], "用户明确保存了新的偏好。")

    assert updated is not None
    assert updated["content"] == "用户明确保存了新的偏好。"
    assert updated["source"] == "user"
    assert updated["session_id"] == "session-8"
    assert updated["created_at"] == memory["created_at"]
    assert knowledge.retrieve_memories(workspace, "新的偏好")[0]["id"] == memory["id"]
    assert knowledge.retrieve_memories(workspace, "原始规则") == []
    assert knowledge.update_memory("missing-id", "合法但不会保存") is None


def test_memory_validation_and_concurrent_writes(knowledge, tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    with pytest.raises(ValueError):
        knowledge.add_memory(workspace, "   ")
    with pytest.raises(ValueError):
        knowledge.add_memory(workspace, "x" * 4001)

    with ThreadPoolExecutor(max_workers=6) as executor:
        list(
            executor.map(
                lambda number: knowledge.add_memory(workspace, f"明确保存的偏好 {number}"),
                range(12),
            )
        )

    assert len(knowledge.list_memories(workspace)) == 12


def test_hash_embeddings_are_repeatable_and_validate_dimensions():
    embeddings = HashTokenEmbeddings(dimensions=96)
    assert embeddings.embed_query("hello 世界") == embeddings.embed_query("hello 世界")
    assert len(embeddings.embed_query("hello 世界")) == 96
    with pytest.raises(ValueError):
        HashTokenEmbeddings(dimensions=0)


def test_embedding_signature_requires_reindex_after_provider_change(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    (workspace / "notes.md").write_text("semantic retrieval example", encoding="utf-8")
    db_path = tmp_path / "knowledge.sqlite3"
    first = KnowledgeStore(db_path, embeddings=StubEmbeddings("provider-a:model-1"))

    indexed = first.index(workspace)
    assert indexed["embedding_kind"] == "test"
    assert indexed["embedding_model"] == "provider-a:model-1"
    assert first.search(workspace, "semantic retrieval")

    changed = StubEmbeddings("provider-b:model-2")
    reopened = KnowledgeStore(db_path, embeddings=changed)
    with pytest.raises(ValueError, match="重新索引 workspace"):
        reopened.search(workspace, "semantic retrieval")
    assert changed.query_calls == 0

    refreshed = reopened.index(workspace)
    assert refreshed["embedding_signature"] == "provider-b:model-2"
    assert reopened.search(workspace, "semantic retrieval")


def test_environment_config_selects_openai_embeddings_without_network_calls(tmp_path, monkeypatch):
    calls = []

    class FakeOpenAIEmbeddings(Embeddings):
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def embed_documents(self, texts):
            calls.append(("documents", texts))
            raise AssertionError("test must not call an embedding endpoint")

        def embed_query(self, text):
            calls.append(("query", text))
            raise AssertionError("test must not call an embedding endpoint")

    module = ModuleType("langchain_openai")
    module.OpenAIEmbeddings = FakeOpenAIEmbeddings
    monkeypatch.setitem(sys.modules, "langchain_openai", module)
    monkeypatch.setenv("AI_CLI_EMBEDDING_MODEL", "example-embedding-model")
    monkeypatch.setenv("AI_CLI_BASE_URL", "https://embedding.example/v1")
    monkeypatch.setenv("AI_CLI_API_KEY_ENV", "TEST_EMBEDDING_API_KEY")
    monkeypatch.setenv("TEST_EMBEDDING_API_KEY", "dummy-test-key")

    store = KnowledgeStore(tmp_path / "knowledge.sqlite3")

    assert store.embedding_kind == "semantic"
    assert store.embedding_model == "example-embedding-model"
    assert "dummy-test-key" not in store._embedding_id
    assert store.embeddings._delegate.kwargs == {
        "model": "example-embedding-model",
        "base_url": "https://embedding.example/v1",
        "api_key": "dummy-test-key",
    }
    assert calls == []


def test_default_embedding_is_labeled_hash_when_model_is_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("AI_CLI_EMBEDDING_MODEL", raising=False)

    store = KnowledgeStore(tmp_path / "knowledge.sqlite3")

    assert store.embedding_kind == "deterministic_hash"
    assert store.embedding_model.startswith("hash-token-v1:")


def test_configured_semantic_embedding_requires_key_without_calling_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_CLI_EMBEDDING_MODEL", "example-embedding-model")
    monkeypatch.setenv("AI_CLI_API_KEY_ENV", "MISSING_EMBEDDING_KEY")
    monkeypatch.delenv("MISSING_EMBEDDING_KEY", raising=False)

    with pytest.raises(ValueError, match="未设置"):
        KnowledgeStore(tmp_path / "knowledge.sqlite3")


def test_invalid_workspace_query_and_limit_are_rejected(knowledge, tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    with pytest.raises(ValueError):
        knowledge.index(tmp_path / "missing")
    with pytest.raises(ValueError):
        knowledge.search(workspace, " ")
    with pytest.raises(ValueError):
        knowledge.search(workspace, "query", limit=0)


def test_index_reuses_unchanged_chunks_without_embedding(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    (workspace / "a.md").write_text("alpha unchanged content", encoding="utf-8")
    (workspace / "b.md").write_text("beta unchanged content", encoding="utf-8")
    embeddings = CountingStub()
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3", embeddings=embeddings)

    first = store.index(workspace)
    embeddings.document_calls.clear()
    second = store.index(workspace)

    assert first["embedded_chunks"] == 2
    assert second["reused_chunks"] == 2
    assert second["embedded_chunks"] == 0
    assert second["reused_files"] == 2
    assert second["updated_files"] == 0
    assert embeddings.document_calls == []


def test_index_embeds_only_chunks_from_changed_file(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    (workspace / "changed.md").write_text("old changed content", encoding="utf-8")
    (workspace / "stable.md").write_text("stable file content", encoding="utf-8")
    embeddings = CountingStub()
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3", embeddings=embeddings)
    store.index(workspace)
    embeddings.document_calls.clear()

    (workspace / "changed.md").write_text("new changed content", encoding="utf-8")
    result = store.index(workspace)

    assert embeddings.document_calls == [["new changed content"]]
    assert result["reused_chunks"] == 1
    assert result["embedded_chunks"] == 1
    assert result["reused_files"] == 1
    assert result["updated_files"] == 1


def test_index_deletes_removed_files_without_embedding_them(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    (workspace / "keep.md").write_text("kept content", encoding="utf-8")
    (workspace / "remove.md").write_text("removed content", encoding="utf-8")
    embeddings = CountingStub()
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3", embeddings=embeddings)
    store.index(workspace)
    embeddings.document_calls.clear()

    (workspace / "remove.md").unlink()
    result = store.index(workspace)

    assert embeddings.document_calls == []
    assert result["removed_files"] == 1
    assert result["reused_files"] == 1
    assert result["updated_files"] == 0
    assert all(match["path"] != "remove.md" for match in store.search(workspace, "removed content"))


def test_index_does_not_reuse_chunks_between_workspaces(tmp_path):
    first_workspace = tmp_path / "first"
    second_workspace = tmp_path / "second"
    first_workspace.mkdir()
    second_workspace.mkdir()
    (first_workspace / "same.md").write_text("same workspace-relative content", encoding="utf-8")
    (second_workspace / "same.md").write_text("same workspace-relative content", encoding="utf-8")
    embeddings = CountingStub()
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3", embeddings=embeddings)
    store.index(first_workspace)
    embeddings.document_calls.clear()

    result = store.index(second_workspace)

    assert embeddings.document_calls == [["same workspace-relative content"]]
    assert result["reused_chunks"] == 0
    assert result["embedded_chunks"] == 1
    assert result["reused_files"] == 0
    assert result["updated_files"] == 1


def test_index_reembeds_every_chunk_after_provider_change(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    (workspace / "a.md").write_text("alpha provider content", encoding="utf-8")
    (workspace / "b.md").write_text("beta provider content", encoding="utf-8")
    db_path = tmp_path / "knowledge.sqlite3"
    KnowledgeStore(db_path, embeddings=CountingStub("provider-a")).index(workspace)
    embeddings = CountingStub("provider-b")
    store = KnowledgeStore(db_path, embeddings=embeddings)

    result = store.index(workspace)

    assert embeddings.document_calls == [["alpha provider content", "beta provider content"]]
    assert result["reused_chunks"] == 0
    assert result["embedded_chunks"] == 2
    assert result["reused_files"] == 0
    assert result["updated_files"] == 2


def test_embedding_failure_preserves_previous_workspace_index(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    document = workspace / "notes.md"
    document.write_text("original indexed content", encoding="utf-8")
    embeddings = CountingStub()
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3", embeddings=embeddings)
    store.index(workspace)
    document.write_text("replacement indexed content", encoding="utf-8")
    embeddings.fail_documents = True

    with pytest.raises(RuntimeError, match="embedding failed"):
        store.index(workspace)

    results = store.search(workspace, "replacement indexed content")
    assert results
    assert all(result["text"] == "original indexed content" for result in results)


def test_corrupt_old_vector_forces_full_embedding_rebuild(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    (workspace / "notes.md").write_text("current indexed content", encoding="utf-8")
    embeddings = CountingStub()
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3", embeddings=embeddings)
    store.index(workspace)
    embeddings.document_calls.clear()
    with sqlite3.connect(store.db_path) as connection:
        connection.execute(
            "UPDATE chunks SET embedding_json = '[NaN,0.0]' WHERE workspace = ?",
            (str(workspace.resolve()),),
        )

    result = store.index(workspace)

    assert embeddings.document_calls == [["current indexed content"]]
    assert result["reused_chunks"] == 0
    assert result["embedded_chunks"] == 1
    assert store.search(workspace, "current indexed content")


def test_dimension_change_reembeds_all_chunks_before_commit(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    (workspace / "a.md").write_text("stable dimensions content", encoding="utf-8")
    (workspace / "b.md").write_text("old dimensions content", encoding="utf-8")
    embeddings = CountingStub(dimensions=2)
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3", embeddings=embeddings)
    store.index(workspace)
    embeddings.document_calls.clear()
    embeddings.dimensions = 3
    (workspace / "b.md").write_text("new dimensions content", encoding="utf-8")

    result = store.index(workspace)

    assert embeddings.document_calls == [
        ["new dimensions content"],
        ["stable dimensions content", "new dimensions content"],
    ]
    assert result["reused_chunks"] == 0
    assert result["embedded_chunks"] == 2
    assert store.search(workspace, "stable dimensions content")


def test_empty_file_does_not_call_embedding(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    (workspace / "empty.md").write_text("", encoding="utf-8")
    embeddings = CountingStub()
    result = KnowledgeStore(tmp_path / "knowledge.sqlite3", embeddings=embeddings).index(workspace)

    assert result["chunks"] == 0
    assert result["embedded_chunks"] == 0
    assert embeddings.document_calls == []
