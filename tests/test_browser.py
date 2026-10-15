import asyncio
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import sys
import threading
from unittest.mock import AsyncMock, Mock

import pytest
from browser_runtime import BrowserController, validate_url
import permissions
import mcp_client
import mcp_manager
import tool_registry
import tool_runtime
from workspace import APP_ROOT, use_workspace


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "javascript:alert(1)",
        "data:text/html,hello",
        "https://user:pass@example.com",
        "",
        "http://",
        "http://a\n.example.com",
        "https://a b.com",
        "https://x:99999",
    ],
)
def test_bad_browser_url_rejected(url):
    with pytest.raises(ValueError):
        validate_url(url)


@pytest.mark.parametrize(
    "url", ["https://example.com/page?q=hello", "http://127.0.0.1:8000", "http://[::1]:8000"]
)
def test_http_and_local_url_allowed(url):
    assert validate_url(url) == url


def test_invalid_url_never_starts_browser():
    client = BrowserController("/tmp/browser-test-unused")
    client._start = AsyncMock(side_effect=AssertionError("不应启动"))
    with pytest.raises(ValueError):
        asyncio.run(client.open("file:///etc/passwd"))
    client._start.assert_not_called()


def test_screenshot_directory_is_bound_to_workspace_and_runtime_is_private(tmp_path, monkeypatch):
    monkeypatch.setitem(
        mcp_client.mcp_config,
        "browser",
        {**mcp_client.mcp_config["browser"], "command": sys.executable},
    )
    with use_workspace(tmp_path):
        spec = mcp_client.prepare_server_connection("browser")
        assert spec["ok"]
        env = spec["parameters"].env
        assert env["AI_CLI_BROWSER_ARTIFACTS"] == str(tmp_path / ".ai-cli/.browser-artifacts")
        assert env["PLAYWRIGHT_BROWSERS_PATH"] == str(APP_ROOT / ".browser-runtime")
        assert not permissions.resolve_project_path(".browser-runtime/secret")["ok"]
        assert not permissions.resolve_project_path(".browser-artifacts/screenshot.png")["ok"]


def test_password_and_upload_are_rejected_before_fill():
    async def check():
        client = BrowserController("/tmp/browser-test-unused")
        locator = AsyncMock()
        client._locator = Mock(return_value=locator)
        for kind in ("password", "file"):
            locator.get_attribute.return_value = kind
            with pytest.raises(ValueError):
                await client.fill("ref", "text")
        locator.fill.assert_not_called()

    asyncio.run(check())


def test_screenshot_symlink_refused_without_writing(tmp_path):
    destination = tmp_path / "screens"
    destination.symlink_to(tmp_path.parent, target_is_directory=True)
    client = BrowserController(destination)
    page = AsyncMock()
    page.screenshot.return_value = b"png"
    client._require_page = Mock(return_value=page)
    with pytest.raises(ValueError):
        asyncio.run(client.screenshot())


def test_browser_close_clears_refs_and_can_be_repeated():
    async def check():
        client = BrowserController("/tmp/browser-test-unused")
        browser, playwright = AsyncMock(), AsyncMock()
        client.browser, client.playwright = browser, playwright
        client.refs = {"old": {}}
        assert (await client.close())["ok"]
        assert (await client.close())["ok"]
        browser.close.assert_awaited_once()
        playwright.stop.assert_awaited_once()
        assert client.page is None and client.refs == {}

    asyncio.run(check())


