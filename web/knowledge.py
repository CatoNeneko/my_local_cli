"""基于 SQLite 的本地 RAG 索引与显式长期记忆。"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import stat
import threading
import uuid
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


MAX_FILE_BYTES = 256 * 1024
MAX_FILES = 500
MAX_TOTAL_BYTES = 8 * 1024 * 1024
MAX_CHUNKS = 5000
MAX_MEMORY_CHARS = 4000
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

_IGNORED_DIRECTORIES = frozenset(
    {
        ".git",
        ".aws",
        ".codex",
        ".agents",
        ".env",
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
    }
)
_IGNORED_STATE_NAMES = frozenset(
    {"webstate", "web_state", "web-state", ".webstate", "history.json"}
)
_ALLOWED_SUFFIXES = frozenset(
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

_TOKEN_RE = re.compile(r"[a-z0-9_]+|[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+", re.IGNORECASE)


class HashTokenEmbeddings(Embeddings):
    """确定性特征哈希向量；它只提供词项匹配，不是语义模型。"""

    def __init__(self, dimensions: int = 384):
        if type(dimensions) is not int or dimensions <= 0:
            raise ValueError("dimensions 必须是正整数")
        self.dimensions = dimensions
        self.model_id = f"hash-token-v1:{dimensions}"
        self.model_name = self.model_id
        self.kind = "deterministic_hash"

    @staticmethod
    def _features(text: str) -> Counter[str]:
        features: Counter[str] = Counter()
        words: list[str] = []
        for raw_token in _TOKEN_RE.findall(text.casefold()):
            if _is_han(raw_token):
                # 中文等汉字文本没有依赖外部分词器，使用连续字符 1 到 3 元组。
                for size in (1, 2, 3):
                    for position in range(max(0, len(raw_token) - size + 1)):
                        features[f"han:{raw_token[position : position + size]}"] += 1
            else:
                words.append(raw_token)
                features[f"word:{raw_token}"] += 1
        for left, right in zip(words, words[1:]):
            features[f"word2:{left}_{right}"] += 1
        return features

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for feature, count in self._features(text).items():
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=16).digest()
            index = int.from_bytes(digest[:8], "big") % self.dimensions
            sign = 1.0 if digest[8] & 1 else -1.0
            vector[index] += sign * (1.0 + math.log(count))
        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]
        return vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class _ConfiguredOpenAIEmbeddings(Embeddings):
    """为 OpenAI 兼容 provider 记录不含凭据的稳定配置签名。"""

    def __init__(self, delegate: Embeddings, model: str, base_url: str):
        self._delegate = delegate
        signature_input = json.dumps(
            {"provider": "openai-compatible-v1", "model": model, "base_url": base_url.rstrip("/")},
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(signature_input.encode("utf-8")).hexdigest()
        self.model_id = f"openai-compatible-v1:{digest}"
        self.model_name = model
        self.kind = "semantic"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._delegate.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._delegate.embed_query(text)


def _configured_embeddings() -> Embeddings:
    model = os.environ.get("AI_CLI_EMBEDDING_MODEL", "").strip()
    if not model:
        return HashTokenEmbeddings()

    base_url = os.environ.get("AI_CLI_BASE_URL", "https://api.openai.com/v1").strip()
    key_env = os.environ.get("AI_CLI_API_KEY_ENV", "OPENAI_API_KEY").strip()
    if not base_url:
        raise ValueError("AI_CLI_BASE_URL 不能为空")
    if not key_env:
        raise ValueError("AI_CLI_API_KEY_ENV 不能为空")
    api_key = os.environ.get(key_env)
    if not api_key or not api_key.strip():
        raise ValueError(f"已配置 AI_CLI_EMBEDDING_MODEL，但环境变量 {key_env} 未设置")

    try:
        from langchain_openai import OpenAIEmbeddings
    except ImportError as error:
        raise RuntimeError("配置语义 embedding 需要安装 langchain-openai") from error

    delegate = OpenAIEmbeddings(model=model, base_url=base_url, api_key=api_key)
    return _ConfiguredOpenAIEmbeddings(delegate, model, base_url)


def _is_han(value: str) -> bool:
    return bool(value) and ord(value[0]) >= 0x3400


def _embedding_id(embeddings: Embeddings) -> str:
    explicit = getattr(embeddings, "model_id", None)
    if isinstance(explicit, str) and explicit:
        return explicit
    kind = type(embeddings)
    settings = {
        name: getattr(embeddings, name)
        for name in (
            "model",
            "model_name",
            "deployment",
            "dimensions",
            "base_url",
            "openai_api_base",
        )
        if isinstance(getattr(embeddings, name, None), (str, int, float))
    }
    if settings:
        signature = json.dumps(
            {"type": f"{kind.__module__}.{kind.__qualname__}", "settings": settings},
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(signature.encode("utf-8")).hexdigest()
        return f"custom-embedding-v1:{digest}"
    return f"{kind.__module__}.{kind.__qualname__}"


def _normalize_vector(vector: Iterable[float]) -> list[float]:
    result = [float(value) for value in vector]
    if not result or any(not math.isfinite(value) for value in result):
        raise ValueError("embedding 必须是非空且有限的数值向量")
    norm = math.sqrt(sum(value * value for value in result))
    return [value / norm for value in result] if norm else result


def _lexical_terms(text: str) -> set[str]:
    terms: set[str] = set()
    words: list[str] = []
    for token in _TOKEN_RE.findall(text.casefold()):
        if _is_han(token):
            for size in (1, 2, 3):
                terms.update(
                    f"han:{token[position : position + size]}"
                    for position in range(max(0, len(token) - size + 1))
                )
        else:
            words.append(token)
            terms.add(f"word:{token}")
    terms.update(f"word2:{left}_{right}" for left, right in zip(words, words[1:]))
    return terms


def _hybrid_score(
    query: str, text: str, query_vector: list[float], document_vector: list[float]
) -> float:
    query_terms = _lexical_terms(query)
    document_terms = _lexical_terms(text)
    lexical = len(query_terms & document_terms) / len(query_terms) if query_terms else 0.0
    if query.casefold() in text.casefold():
        lexical = 1.0

    if len(query_vector) == len(document_vector):
        cosine = sum(left * right for left, right in zip(query_vector, document_vector))
        vector_score = max(0.0, min(1.0, cosine))
    else:
        vector_score = 0.0
    # Hash 碰撞会给无关文本带来少量正余弦值；没有词项命中时，仅接受较强的向量重合。
    if lexical == 0.0 and vector_score < 0.2:
        return 0.0
    return 0.6 * lexical + 0.4 * vector_score


def _line_range(text: str, start: int, end: int) -> tuple[int, int]:
    start_line = text.count("\n", 0, start) + 1
    end_line = text.count("\n", 0, end)
    if end <= 0 or text[end - 1] != "\n":
        end_line += 1
    return start_line, max(start_line, end_line)


class KnowledgeStore:
    """保存 workspace 文档块和用户显式创建的长期记忆。"""

    def __init__(self, db_path: str | os.PathLike[str], embeddings: Embeddings | None = None):
        if str(db_path) == ":memory:":
            raise ValueError("KnowledgeStore 需要持久化 SQLite 文件，不能使用 :memory:")
        self.db_path = str(Path(db_path).expanduser().absolute())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.embeddings = embeddings if embeddings is not None else _configured_embeddings()
        self._embedding_id = _embedding_id(self.embeddings)
        kind = getattr(self.embeddings, "kind", "custom")
        model = getattr(self.embeddings, "model_name", self._embedding_id)
        self.embedding_kind = kind if isinstance(kind, str) else "custom"
        self.embedding_model = model if isinstance(model, str) else self._embedding_id
        self._db_lock = threading.RLock()
        self._embedding_lock = threading.RLock()
        self._index_lock = threading.RLock()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """每次操作使用独立连接；锁保护同一实例，SQLite 超时处理跨实例竞争。"""
        with self._db_lock:
            connection = sqlite3.connect(self.db_path, timeout=10.0)
            connection.row_factory = sqlite3.Row
            try:
                connection.execute("PRAGMA busy_timeout = 10000")
                connection.execute("PRAGMA journal_mode = WAL")
                connection.execute("PRAGMA foreign_keys = ON")
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS workspace_files (
                        workspace TEXT NOT NULL,
                        path TEXT NOT NULL,
                        sha256 TEXT NOT NULL,
                        mtime REAL NOT NULL,
                        size INTEGER NOT NULL,
                        PRIMARY KEY (workspace, path)
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chunks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        workspace TEXT NOT NULL,
                        path TEXT NOT NULL,
                        start_line INTEGER NOT NULL,
                        end_line INTEGER NOT NULL,
                        text TEXT NOT NULL,
                        embedding_json TEXT NOT NULL,
                        embedding_id TEXT NOT NULL,
                        FOREIGN KEY (workspace, path)
                            REFERENCES workspace_files (workspace, path) ON DELETE CASCADE
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS index_metadata (
                        workspace TEXT PRIMARY KEY,
                        embedding_signature TEXT NOT NULL,
                        embedding_kind TEXT NOT NULL,
                        embedding_model TEXT NOT NULL,
                        indexed_at TEXT NOT NULL,
                        files_count INTEGER NOT NULL,
                        chunks_count INTEGER NOT NULL
                    )
                    """
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS chunks_workspace ON chunks(workspace)"
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memories (
                        id TEXT PRIMARY KEY,
                        workspace TEXT NOT NULL,
                        content TEXT NOT NULL,
                        source TEXT NOT NULL,
                        session_id TEXT,
                        created_at TEXT NOT NULL,
                        embedding_json TEXT NOT NULL,
                        embedding_id TEXT NOT NULL
                    )
                    """
                )
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()

    @staticmethod
    def _workspace_path(workspace: str | os.PathLike[str]) -> Path:
        workspace_value = os.fspath(workspace)
        if not workspace_value.strip():
            raise ValueError("workspace 不能为空")
        candidate = Path(os.path.abspath(Path(workspace_value).expanduser()))
        cursor = Path(candidate.anchor)
        for component in candidate.parts[1:]:
            cursor /= component
            if cursor.is_symlink():
                raise ValueError("workspace 路径不能经过符号链接")
        try:
            root = candidate.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise ValueError("workspace 必须是存在的目录") from error
        if not root.is_dir():
            raise ValueError("workspace 必须是目录")
        return root

    def _embed_documents(self, documents: list[Document]) -> list[list[float]]:
        with self._embedding_lock:
            vectors = self.embeddings.embed_documents(
                [document.page_content for document in documents]
            )
        if len(vectors) != len(documents):
            raise ValueError("embedding 返回数量与文档块数量不一致")
        normalized = [_normalize_vector(vector) for vector in vectors]
        if normalized and len({len(vector) for vector in normalized}) != 1:
            raise ValueError("embedding 向量维度不一致")
        return normalized

    def _embed_query(self, query: str) -> list[float]:
        with self._embedding_lock:
            vector = self.embeddings.embed_query(query)
        return _normalize_vector(vector)

    @staticmethod
    def _validate_memory_content(content: str) -> None:
        if not isinstance(content, str) or not content.strip():
            raise ValueError("记忆内容不能为空")
        if len(content) > MAX_MEMORY_CHARS:
            raise ValueError(f"记忆内容不能超过 {MAX_MEMORY_CHARS} 个字符")

    @staticmethod
    def _ignored_path(relative: Path) -> bool:
        parts = relative.parts
        if any(part in _IGNORED_DIRECTORIES for part in parts[:-1]):
            return True
        name = relative.name.casefold()
        if name in _IGNORED_DIRECTORIES or name.startswith(".env"):
            return True
        if (
            name in _IGNORED_STATE_NAMES
            or relative.stem.casefold() in _IGNORED_STATE_NAMES
            or relative.suffix.casefold() == ".jsonl"
        ):
            return True
        return False

    def index(self, workspace: str | os.PathLike[str]) -> dict[str, object]:
        with self._index_lock:
            return self._index_workspace(workspace)

    def _index_workspace(self, workspace: str | os.PathLike[str]) -> dict[str, object]:
        root = self._workspace_path(workspace)
        if root.name in _IGNORED_DIRECTORIES or root.name.startswith(".env"):
            raise ValueError("不能将私有目录作为 workspace 索引")
        workspace_key = str(root)
        database_file = Path(self.db_path).resolve()
        skipped: Counter[str] = Counter()
        files: list[tuple[str, str, float, int]] = []
        documents: list[Document] = []
        total_bytes = 0
        visited_files = 0
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            add_start_index=True,
        )

        def walk_error(_error: OSError) -> None:
            skipped["unreadable"] += 1

        for directory, directory_names, file_names in os.walk(
            root, followlinks=False, onerror=walk_error
        ):
            directory_path = Path(directory)
            allowed_directories = []
            for name in sorted(directory_names):
                path = directory_path / name
                relative = path.relative_to(root)
                if name in _IGNORED_DIRECTORIES or self._ignored_path(relative):
                    skipped["private"] += 1
                elif path.is_symlink():
                    skipped["symlink"] += 1
                else:
                    allowed_directories.append(name)
            directory_names[:] = allowed_directories

            for name in sorted(file_names):
                path = directory_path / name
                relative = path.relative_to(root)
                if self._ignored_path(relative):
                    skipped["private"] += 1
                    continue
                if path.is_symlink():
                    skipped["symlink"] += 1
                    continue
                if path.suffix.casefold() not in _ALLOWED_SUFFIXES:
                    skipped["unsupported"] += 1
                    continue
                if visited_files >= MAX_FILES:
                    skipped["file_limit"] += 1
                    continue
                visited_files += 1

                try:
                    resolved = path.resolve(strict=True)
                    resolved.relative_to(root)
                    if resolved == database_file:
                        skipped["private"] += 1
                        continue
                    before = path.stat()
                    if not stat.S_ISREG(before.st_mode):
                        skipped["non_file"] += 1
                        continue
                    if before.st_size > MAX_FILE_BYTES:
                        skipped["large"] += 1
                        continue
                    remaining = MAX_TOTAL_BYTES - total_bytes
                    if before.st_size > remaining:
                        skipped["total_limit"] += 1
                        continue
                    with path.open("rb") as file_handle:
                        raw = file_handle.read(MAX_FILE_BYTES + 1)
                    if len(raw) > MAX_FILE_BYTES:
                        skipped["large"] += 1
                        continue
                    if len(raw) > remaining:
                        skipped["total_limit"] += 1
                        continue
                    total_bytes += len(raw)
                    if b"\x00" in raw:
                        skipped["binary"] += 1
                        continue
                    try:
                        text = raw.decode("utf-8-sig")
                    except UnicodeDecodeError:
                        skipped["invalid_utf8"] += 1
                        continue
                    after = path.stat()
                except (OSError, RuntimeError, ValueError):
                    skipped["unreadable"] += 1
                    continue

                relative_name = relative.as_posix()
                files.append(
                    (
                        relative_name,
                        hashlib.sha256(raw).hexdigest(),
                        after.st_mtime,
                        len(raw),
                    )
                )
                source_document = Document(page_content=text, metadata={"path": relative_name})
                split_documents = splitter.split_documents([source_document])
                available = max(0, MAX_CHUNKS - len(documents))
                if len(split_documents) > available:
                    skipped["chunk_limit"] += len(split_documents) - available
                    split_documents = split_documents[:available]
                for document in split_documents:
                    start = document.metadata.get("start_index")
                    if not isinstance(start, int) or start < 0:
                        start = text.find(document.page_content)
                    if start < 0:
                        start = 0
                    start_line, end_line = _line_range(
                        text, start, start + len(document.page_content)
                    )
                    document.metadata.update(
                        {
                            "path": relative_name,
                            "start_line": start_line,
                            "end_line": end_line,
                            "untrusted": True,
                        }
                    )
                    documents.append(document)

        current_file_hashes = {path: sha256 for path, sha256, _, _ in files}
        with self._connection() as connection:
            connection.execute("BEGIN")
            previous_file_rows = connection.execute(
                "SELECT path,sha256 FROM workspace_files WHERE workspace = ?",
                (workspace_key,),
            ).fetchall()
            previous_chunk_rows = connection.execute(
                """
                SELECT path,start_line,end_line,text,embedding_json,embedding_id
                FROM chunks WHERE workspace = ?
                """,
                (workspace_key,),
            ).fetchall()

        previous_file_hashes = {row["path"]: row["sha256"] for row in previous_file_rows}
        previous_vectors: defaultdict[tuple[str, int, int, str], list[list[float]]] = defaultdict(
            list
        )
        previous_dimensions: set[int] = set()
        invalid_previous_vector = False
        for row in previous_chunk_rows:
            try:
                raw_vector = json.loads(row["embedding_json"])
                if not isinstance(raw_vector, list) or any(
                    isinstance(value, bool) or not isinstance(value, (int, float))
                    for value in raw_vector
                ):
                    raise ValueError("索引 embedding 格式错误")
                vector = _normalize_vector(raw_vector)
            except (TypeError, ValueError, OverflowError):
                invalid_previous_vector = True
                continue

            previous_dimensions.add(len(vector))
            path = str(row["path"])
            if (
                path in current_file_hashes
                and previous_file_hashes.get(path) == current_file_hashes[path]
                and row["embedding_id"] == self._embedding_id
            ):
                key = (
                    path,
                    int(row["start_line"]),
                    int(row["end_line"]),
                    str(row["text"]),
                )
                previous_vectors[key].append(vector)

        can_reuse_vectors = not invalid_previous_vector and len(previous_dimensions) <= 1
        vectors_by_document: list[list[float] | None] = [None] * len(documents)
        document_indexes: list[int] = []
        current_chunk_counts: Counter[str] = Counter()
        reused_chunk_counts: Counter[str] = Counter()
        for index, document in enumerate(documents):
            path = str(document.metadata["path"])
            current_chunk_counts[path] += 1
            key = (
                path,
                int(document.metadata["start_line"]),
                int(document.metadata["end_line"]),
                document.page_content,
            )
            if can_reuse_vectors and previous_vectors[key]:
                vectors_by_document[index] = previous_vectors[key].pop()
                reused_chunk_counts[path] += 1
            else:
                document_indexes.append(index)

        documents_to_embed = [documents[index] for index in document_indexes]
        embedded_vectors = self._embed_documents(documents_to_embed) if documents_to_embed else []
        reused_chunks = sum(reused_chunk_counts.values())
        if (
            reused_chunks
            and previous_dimensions
            and any(len(vector) != next(iter(previous_dimensions)) for vector in embedded_vectors)
        ):
            vectors = self._embed_documents(documents) if documents else []
            reused_chunks = 0
            reused_chunk_counts.clear()
        else:
            for index, vector in zip(document_indexes, embedded_vectors):
                vectors_by_document[index] = vector
            vectors = [vector for vector in vectors_by_document if vector is not None]
            if len(vectors) != len(documents):
                raise RuntimeError("索引块缺少 embedding 向量")

        current_paths = {path for path, _, _, _ in files}
        reused_files = sum(
            previous_file_hashes.get(path) == sha256
            and current_chunk_counts[path] == reused_chunk_counts[path]
            for path, sha256, _, _ in files
        )
        updated_files = len(files) - reused_files
        removed_files = len(set(previous_file_hashes) - current_paths)
        chunk_rows = [
            (
                workspace_key,
                str(document.metadata["path"]),
                int(document.metadata["start_line"]),
                int(document.metadata["end_line"]),
                document.page_content,
                json.dumps(vector, separators=(",", ":")),
                self._embedding_id,
            )
            for document, vector in zip(documents, vectors)
        ]

        # 先在内存中完成受限扫描和向量化，再用单个写事务替换 workspace，旧文件不会留下陈旧块。
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM chunks WHERE workspace = ?", (workspace_key,))
            connection.execute("DELETE FROM workspace_files WHERE workspace = ?", (workspace_key,))
            connection.executemany(
                "INSERT INTO workspace_files(workspace,path,sha256,mtime,size) VALUES(?,?,?,?,?)",
                ((workspace_key, path, sha, mtime, size) for path, sha, mtime, size in files),
            )
            connection.executemany(
                """
                INSERT INTO chunks(
                    workspace,path,start_line,end_line,text,embedding_json,embedding_id
                ) VALUES(?,?,?,?,?,?,?)
                """,
                chunk_rows,
            )
            connection.execute(
                """
                INSERT INTO index_metadata(
                    workspace,embedding_signature,embedding_kind,embedding_model,
                    indexed_at,files_count,chunks_count
                ) VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(workspace) DO UPDATE SET
                    embedding_signature=excluded.embedding_signature,
                    embedding_kind=excluded.embedding_kind,
                    embedding_model=excluded.embedding_model,
                    indexed_at=excluded.indexed_at,
                    files_count=excluded.files_count,
                    chunks_count=excluded.chunks_count
                """,
                (
                    workspace_key,
                    self._embedding_id,
                    self.embedding_kind,
                    str(self.embedding_model),
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    len(files),
                    len(chunk_rows),
                ),
            )

        return {
            "files": len(files),
            "chunks": len(chunk_rows),
            "reused_chunks": reused_chunks,
            "embedded_chunks": len(documents) - reused_chunks,
            "reused_files": reused_files,
            "updated_files": updated_files,
            "removed_files": removed_files,
            "skipped": dict(skipped),
            "embedding_kind": self.embedding_kind,
            "embedding_model": self.embedding_model,
            "embedding_signature": self._embedding_id,
        }

    def search(
        self,
        workspace: str | os.PathLike[str],
        query: str,
        limit: int = 5,
    ) -> list[dict[str, object]]:
        root = self._workspace_path(workspace)
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query 不能为空")
        _validate_limit(limit)
        with self._connection() as connection:
            metadata = connection.execute(
                "SELECT embedding_signature FROM index_metadata WHERE workspace = ?",
                (str(root),),
            ).fetchone()
            rows = connection.execute(
                """
                SELECT path,start_line,end_line,text,embedding_json,embedding_id
                FROM chunks WHERE workspace = ?
                """,
                (str(root),),
            ).fetchall()

        if metadata is not None and metadata["embedding_signature"] != self._embedding_id:
            raise ValueError("embedding 配置与索引签名不一致，请重新索引 workspace")
        if rows and metadata is None:
            raise ValueError("索引缺少 embedding 签名，请重新索引 workspace")
        if any(row["embedding_id"] != self._embedding_id for row in rows):
            raise ValueError("索引块 embedding 与 workspace 签名不一致，请重新索引 workspace")
        if not rows:
            return []

        query_vector = self._embed_query(query)

        results: list[dict[str, object]] = []
        for row in rows:
            try:
                vector = [float(value) for value in json.loads(row["embedding_json"])]
            except (TypeError, ValueError, json.JSONDecodeError):
                raise ValueError("索引 embedding 数据损坏，请重新索引 workspace")
            if len(vector) != len(query_vector):
                raise ValueError("索引 embedding 维度与查询不一致，请重新索引 workspace")
            score = _hybrid_score(query, row["text"], query_vector, vector)
            if score <= 0.0:
                continue
            results.append(
                {
                    "path": row["path"],
                    "start_line": row["start_line"],
                    "end_line": row["end_line"],
                    "text": row["text"],
                    "score": score,
                    "citation": f"{row['path']}:{row['start_line']}-{row['end_line']}",
                    "untrusted": True,
                    "embedding_kind": self.embedding_kind,
                    "embedding_model": self.embedding_model,
                }
            )
        results.sort(
            key=lambda item: (-float(item["score"]), str(item["path"]), int(item["start_line"]))
        )
        return results[:limit]

    def add_memory(
        self,
        workspace: str | os.PathLike[str],
        content: str,
        source: str = "user",
        session_id: str | None = None,
    ) -> dict[str, object]:
        root = self._workspace_path(workspace)
        self._validate_memory_content(content)
        if not isinstance(source, str) or not source.strip():
            raise ValueError("source 不能为空")
        if session_id is not None and not isinstance(session_id, str):
            raise ValueError("session_id 必须是字符串或 None")

        memory_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        vector = self._embed_query(content)
        result = {
            "id": memory_id,
            "workspace": str(root),
            "content": content,
            "source": source,
            "session_id": session_id,
            "created_at": created_at,
        }
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO memories(
                    id,workspace,content,source,session_id,created_at,embedding_json,embedding_id
                ) VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    memory_id,
                    str(root),
                    content,
                    source,
                    session_id,
                    created_at,
                    json.dumps(vector, separators=(",", ":")),
                    self._embedding_id,
                ),
            )
        return result

    def update_memory(self, memory_id: str, content: str) -> dict[str, object] | None:
        self._validate_memory_content(content)
        if not isinstance(memory_id, str) or not memory_id:
            return None
        with self._connection() as connection:
            existing = connection.execute(
                "SELECT id FROM memories WHERE id = ?", (memory_id,)
            ).fetchone()
        if existing is None:
            return None

        vector = self._embed_query(content)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """
                UPDATE memories
                SET content = ?, embedding_json = ?, embedding_id = ?
                WHERE id = ?
                """,
                (
                    content,
                    json.dumps(vector, separators=(",", ":")),
                    self._embedding_id,
                    memory_id,
                ),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                """
                SELECT id,workspace,content,source,session_id,created_at
                FROM memories WHERE id = ?
                """,
                (memory_id,),
            ).fetchone()
        return dict(row)

    def list_memories(self, workspace: str | os.PathLike[str]) -> list[dict[str, object]]:
        root = self._workspace_path(workspace)
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id,workspace,content,source,session_id,created_at
                FROM memories WHERE workspace = ? ORDER BY created_at DESC, id
                """,
                (str(root),),
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_memory(self, memory_id: str) -> bool:
        if not isinstance(memory_id, str) or not memory_id:
            return False
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return cursor.rowcount > 0

    def retrieve_memories(
        self,
        workspace: str | os.PathLike[str],
        query: str,
        limit: int = 3,
    ) -> list[dict[str, object]]:
        root = self._workspace_path(workspace)
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query 不能为空")
        _validate_limit(limit)
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id,workspace,content,source,session_id,created_at,embedding_json,embedding_id
                FROM memories WHERE workspace = ?
                """,
                (str(root),),
            ).fetchall()

        if not rows:
            return []
        query_vector = self._embed_query(query)

        results: list[dict[str, object]] = []
        for row in rows:
            try:
                vector = [float(value) for value in json.loads(row["embedding_json"])]
            except (TypeError, ValueError, json.JSONDecodeError):
                vector = []
            if row["embedding_id"] != self._embedding_id or len(vector) != len(query_vector):
                vector = self._embed_query(row["content"])
            score = _hybrid_score(query, row["content"], query_vector, vector)
            if score <= 0.0:
                continue
            results.append(
                {
                    "id": row["id"],
                    "workspace": row["workspace"],
                    "content": row["content"],
                    "source": row["source"],
                    "session_id": row["session_id"],
                    "created_at": row["created_at"],
                    "score": score,
                    "citation": f"memory:{row['id']}",
                    "untrusted": True,
                    "embedding_kind": self.embedding_kind,
                    "embedding_model": self.embedding_model,
                }
            )
        results.sort(
            key=lambda item: (-float(item["score"]), str(item["created_at"]), str(item["id"]))
        )
        return results[:limit]


def _validate_limit(limit: int) -> None:
    if type(limit) is not int or limit <= 0:
        raise ValueError("limit 必须是正整数")
