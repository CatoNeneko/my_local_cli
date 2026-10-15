"""本机 Web API；同源写入、允许目录、进程隔离。不是公网多租户服务。"""

import asyncio
from contextlib import asynccontextmanager
import json
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from config import permission_config
from web.guardrails import check_input, redact
from web.knowledge import KnowledgeStore
from web.runner import ACTIVE, Runner
from web.settings import Settings
from web.store import Store


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NewSession(Payload):
    title: str = Field(min_length=1, max_length=120)
    workspace: str = Field(min_length=1, max_length=4096)


class Rename(Payload):
    title: str = Field(min_length=1, max_length=120)


class Message(Payload):
    message: str = Field(min_length=1, max_length=12000)


class Memory(Payload):
    content: str = Field(min_length=1, max_length=4000)


class Search(Payload):
    query: str = Field(min_length=1, max_length=2000)


class Approval(Payload):
    allow: StrictBool


class RestorePreview(Payload):
    snapshot_id: str = Field(min_length=1, max_length=100)
    path: str = Field(min_length=1, max_length=4096)


class Restore(RestorePreview):
    expected_hash: str | None = Field(default=None, max_length=64)
    allow: StrictBool


class TaskInput(Payload):
    text: str = Field(max_length=4096)
    allow: StrictBool