@pytest.fixture
def website():
    page = b"""<!doctype html><title>Browser test</title>
<label>Name <input id="name" placeholder="Your name"></label>
<button onclick="document.getElementById('result').textContent='Hello '+document.getElementById('name').value; setTimeout(()=>document.getElementById('later').textContent='Ready',100)">Greet</button>
<div id="result"></div><div id="later"></div>
<input type="password" aria-label="Password"><input type="file" aria-label="Upload">
<a href="/missing">Missing</a>
"""

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.send_response(404 if self.path == "/missing" else 200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    thread.join()


real_browser = pytest.mark.skipif(
    os.environ.get("CLI_BROWSER_INTEGRATION") != "1", reason="需要真实 Chromium 与本地网页"
)


@real_browser
def test_real_browser_fill_click_wait_screenshot_and_ephemeral_session(
    tmp_path, website, monkeypatch
):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(APP_ROOT / ".browser-runtime"))

    async def check():
        client = BrowserController(tmp_path / "screens")
        try:
            opened = await client.open(website)
            assert opened["http_status"] == 200
            input_ref = next(
                item["ref"]
                for item in opened["elements"]
                if item["tag"] == "input" and item["type"] not in ("file", "password")
            )
            filled = await client.fill(input_ref, "Ada")
            with pytest.raises(ValueError):
                await client.fill(input_ref, "stale")
            button = next(item["ref"] for item in filled["elements"] if item["label"] == "Greet")
            clicked = await client.click(button)
            assert "Hello Ada" in clicked["text"]
            assert "Ready" in (await client.wait_text("Ready"))["text"]
            screenshot = await client.screenshot()
            assert Path(screenshot["path"]).read_bytes().startswith(b"\x89PNG")
            assert Path(screenshot["path"]).parent == tmp_path / "screens"
            await client.context.add_cookies(
                [{"name": "temporary", "value": "yes", "url": website}]
            )
            assert await client.context.cookies()
            await client.close()
            await client.open(website)
            assert not await client.context.cookies()
            missing = await client.open(website + "/missing")
            assert missing["http_status"] == 404
        finally:
            await client.close()

    asyncio.run(check())


@real_browser
def test_real_browser_mcp_uses_permissions_and_reports_errors(tmp_path, website, monkeypatch):
    confirm = Mock(return_value=True)
    monkeypatch.setattr(permissions, "confirm_tool", confirm)
    monkeypatch.setattr(tool_runtime, "record_tool_event", Mock())
    monkeypatch.setattr(mcp_manager, "record_tool_event", Mock())
    saved = dict(tool_registry.TOOL_REGISTRY)
    try:
        with use_workspace(tmp_path), mcp_manager.MCPManager() as manager:
            assert manager.connect("browser")["ok"]
            names = manager.tool_names()
            assert "mcp__browser__open_page" in names and "mcp__browser__screenshot" in names
            opened = tool_runtime.execute_tool("mcp__browser__open_page", {"url": website})
            assert opened["ok"] and opened["structured_content"]["title"] == "Browser test"
            confirm.return_value = False
            rejected = tool_runtime.execute_tool(
                "mcp__browser__open_page", {"url": website + "/missing"}
            )
            assert not rejected["ok"]
            confirm.return_value = True
            assert (
                tool_runtime.execute_tool("mcp__browser__read_page", {})["structured_content"][
                    "url"
                ]
                == website + "/"
            )
            invalid = tool_runtime.execute_tool("mcp__browser__click", {"ref": "missing"})
            assert not invalid["ok"]
            assert "browser" in manager.services  # 工具失败不误断开整个服务。
            screenshot = tool_runtime.execute_tool("mcp__browser__screenshot", {})
            assert screenshot["ok"]
            assert Path(screenshot["structured_content"]["path"]).is_relative_to(
                tmp_path / ".ai-cli"
            )
            assert tool_runtime.execute_tool("mcp__browser__close_browser", {})["ok"]
        assert not any(name.startswith("mcp__browser__") for name in tool_registry.TOOL_REGISTRY)
    finally:
        tool_registry.TOOL_REGISTRY.clear()
        tool_registry.TOOL_REGISTRY.update(saved)


def test_snapshot_budget_counts_json_escaping_and_keeps_only_returned_refs():
    async def check():
        client = BrowserController("/tmp/browser-test-unused")
        page = AsyncMock()
        page.url = "http://localhost/"
        page.title.return_value = "Budget"
        page.evaluate.return_value = {
            "text": '\\"\n' * 667,
            "text_truncated": False,
            "elements": [{"ref": str(i), "label": '\\"\n' * 26} for i in range(15)],
            "elements_truncated": False,
        }
        client._require_page = Mock(return_value=page)
        result = await client.read()
        import json

        assert len(json.dumps(result, ensure_ascii=False)) <= 4000
        assert result["text_truncated"]
        assert set(client.refs) == {item["ref"] for item in result["elements"]}

    asyncio.run(check())
