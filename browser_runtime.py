"""单页面、临时上下文的浏览器执行器；不暴露任意 JS、Shell 或文件路径。"""
import asyncio
import json
from pathlib import Path
from urllib.parse import urlsplit
import uuid

MAX_TEXT = 2000
MAX_ELEMENTS = 15
MAX_SCREENSHOTS = 32


def validate_url(url):
    if not isinstance(url, str) or not url or len(url) > 2048 or any(ord(char) < 32 or char.isspace() for char in url):
        raise ValueError('URL 必须是 1–2048 字符的 HTTP(S) 地址')
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username is not None or parsed.password is not None:
            raise ValueError()
        _ = parsed.port
    except ValueError as error:
        raise ValueError('只允许无嵌入凭据的 HTTP(S) URL；不支持 file/data/javascript') from error
    return url


# 固定的内部 JS，仅提取 DOM 与生成元素编号；模型没有 evaluate 接口。
SNAPSHOT_SCRIPT = """({prefix, textLimit, elementLimit}) => {
    const body = document.body;
    const text = (body?.innerText || '').slice(0, textLimit + 1);
    const candidates = [...document.querySelectorAll('a[href],button,input,textarea,select,[role="button"],[contenteditable="true"]')].slice(0,200);
    const elements = [];
    for (const node of candidates) {
        const box = node.getBoundingClientRect();
        if (!box.width || !box.height || getComputedStyle(node).visibility === 'hidden') continue;
        if (elements.length >= elementLimit) break;
        const ref = prefix + '-' + (elements.length + 1);
        node.setAttribute('data-ai-cli-ref', ref);
        const label = node.getAttribute('aria-label') || node.labels?.[0]?.innerText || node.getAttribute('placeholder') || node.innerText || node.getAttribute('name') || '';
        elements.push({ref, tag: node.tagName.toLowerCase(), type: (node.getAttribute('type') || '').slice(0,30),
            label: label.trim().slice(0,80), disabled: !!node.disabled});
    }
    return {text: text.slice(0,textLimit), text_truncated: text.length > textLimit,
        elements, elements_truncated: candidates.length > elements.length};
}"""


class BrowserController:
    def __init__(self, screenshot_directory):
        self.screenshot_directory = Path(screenshot_directory)
        self.playwright = self.browser = self.context = self.page = None
        self.refs = {}
        self.screenshots = 0

    async def _start(self):
        if self.browser is not None and self.browser.is_connected():
            return
        from playwright.async_api import async_playwright
        self.playwright = await async_playwright().start()
        try:
            self.browser = await self.playwright.chromium.launch(headless=True, chromium_sandbox=True, timeout=15000)
            self.context = await self.browser.new_context(viewport={'width': 1280, 'height': 720},
                accept_downloads=False, service_workers='block', permissions=[])
            self.context.set_default_timeout(5000)
            self.context.set_default_navigation_timeout(10000)
            await self.context.route('**/*', self._route)
            self.page = await self.context.new_page()
            self.context.on('page', lambda page: asyncio.create_task(page.close()) if page != self.page else None)
            self.page.on('download', lambda download: asyncio.create_task(download.cancel()))
        except BaseException:
            await self.close()
            raise

    async def _route(self, route):
        try:
            validate_url(route.request.url)
        except ValueError:
            await route.abort()
        else:
            await route.continue_()

    def _require_page(self):
        if self.page is None or self.page.is_closed():
            raise ValueError('尚未打开页面，请先调用 open_page')
        return self.page

    async def open(self, url):
        validate_url(url)
        await self._start()
        self.refs.clear()
        response = await self.page.goto(url, wait_until='domcontentloaded')
        result = await self.read()
        result['http_status'] = response.status if response else None
        return result

    async def read(self):
        page = self._require_page()
        if page.url != 'about:blank':
            validate_url(page.url)
        result = await page.evaluate(SNAPSHOT_SCRIPT, {'prefix': uuid.uuid4().hex[:8],
            'textLimit': MAX_TEXT, 'elementLimit': MAX_ELEMENTS})
        self.refs = {item['ref']: dict(item) for item in result['elements']}
        snapshot = {'ok': True, 'url': page.url[:300], 'url_truncated': len(page.url) > 300,
                    'title': (await page.title())[:200], **result}
        # MCP 同时返回正文 JSON 和结构化 JSON，转义字符也计入体积预算。
        while len(json.dumps(snapshot, ensure_ascii=False)) > 4000:
            if snapshot['text']:
                snapshot['text'] = snapshot['text'][:-200]
                snapshot['text_truncated'] = True
            elif snapshot['elements']:
                snapshot['elements'].pop()
                snapshot['elements_truncated'] = True
            else:
                break
        self.refs = {item['ref']: dict(item) for item in snapshot['elements']}
        return snapshot

    def _locator(self, ref):
        self._require_page()
        if ref not in self.refs:
            raise ValueError('元素编号不存在或已过期，请重新 read_page 并使用最新 ref')
        return self.page.locator('[data-ai-cli-ref="' + ref + '"]')

    async def click(self, ref):
        locator = self._locator(ref)
        await locator.click()
        await self.page.wait_for_load_state('domcontentloaded')
        return await self.read()

    async def fill(self, ref, value):
        if not isinstance(value, str) or len(value) > 4000 or '\x00' in value:
            raise ValueError('输入内容最多 4000 字符，不允许空字符')
        locator = self._locator(ref)
        if await locator.get_attribute('type') in ('file', 'password'):
            raise ValueError('基础版不支持文件上传或密码输入')
        await locator.fill(value)
        return await self.read()

    async def wait_text(self, text):
        if not isinstance(text, str) or not text or len(text) > 200:
            raise ValueError('等待文字必须是 1–200 字符')
        await self._require_page().get_by_text(text, exact=False).first.wait_for(state='visible', timeout=5000)
        return await self.read()

    async def screenshot(self):
        if self.screenshots >= MAX_SCREENSHOTS:
            raise ValueError('本次浏览器服务截图达到 32 张上限')
        raw = await self._require_page().screenshot(type='png', full_page=False, timeout=5000)
        if len(raw) > 4194304:
            raise ValueError('截图超过 4 MiB，未保存')
        directory = self.screenshot_directory
        if any(path.is_symlink() for path in (directory, *directory.parents)):
            raise ValueError('截图目录不能含符号链接')
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / (uuid.uuid4().hex + '.png')
        with path.open('xb') as file:
            file.write(raw)
        self.screenshots += 1
        return {'ok': True, 'path': str(path), 'bytes': len(raw), 'message': '截图仅保存为文件，未发送给视觉模型'}

    async def close(self):
        browser, playwright = self.browser, self.playwright
        self.browser = self.playwright = self.context = self.page = None
        self.refs.clear()
        try:
            if browser is not None:
                await browser.close()
        finally:
            if playwright is not None:
                await playwright.stop()
        return {'ok': True, 'message': '浏览器及临时会话已关闭'}
