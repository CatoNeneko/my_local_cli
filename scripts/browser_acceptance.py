"""真实模型通过统一工具循环操作固定本地网页；只授权该网页的浏览器工具。"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import tempfile
import threading
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent import run_agent
from config import model_config
import history
from mcp_manager import MCPManager
import permissions
from workspace import use_workspace


def main():
    marker = 'Ada_' + uuid.uuid4().hex[:8]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'''<!doctype html><title>Browser acceptance</title>
<label>Name<input id="name" placeholder="Name"></label>
<button onclick="document.getElementById('result').textContent='Hello '+document.getElementById('name').value">Greet</button>
<div id="result"></div>''')
    website = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = threading.Thread(target=website.serve_forever, daemon=True)
    worker.start()
    url = f'http://127.0.0.1:{website.server_port}/'
    workspace = Path(tempfile.mkdtemp(prefix='cli-browser-acceptance-'))
    old_confirm = permissions.confirm_tool
    approvals = []
    def confirm(name, target, details=''):
        allowed = target == 'browser' and name == 'mcp_connect'
        if target == 'browser' and name.startswith('mcp__browser__'):
            args = json.loads(details.split('\n工具参数: ', 1)[1])
            allowed = name != 'mcp__browser__open_page' or args.get('url') == url
        approvals.append({'tool': name, 'allowed': allowed})
        return allowed
    permissions.confirm_tool = confirm
    report = {'workspace': str(workspace), 'model': model_config['model'], 'checks': {}, 'approvals': approvals}
    try:
        with use_workspace(workspace), MCPManager() as manager:
            connection = manager.connect('browser')
            if not connection['ok']:
                raise RuntimeError(connection)
            messages = [{'role': 'user', 'content':
                f'浏览器验收：真实调用 MCP 浏览器工具打开 {url}，向 Name 输入框填写 {marker}，'
                '点击 Greet 按钮，读取并确认页面显示的 Hello 文字，然后保存截图。'
                '每次操作使用上一份结果中的最新 ref。只操作这个本地网页，不使用其他工具。'
                '最后告诉我页面实际显示的完整问候和截图路径。不要模拟工具结果。'}]
            history.append_messages(messages)
            reply = run_agent(messages)
            history.append_message({'role': 'assistant', 'content': reply})
            results = [(m['tool_name'], json.loads(m['content'])) for m in messages if m['role'] == 'tool']
            report['reply'] = reply
            report['tool_results'] = results
            checks = report['checks']
            for suffix in ('open_page', 'fill', 'click', 'screenshot'):
                checks[suffix] = any(name == 'mcp__browser__' + suffix and result.get('ok') for name, result in results)
            checks['actual_page_greeting'] = any('Hello ' + marker in result.get('structured_content', {}).get('text', '') for _, result in results)
            shots = [result['structured_content']['path'] for name, result in results
                     if name == 'mcp__browser__screenshot' and result.get('ok')]
            checks['real_png_in_private_directory'] = bool(shots) and all(
                Path(path).is_relative_to(workspace / '.ai-cli/.browser-artifacts') and Path(path).read_bytes().startswith(b'\x89PNG') for path in shots)
            checks['answer_matches_page'] = 'Hello ' + marker in reply
            checks['only_browser_tools'] = bool(results) and all(name.startswith('mcp__browser__') for name, _ in results)
            checks['no_failed_tools'] = all(result.get('ok') for _, result in results)
    finally:
        permissions.confirm_tool = old_confirm
        website.shutdown()
        website.server_close()
        worker.join()
        destination = ROOT / 'artifacts/browser/real_acceptance.json'
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report['checks'] or not all(report['checks'].values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