def create_app(settings=None):
    settings = (settings or Settings.from_env()).validate()
    settings.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    settings.state_dir.chmod(0o700)
    store = Store(settings.state_dir / "workbench.sqlite")
    knowledge = KnowledgeStore(settings.state_dir / "knowledge.sqlite")
    runner = Runner(settings, store)
    from web.task_service import TaskService

    task_service = TaskService(settings, store)
    runner.task_service = task_service

    @asynccontextmanager
    async def lifespan(app):
        await asyncio.to_thread(task_service.start)
        try:
            runner.recover()
            yield
        finally:
            await asyncio.to_thread(runner.close)
            await asyncio.to_thread(task_service.close)

    app = FastAPI(title="AI 开发工作台", lifespan=lifespan)
    app.state.store, app.state.runner, app.state.knowledge = store, runner, knowledge
    app.state.task_service = task_service
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "[::1]", "testserver"]
    )

    @app.middleware("http")
    async def same_origin(request, call_next):
        origin = request.headers.get("origin")
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            if origin and (
                urlparse(origin).netloc != request.headers.get("host")
                or urlparse(origin).scheme != request.url.scheme
            ):
                return JSONResponse({"detail": "拒绝跨来源写入"}, status_code=403)
            if request.headers.get("sec-fetch-site") == "cross-site":
                return JSONResponse({"detail": "拒绝跨站请求"}, status_code=403)
            length = request.headers.get("content-length")
            if length and (not length.isdigit() or int(length) > 65536):
                return JSONResponse({"detail": "请求体超限"}, status_code=413)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'"
        )
        return response

    @app.exception_handler(ValueError)
    async def invalid(request, error):
        return JSONResponse({"detail": str(error)}, status_code=400)

    @app.exception_handler(RuntimeError)
    async def service_failure(request, error):
        from web.diagnostics import safe_diagnostic

        diagnostic = safe_diagnostic(error, "web_api")
        return JSONResponse(
            {
                "detail": diagnostic["title"] + "；" + diagnostic["suggestion"],
                "diagnostic": diagnostic,
            },
            status_code=503,
        )

    def session(identifier):
        value = store.get_session(identifier)
        if not value:
            raise HTTPException(404, "会话不存在")
        settings.workspace(value["workspace"])  # 目录变化后仍复查边界。
        return value

    def run(identifier):
        value = store.get_run(identifier)
        if not value:
            raise HTTPException(404, "任务不存在")
        return value

    @app.get("/api/sessions/{identifier}/tasks")
    def tasks(identifier: str):
        session(identifier)
        return task_service.request(identifier, "list_tasks")

    @app.get("/api/sessions/{identifier}/tasks/{task_id}")
    def task_status(identifier: str, task_id: str, offset: int = 0):
        session(identifier)
        return task_service.request(
            identifier, "task_status", {"task_id": task_id, "offset": offset}
        )

    @app.post("/api/sessions/{identifier}/tasks/{task_id}/input")
    def task_input(identifier: str, task_id: str, body: TaskInput):
        session(identifier)
        if not body.allow:
            return {"ok": False, "error": "用户拒绝发送终端输入"}
        check_input(body.text) if body.text.strip() else None
        result = task_service.request(
            identifier, "task_input", {"task_id": task_id, "text": body.text}
        )
        # 用户按钮只授权此动作，不能改变归属检查、终端状态和隔离环境。
        return result

    @app.post("/api/sessions/{identifier}/tasks/{task_id}/cancel")
    def task_cancel(identifier: str, task_id: str, body: Approval):
        session(identifier)
        if not body.allow:
            return {"ok": False, "error": "用户拒绝取消任务"}
        return task_service.request(identifier, "task_cancel", {"task_id": task_id})

    @app.post("/api/sessions/{identifier}/tasks/{task_id}/approvals/{approval_id}")
    def task_approval(identifier: str, task_id: str, approval_id: str, body: Approval):
        session(identifier)
        return task_service.request(
            identifier,
            "resolve_task_approval",
            {"task_id": task_id, "approval_id": approval_id, "allow": body.allow},
        )

    @app.get("/api/runs/{identifier}/diagnostics")
    def diagnostics(identifier: str):
        run(identifier)
        return [
            event["payload"] for event in store.events(identifier) if event["kind"] == "diagnostic"
        ][-50:]

    def file_path(identifier, path):
        root = Path(session(identifier)["workspace"])
        candidate = (root / path).resolve()
        if not candidate.is_relative_to(root) or any(
            part in permission_config["blocked_names"] or part.startswith(".")
            for part in candidate.relative_to(root).parts
        ):
            raise ValueError("禁止访问项目外或私有文件")
        if candidate.is_relative_to(settings.state_dir):
            raise ValueError("禁止访问工作台私有状态")
        return candidate

    @app.get("/api/sessions/{identifier}/git/status")
    def git_status(identifier: str):
        return runner.git.status(session(identifier)["workspace"])

    @app.get("/api/sessions/{identifier}/git/diff")
    def git_diff(identifier: str):
        value = runner.git.diff(session(identifier)["workspace"])
        # Git diff 同样是外部数据，界面不执行 HTML，疑似密钥脱敏。
        return json.loads(redact(json.dumps(value, ensure_ascii=False)))

    @app.get("/api/sessions/{identifier}/git/snapshots")
    def snapshots(identifier: str):
        return runner.git.list_snapshots(session(identifier)["workspace"])

    @app.post("/api/sessions/{identifier}/git/snapshots", status_code=201)
    def snapshot(identifier: str):
        from harness.infrastructure.workspace_locks import workspace_write_lock

        workspace = session(identifier)["workspace"]
        with workspace_write_lock(workspace):
            return runner.git.snapshot(workspace, "manual")

    @app.post("/api/sessions/{identifier}/git/restore-preview")
    def preview_restore(identifier: str, body: RestorePreview):
        file_path(identifier, body.path)
        return runner.git.preview_restore(
            session(identifier)["workspace"], body.snapshot_id, body.path
        )

    @app.post("/api/sessions/{identifier}/git/restore")
    def restore(identifier: str, body: Restore):
        if not body.allow:
            return {"restored": False, "message": "用户拒绝恢复，文件未修改"}
        target = file_path(identifier, body.path)
        from approval import write_boundary

        boundary = write_boundary(target)
        if not boundary["ok"]:
            raise HTTPException(403, boundary["error"])
        from harness.infrastructure.workspace_locks import workspace_write_lock

        workspace = session(identifier)["workspace"]
        with workspace_write_lock(workspace):
            return runner.git.restore(workspace, body.snapshot_id, body.path, body.expected_hash)

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "model_ready": settings.model_ready,
            "provider": "openai-compatible",
            "model": settings.model,
            "workspace_root": str(settings.workspace_root),
            "features": ["langgraph", "rag", "memory", "approval", "four-layer-guardrails"],
            "retrieval": (
                "semantic-vector + keyword"
                if knowledge.embedding_kind == "semantic"
                else "hash-vector + keyword; 非语义模型"
            ),
        }

    @app.get("/api/sessions")
    def sessions():
        return store.list_sessions()

    @app.post("/api/sessions", status_code=201)
    def new_session(body: NewSession):
        return store.create_session(body.title, settings.workspace(body.workspace))

    @app.post("/api/sessions/{identifier}/rename")
    def rename(identifier: str, body: Rename):
        session(identifier)
        return store.rename_session(identifier, body.title)

    @app.get("/api/sessions/{identifier}/messages")
    def messages(identifier: str):
        session(identifier)
        return store.messages(identifier)

    @app.post("/api/sessions/{identifier}/runs", status_code=202)
    def submit(identifier: str, body: Message):
        session(identifier)
        try:
            return runner.submit(identifier, body.message)
        except RuntimeError as error:
            raise HTTPException(503, str(error)) from error

    @app.get("/api/runs")
    def runs():
        return store.list_runs()

    @app.get("/api/runs/{identifier}")
    def status(identifier: str):
        return run(identifier)

    @app.post("/api/runs/{identifier}/cancel")
    def cancel(identifier: str):
        run(identifier)
        return {"ok": runner.cancel(identifier)}

    @app.post("/api/runs/{identifier}/resume", status_code=202)
    def resume(identifier: str):
        run(identifier)
        try:
            return runner.continue_run(identifier)
        except RuntimeError as error:
            raise HTTPException(503, str(error)) from error

    @app.get("/api/runs/{identifier}/approvals")
    def approvals(identifier: str):
        run(identifier)
        return store.pending_approvals(identifier)

    @app.post("/api/approvals/{identifier}")
    def approve(identifier: str, body: Approval):
        result = runner.approve(identifier, body.allow)
        if not result:
            raise HTTPException(409, "审批已结束或运行已停止")
        return result

    @app.get("/api/runs/{identifier}/events")
    async def events(identifier: str, request: Request, after: int = 0):
        run(identifier)
        try:
            cursor = max(after, int(request.headers.get("last-event-id", "0")))
        except ValueError:
            raise HTTPException(400, "事件游标无效")
        if cursor < 0:
            raise HTTPException(400, "事件游标无效")

        async def stream():
            nonlocal cursor
            while not await request.is_disconnected():
                batch = await asyncio.to_thread(store.events, identifier, cursor)
                for event in batch:
                    cursor = event["id"]
                    yield f"id: {cursor}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                current = await asyncio.to_thread(store.get_run, identifier)
                if current["status"] not in ACTIVE:
                    # 重启中断的运行也发送终态，客户端不会无限重连。
                    if not batch or batch[-1]["kind"] != "done":
                        yield (
                            "data: "
                            + json.dumps(
                                {
                                    "kind": "done",
                                    "payload": {
                                        "status": current["status"],
                                        "answer": current["answer"],
                                        "error": current["error"],
                                    },
                                }
                            )
                            + "\n\n"
                        )
                    return
                yield ": heartbeat\n\n"
                await asyncio.sleep(0.3)

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/sessions/{identifier}/memories")
    def memories(identifier: str):
        return knowledge.list_memories(session(identifier)["workspace"])

    @app.post("/api/sessions/{identifier}/memories", status_code=201)
    def remember(identifier: str, body: Memory):
        check_input(body.content)
        return knowledge.add_memory(
            session(identifier)["workspace"], body.content, session_id=identifier
        )

    @app.delete("/api/memories/{identifier}")
    def forget(identifier: str):
        return {"ok": knowledge.delete_memory(identifier)}

    @app.patch("/api/memories/{identifier}")
    def update_memory(identifier: str, body: Memory):
        check_input(body.content)
        result = knowledge.update_memory(identifier, body.content)
        if result is None:
            raise HTTPException(404, "记忆不存在")
        return result

    @app.post("/api/sessions/{identifier}/index")
    def index(identifier: str):
        return knowledge.index(session(identifier)["workspace"])

    @app.post("/api/sessions/{identifier}/search")
    def search(identifier: str, body: Search):
        return knowledge.search(session(identifier)["workspace"], body.query)

    @app.get("/api/sessions/{identifier}/files")
    def files(identifier: str):
        root = Path(session(identifier)["workspace"])
        items = []
        import os

        for directory, dirs, names in os.walk(root):
            dirs[:] = [
                name
                for name in dirs
                if not name.startswith(".")
                and name not in ("node_modules", "artifacts", "__pycache__", "sessions")
                and not (Path(directory) / name).is_symlink()
            ]
            for name in names:
                path = Path(directory) / name
                if (
                    name not in permission_config["blocked_names"]
                    and not name.startswith(".")
                    and not path.is_symlink()
                    and path.suffix
                    in (
                        ".py",
                        ".md",
                        ".txt",
                        ".js",
                        ".ts",
                        ".json",
                        ".toml",
                        ".yaml",
                        ".yml",
                        ".html",
                        ".css",
                    )
                ):
                    items.append(path.relative_to(root).as_posix())
                if len(items) >= 2000:
                    return {"files": sorted(items), "truncated": True}
        return {"files": sorted(items), "truncated": False}

    @app.get("/api/sessions/{identifier}/file")
    def file(identifier: str, path: str):
        candidate = file_path(identifier, path)
        if not candidate.is_file():
            raise HTTPException(404, "文件不存在")
        with candidate.open("rb") as handle:
            data = handle.read(262145)
        if len(data) > 262144:
            raise ValueError("文件超过预览大小上限")
        try:
            return {"path": path, "content": redact(data.decode("utf-8"))}
        except UnicodeError:
            raise ValueError("文件不是 UTF-8 文本")

    static = Path(__file__).parent / "static"
    static.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory=static), name="static")

    @app.get("/")
    def home():
        return FileResponse(static / "index.html")

    return app
