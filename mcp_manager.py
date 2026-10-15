"""CLI 运行期间持有 MCP 连接；同步主循环通过 portal 请求异步操作。"""

import asyncio
from datetime import timedelta

from anyio import TASK_STATUS_IGNORED
from anyio.from_thread import start_blocking_portal
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from audit import record_tool_event
from config import mcp_config
from mcp_client import call_session_tool, collect_tools, prepare_server_connection
from mcp_tools import register_server_tools, unregister_server_tools
from permissions import authorize_external_tool


class MCPManager:
    def __init__(self):
        self.services = {}
        self.portal = None

    def __enter__(self):
        self.portal_context = start_blocking_portal()
        self.portal = self.portal_context.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            for name in list(self.services):
                self.disconnect(name)
        finally:
            self.portal_context.__exit__(exc_type, exc_value, traceback)
            self.portal = None

    async def _serve(self, connection, *, task_status=TASK_STATUS_IGNORED):
        closed = asyncio.Event()
        try:
            await self._serve_connected(connection, closed, task_status=task_status)
        finally:
            closed.set()

    async def _serve_connected(self, connection, closed, *, task_status=TASK_STATUS_IGNORED):
        # 由同一个异步任务进入、持有并退出 SDK 上下文，避免跨任务清理错误。
        queue = asyncio.Queue()
        async with stdio_client(connection["parameters"]) as (read_stream, write_stream):
            async with ClientSession(
                read_stream,
                write_stream,
                read_timeout_seconds=timedelta(seconds=connection["timeout"]),
            ) as session:
                async with asyncio.timeout(connection["timeout"]):
                    initialized = await session.initialize()
                    tools = await collect_tools(session)
                task_status.started(
                    {
                        "queue": queue,
                        "closed": closed,
                        "server": initialized.serverInfo.model_dump(mode="json"),
                        "tools": tools,
                    }
                )
                while True:
                    operation, arguments, response = await queue.get()
                    if operation == "close":
                        response.set_result({"ok": True})
                        return
                    try:
                        async with asyncio.timeout(connection["timeout"]):
                            if operation == "refresh":
                                result = {"ok": True, "tools": await collect_tools(session)}
                            else:
                                result = await call_session_tool(session, *arguments)
                        if not response.done():
                            response.set_result(result)
                    except Exception as error:
                        if not response.done():
                            response.set_result(
                                {
                                    "ok": False,
                                    "disconnected": True,
                                    "error": "MCP 通信失败: " + type(error).__name__,
                                }
                            )
                        return

    async def _request(self, handle, operation, arguments):
        response = asyncio.get_running_loop().create_future()
        await handle["queue"].put((operation, arguments, response))
        stopped = asyncio.wrap_future(handle["future"])
        done, pending = await asyncio.wait(
            [response, stopped],
            timeout=handle["connection"]["timeout"] + 3,
            return_when=asyncio.FIRST_COMPLETED,
        )
        if response in done:
            return response.result()
        response.cancel()
        raise ConnectionError("MCP 服务已停止或请求超时")

    def connect(self, name):
        if name in self.services:
            return {"ok": True, "message": "MCP 服务已经连接"}
        connection = prepare_server_connection(name)
        if not connection["ok"]:
            return connection
        authorized = authorize_external_tool("mcp_connect", name, "user", connection["details"])
        if not authorized["ok"]:
            record_tool_event("mcp_connect", authorized)
            return authorized
        try:
            future, started = self.portal.start_task(self._serve, connection)
            connection["manager"] = self
            connection["server_name"] = name
            self.services[name] = {**started, "future": future, "connection": connection}
            result = register_server_tools(name, {**started, "connection": connection})
            if not result["ok"]:
                self.disconnect(name)
        except Exception as error:
            result = {"ok": False, "error": "MCP 启动失败: " + type(error).__name__}
        result = {**result, "approval": authorized.get("approval", [])}
        record_tool_event("mcp_connect", result)
        return result

    def load_configured(self):
        return {name: self.connect(name) for name in mcp_config}

    def request(self, name, operation, arguments=()):
        handle = self.services.get(name)
        if handle is None or handle["future"].done():
            self.disconnect(name)
            return {"ok": False, "error": "MCP 服务未连接，请运行 /mcp refresh"}
        try:
            result = self.portal.call(self._request, handle, operation, arguments)
        except KeyboardInterrupt:
            self.abort(name)
            raise
        except Exception as error:
            result = {
                "ok": False,
                "disconnected": True,
                "error": "MCP 请求失败: " + type(error).__name__,
            }
        if result.get("disconnected"):
            self.disconnect(name)
        return result

    def call_tool(self, name, tool_name, schema, arguments):
        return self.request(name, "call", (tool_name, schema, arguments))

    def refresh(self, name):
        if name in self.services and self.services[name]["future"].done():
            self.disconnect(name)
        if name not in self.services:
            return self.connect(name)
        result = self.request(name, "refresh")
        if not result["ok"]:
            return result
        handle = self.services[name]
        registered = register_server_tools(name, {**result, "connection": handle["connection"]})
        if registered["ok"]:
            handle["tools"] = result["tools"]
        return registered

    def disconnect(self, name):
        handle = self.services.pop(name, None)
        unregister_server_tools(name)
        if handle is not None:
            try:
                if not handle["future"].done():
                    self.portal.call(self._request, handle, "close", ())
                handle["future"].result(timeout=5)
            except Exception:
                handle["future"].cancel()

    async def _wait_closed(self, event):
        async with asyncio.timeout(5):
            await event.wait()

    def abort(self, name):
        """取消连接拥有者任务，让 stdio 上下文关闭服务；不等待排队的 close。"""
        handle = self.services.pop(name, None)
        unregister_server_tools(name)
        if handle is not None:
            handle["future"].cancel()
            try:
                self.portal.call(self._wait_closed, handle["closed"])
            except Exception:
                pass

    def tool_names(self):
        from tool_registry import TOOL_REGISTRY

        return [name for name, spec in TOOL_REGISTRY.items() if spec.get("kind") == "mcp"]
