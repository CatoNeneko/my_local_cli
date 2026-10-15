"""本地静态页面的 DOM 验收；API 由浏览器内存夹具拦截，不连接模型。"""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "web"


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def log_message(self, *_args):
        pass


def wait_for_page(page, diagnostics, stage, wait_method, *args, **kwargs):
    try:
        return getattr(page, wait_method)(*args, **kwargs)
    except Exception:
        screenshot_path = ROOT / "artifacts" / "ui_readability_failure.png"
        failure = {
            "stage": stage,
            "errorBanner": None,
            "requestPaths": diagnostics["requestPaths"][-30:],
            "requestFailures": diagnostics["requestFailures"][-10:],
            "pageErrors": diagnostics["pageErrors"][-10:],
            "consoleErrors": diagnostics["consoleErrors"][-10:],
            "screenshot": str(screenshot_path),
        }
        try:
            failure["errorBanner"] = page.evaluate(
                """() => {
                  const banner = document.getElementById('errorBanner');
                  return banner ? { hidden: banner.hidden, text: banner.textContent.trim() } : null;
                }"""
            )
        except Exception as error:
            failure["errorBannerReadError"] = str(error)
        try:
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot_path), full_page=True)
        except Exception as error:
            failure["screenshotError"] = str(error)
        print(
            "UI readability acceptance wait failed:\n"
            + json.dumps(failure, ensure_ascii=False, indent=2),
            file=sys.stderr,
        )
        raise


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise SystemExit("需要已有的 Playwright 安装；脚本不会安装或升级依赖。") from error

    assistant_text = (
        "# Markdown 标题\n\n"
        "段落含 **粗体**、`inline code` 和 [安全链接](https://example.com/docs)。\n\n"
        "- 无序项\n- 第二项\n\n"
        "1. 有序项\n2. 第二项\n\n"
        "```python\n"
        "complete = 'fence-content'\n"
        "print(complete)\n"
        "```\n\n"
        '<img src=x onerror="window.__markdownXss = true">\n'
        "<script>window.__markdownXss = true</script>\n"
        "[javascript](javascript:window.__markdownXss=true)\n"
        "[data](data:text/html,alert(1))\n"
        "[file](file:///etc/passwd)\n"
        "https://example.org/plain-link"
    )
    user_text = '**user text stays plain** <img src=x onerror="window.__markdownXss = true">'
    sessions = [
        {"id": "readability-one", "title": "Fixture One", "workspace": "/workspace/one"},
        {"id": "readability-two", "title": "Fixture Two", "workspace": "/workspace/two"},
    ]

    server = ThreadingHTTPServer(("127.0.0.1", 0), QuietStaticHandler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    report = {"checks": {}}

    try:
        with sync_playwright() as playwright:
            executable = next(
                (ROOT / ".browser-runtime").glob(
                    "chromium_headless_shell-*/chrome-linux/headless_shell"
                ),
                None,
            )
            if executable is None:
                executable = next(
                    (ROOT / ".browser-runtime").glob(
                        "chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell"
                    ),
                    None,
                )
            if executable is None:
                raise SystemExit(".browser-runtime 中没有已缓存的 Chromium；脚本不会下载浏览器。")
            browser = playwright.chromium.launch(
                executable_path=str(executable),
                headless=True,
                chromium_sandbox=True,
            )
            page = browser.new_page()
            diagnostics = {
                "requestPaths": [],
                "requestFailures": [],
                "pageErrors": [],
                "consoleErrors": [],
            }

            def record_request(request):
                entry = {"method": request.method, "path": urlsplit(request.url).path}
                if entry not in diagnostics["requestPaths"]:
                    diagnostics["requestPaths"].append(entry)

            page.on("request", record_request)
            page.on(
                "requestfailed",
                lambda request: diagnostics["requestFailures"].append(
                    {
                        "method": request.method,
                        "path": urlsplit(request.url).path,
                        "failure": request.failure,
                    }
                ),
            )
            page.on("pageerror", lambda error: diagnostics["pageErrors"].append(str(error)))
            page.on(
                "console",
                lambda message: (
                    diagnostics["consoleErrors"].append(message.text)
                    if message.type == "error"
                    else None
                ),
            )

            def fulfill_api(route):
                path = urlsplit(route.request.url).path
                if path == "/api/health":
                    payload = {"model_ready": False, "provider": "offline-fixture", "features": []}
                elif path == "/api/sessions":
                    payload = sessions
                elif path.endswith("/runs") and route.request.method == "POST":
                    message = (route.request.post_data_json or {}).get("message", "")
                    if message == "保留失败草稿":
                        route.fulfill(
                            status=503,
                            content_type="application/json",
                            body=json.dumps({"detail": "fixture submission failed"}),
                        )
                        return
                    payload = {"id": "fixture-run", "status": "running"}
                elif path == "/api/sessions/readability-one/messages":
                    payload = [
                        {"role": "user", "content": user_text},
                        {"role": "assistant", "content": assistant_text},
                    ]
                elif path.endswith("/messages"):
                    payload = []
                elif path.endswith("/files") or path.endswith("/memories"):
                    payload = []
                else:
                    payload = {}
                route.fulfill(status=200, content_type="application/json", body=json.dumps(payload))

            page.route("**/api/**", fulfill_api)
            wait_for_page(
                page,
                diagnostics,
                "load static page",
                "goto",
                f"http://127.0.0.1:{server.server_port}/static/index.html",
                wait_until="domcontentloaded",
            )
            wait_for_page(
                page,
                diagnostics,
                "initial assistant markdown",
                "wait_for_selector",
                "#conversation .assistant-row .markdown-body",
            )

            rendered = page.evaluate(
                """() => {
                  const body = document.querySelector('#conversation .assistant-row .markdown-body');
                  const links = Array.from(body.querySelectorAll('a'));
                  const code = body.querySelector('.markdown-code-block code');
                  return {
                    heading: body.querySelector('h1')?.textContent || '',
                    strong: body.querySelector('strong')?.textContent || '',
                    inlineCode: body.querySelector('.markdown-inline-code')?.textContent || '',
                    unorderedItems: body.querySelectorAll('ul > li').length,
                    orderedItems: body.querySelectorAll('ol > li').length,
                    language: body.querySelector('.markdown-code-language')?.textContent || '',
                    fence: code?.textContent || '',
                    unsafeElements: body.querySelectorAll('img, script, svg, iframe, object, embed').length,
                    unsafeLinks: links.filter((link) => !/^https?:$/.test(new URL(link.href).protocol)).length,
                    safeLinkSecurity: links.every((link) =>
                      link.target === '_blank' && link.rel.includes('noopener') && link.rel.includes('noreferrer')),
                    dangerousLinkLabelsNotAnchors: !links.some((link) =>
                      ['javascript', 'data', 'file'].includes(link.textContent.toLowerCase())),
                    xssExecuted: Boolean(window.__markdownXss),
                    dangerousTextVisible: body.textContent.includes('[javascript]') && body.textContent.includes('[data]') && body.textContent.includes('[file]')
                  };
                }"""
            )
            report["checks"].update(
                {
                    "markdown_blocks_and_inline": (
                        rendered["heading"] == "Markdown 标题"
                        and rendered["strong"] == "粗体"
                        and rendered["inlineCode"] == "inline code"
                        and rendered["unorderedItems"] == 2
                        and rendered["orderedItems"] == 2
                    ),
                    "fenced_code_and_language": (
                        rendered["language"] == "python"
                        and rendered["fence"] == "complete = 'fence-content'\nprint(complete)"
                    ),
                    "xss_and_dangerous_links_blocked": (
                        rendered["unsafeElements"] == 0
                        and rendered["unsafeLinks"] == 0
                        and rendered["safeLinkSecurity"]
                        and rendered["dangerousLinkLabelsNotAnchors"]
                        and not rendered["xssExecuted"]
                        and rendered["dangerousTextVisible"]
                    ),
                }
            )

            user_rendered = page.locator("#conversation .user-row .message-text")
            report["checks"]["user_message_remains_plain_text"] = (
                user_rendered.count() == 1
                and user_rendered.evaluate("element => element.textContent") == user_text
                and user_rendered.locator("strong, img").count() == 0
            )

            page.evaluate(
                """() => Object.defineProperty(window.navigator, 'clipboard', {
                  configurable: true,
                  value: { writeText: async (value) => { window.__copiedCode = value; } }
                })"""
            )
            page.locator(".markdown-copy-button").click()
            wait_for_page(
                page,
                diagnostics,
                "copy button",
                "wait_for_function",
                "window.__copiedCode !== undefined",
            )
            copied = page.evaluate("window.__copiedCode")
            report["checks"]["copy_button_copies_complete_fence"] = (
                copied == rendered["fence"]
                and page.locator(".markdown-copy-button").inner_text() == "已复制"
            )

            streaming_fence = page.evaluate(
                """() => {
                  const host = document.createElement('div');
                  host.append(window.HarnessMarkdown.render('```js\\nconst live = true;'));
                  return {
                    code: host.querySelector('.markdown-code-block code')?.textContent || '',
                    language: host.querySelector('.markdown-code-language')?.textContent || '',
                    copyButton: Boolean(host.querySelector('.markdown-copy-button'))
                  };
                }"""
            )
            report["checks"]["unfinished_streaming_fence_renders"] = streaming_fence == {
                "code": "const live = true;",
                "language": "js",
                "copyButton": True,
            }

            keyboard = page.evaluate(
                """() => {
                  const input = document.getElementById('messageInput');
                  const form = document.getElementById('chatForm');
                  form.requestSubmit = () => { form.dataset.fixtureSubmitCount = String(Number(form.dataset.fixtureSubmitCount || 0) + 1); };
                  const dispatch = (options) => {
                    const event = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true, ...options });
                    input.dispatchEvent(event);
                    return event.defaultPrevented;
                  };
                  const composingPrevented = dispatch({ isComposing: true });
                  const imeKeyCodePrevented = dispatch({ keyCode: 229 });
                  const shiftedPrevented = dispatch({ shiftKey: true });
                  const plainPrevented = dispatch({});
                  return {
                    composingPrevented,
                    imeKeyCodePrevented,
                    shiftedPrevented,
                    plainPrevented,
                    submitCount: Number(form.dataset.fixtureSubmitCount || 0)
                  };
                }"""
            )
            report["checks"]["composer_preserves_ime_and_shift_enter"] = (
                not keyboard["composingPrevented"]
                and not keyboard["imeKeyCodePrevented"]
                and not keyboard["shiftedPrevented"]
                and keyboard["plainPrevented"]
                and keyboard["submitCount"] == 1
            )

            page.evaluate(
                """() => {
                  delete document.getElementById('chatForm').requestSubmit;
                  window.__fixtureEventSources = [];
                  window.EventSource = class {
                    constructor(url) {
                      this.url = url;
                      this.listeners = new Map();
                      window.__fixtureEventSources.push(this);
                    }
                    addEventListener(name, listener) {
                      const listeners = this.listeners.get(name) || [];
                      listeners.push(listener);
                      this.listeners.set(name, listeners);
                    }
                    emit(name, payload, id) {
                      const message = { kind: name, payload };
                      if (id !== undefined) message.id = id;
                      const event = { data: JSON.stringify(message) };
                      (this.listeners.get(name) || []).forEach((listener) => listener(event));
                    }
                    close() {}
                  };
                }"""
            )
            page.locator("#messageInput").fill("提交后清理")
            page.keyboard.press("Enter")
            wait_for_page(
                page,
                diagnostics,
                "run event source created",
                "wait_for_function",
                "window.__fixtureEventSources.length === 1",
            )
            page.evaluate(
                """() => {
                  window.__historicalNodeBeforeTokens = document.querySelector(
                    '#conversation .assistant-row:not(.run-row) .markdown-body'
                  );
                  const source = window.__fixtureEventSources[0];
                  for (let index = 0; index < 10; index += 1) {
                    source.emit('token', { text: 'T' + index }, index + 1);
                  }
                  source.emit('token', { text: 'DUP' }, 10);
                  source.emit('token', { text: 'NOID' });
                }"""
            )
            page.evaluate("() => new Promise((resolve) => requestAnimationFrame(resolve))")
            token_batch = page.evaluate(
                """() => {
                  const historical = document.querySelector(
                    '#conversation .assistant-row:not(.run-row) .markdown-body'
                  );
                  const live = document.querySelector('#conversation .run-row .live-answer');
                  return {
                    historyNodePreserved: window.__historicalNodeBeforeTokens.isConnected &&
                      historical === window.__historicalNodeBeforeTokens,
                    renderedTokens: live?.textContent || ''
                  };
                }"""
            )
            report["checks"]["ten_tokens_update_without_rebuilding_history"] = (
                token_batch["historyNodePreserved"]
                and token_batch["renderedTokens"] == "T0T1T2T3T4T5T6T7T8T9NOID"
                and "DUP" not in token_batch["renderedTokens"]
            )
            page.evaluate(
                """() => {
                  const source = window.__fixtureEventSources[0];
                  source.emit('token', { text: 'pending tail' });
                  source.emit('done', { status: 'succeeded', answer: '完整最终答案' });
                }"""
            )
            wait_for_page(
                page,
                diagnostics,
                "done event rendered",
                "wait_for_function",
                "document.querySelector('#conversation .run-row .live-answer')?.textContent === '完整最终答案'",
            )
            report["checks"]["done_keeps_final_answer_after_pending_token"] = (
                page.locator("#conversation .run-row .live-answer").inner_text() == "完整最终答案"
            )
            wait_for_page(
                page,
                diagnostics,
                "draft cleared after success",
                "wait_for_function",
                "document.getElementById('messageInput').value === '' && "
                "sessionStorage.getItem('ai-workbench.draft.readability-one') === null",
            )
            wait_for_page(
                page,
                diagnostics,
                "composer enabled after completion",
                "wait_for_function",
                "!document.getElementById('messageInput').disabled",
            )
            page.locator("#messageInput").fill("保留失败草稿")
            page.keyboard.press("Enter")
            wait_for_page(
                page,
                diagnostics,
                "failed submission draft retained",
                "wait_for_function",
                "document.getElementById('messageInput').value === '保留失败草稿'",
            )
            report["checks"]["draft_clears_on_success_and_survives_failure"] = (
                page.evaluate("sessionStorage.getItem('ai-workbench.draft.readability-one')")
                == "保留失败草稿"
            )

            page.locator("#messageInput").fill("草稿一")
            page.locator(".session-select").nth(1).click()
            wait_for_page(
                page,
                diagnostics,
                "second session selected",
                "wait_for_function",
                "document.getElementById('currentSessionTitle').textContent === 'Fixture Two'",
            )
            second_session_starts_empty = page.locator("#messageInput").input_value() == ""
            page.locator("#messageInput").fill("草稿二")
            page.locator(".session-select").nth(0).click()
            wait_for_page(
                page,
                diagnostics,
                "first session selected",
                "wait_for_function",
                "document.getElementById('currentSessionTitle').textContent === 'Fixture One'",
            )
            first_draft_restored = page.locator("#messageInput").input_value() == "草稿一"
            page.locator("#sessionSearchInput").fill("/workspace/two")
            one_filtered_session = page.locator(".session-row").count() == 1
            page.keyboard.press("Control+k")
            search_focused = page.evaluate("document.activeElement.id === 'sessionSearchInput'")
            page.keyboard.press("Escape")
            search_cleared = page.locator("#sessionSearchInput").input_value() == ""
            report["checks"]["session_drafts_filter_and_shortcuts"] = (
                second_session_starts_empty
                and first_draft_restored
                and one_filtered_session
                and search_focused
                and search_cleared
            )

            screenshot_path = ROOT / "artifacts" / "upgrade" / "ui-readability.png"
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot_path), full_page=True)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        worker.join()

    report_path = ROOT / "artifacts" / "upgrade" / "ui-readability.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["checks"] or not all(report["checks"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
