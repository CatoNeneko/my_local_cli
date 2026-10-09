"""准备独立验收项目，检查真实 CLI 历史并保存证据；不模拟模型回复。"""
import argparse
import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

PROMPT = (
    '请完成这个折扣函数修复项目。先读取 README.md、discount.py 和 test_discount.py，'
    '在任何写入之前调用 run_tests 运行现有测试并观察失败。然后按说明修复 discount.py，'
    '使用 create_file 新建 test_discount_edges.py，覆盖 0%、100%、负价格和超范围折扣。'
    '禁止修改或删除固定的 test_discount.py。最后调用 run_tests 运行整个项目，'
    '若失败，根据真实错误继续修复；只根据工具结果报告最终状态。'
)
RESTART_PROMPT = '请只根据本会话已有历史回答：刚才修复了哪个文件、新建了哪个测试文件、最后测试是否通过？不要重新调用工具。'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    from config import model_config
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    evidence = APP_ROOT / 'artifacts/acceptance' / run_id
    evidence.mkdir(parents=True, exist_ok=False)
    project = Path(tempfile.mkdtemp(prefix='ai-cli-acceptance-', dir='/tmp'))
    seed = APP_ROOT / 'examples/acceptance_seed'
    for source in seed.iterdir():
        if source.is_file():
            name = source.name.removesuffix('.txt')
            (project / name).write_bytes(source.read_bytes())
    manifest = {
        'run_id': run_id, 'prepared_at': datetime.now(timezone.utc).isoformat(),
        'workspace': str(project), 'session': 'acceptance',
        'model': model_config['model'], 'base_url': model_config['base_url'], 'stream': model_config['stream'],
        'baseline_sha256': sha256(project / 'test_discount.py'),
        'criteria': ['真实失败在首次写入前', '实现修改', '新增边界测试', '修复后真实测试通过',
                     '固定测试未改变', '完整工具链', '另进程恢复会话', '独立边界验证通过'],
    }
    (evidence / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    (evidence / 'task.txt').write_text(PROMPT)
    print(json.dumps({'evidence': str(evidence), **manifest}, ensure_ascii=False, indent=2))


def inspect_history(project, session='acceptance'):
    from context_window import split_turns, valid_turn
    path = project / '.ai-cli/sessions' / (session + '.jsonl')
    messages = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    pending = []
    executions = []
    for message in messages:
        if message['role'] == 'assistant':
            pending.extend(call['function'] for call in message.get('tool_calls', []))
        elif message['role'] == 'tool':
            if not pending:
                raise ValueError('历史中存在孤立工具结果')
            call = pending.pop(0)
            executions.append({'name': call['name'], 'arguments': call.get('arguments', {}),
                               'result': json.loads(message['content'])})
    writes = [i for i, item in enumerate(executions)
              if item['name'] in ('edit_file', 'create_file') and item['result'].get('ok')
              and item['result'].get('changed')]
    failed = [i for i, item in enumerate(executions)
              if item['name'] == 'run_tests' and item['result'].get('exit_code') == 1
              and 'failed' in item['result'].get('output', '')]
    passed = [i for i, item in enumerate(executions)
              if item['name'] == 'run_tests' and item['result'].get('ok') is True
              and 'passed' in item['result'].get('output', '')]
    checks = {
        'failure_before_first_write': bool(writes and failed and min(failed) < min(writes)),
        'edit_executed': any(item['name'] == 'edit_file' and item['result'].get('ok') is True
                             and Path(item['arguments'].get('path', '')).name == 'discount.py'
                             and item['result'].get('changed') for item in executions),
        'create_executed': any(item['name'] == 'create_file' and item['result'].get('ok') is True
                               and Path(item['arguments'].get('path', '')).name == 'test_discount_edges.py'
                               and item['result'].get('changed') for item in executions),
        'passed_after_last_write': bool(writes and passed and max(passed) > max(writes)),
        'tool_chain_complete': bool(messages) and not pending and all(valid_turn(turn) for turn in split_turns(messages)),
    }
    return messages, executions, checks


def snapshot(evidence):
    manifest = json.loads((evidence / 'manifest.json').read_text())
    path = Path(manifest['workspace']) / '.ai-cli/sessions' / (manifest['session'] + '.jsonl')
    destination = evidence / 'initial_session.jsonl'
    if destination.exists():
        raise ValueError('初始历史快照已存在，拒绝覆盖')
    destination.write_bytes(path.read_bytes())
    print('已保存初始历史；在新的 CLI 进程中输入：\n' + RESTART_PROMPT)


def verify_restart(evidence):
    manifest = json.loads((evidence / 'manifest.json').read_text())
    project = Path(manifest['workspace'])
    previous = (evidence / 'initial_session.jsonl').read_bytes()
    current = (project / '.ai-cli/sessions' / (manifest['session'] + '.jsonl')).read_bytes()
    old_rows = [json.loads(line) for line in previous.decode().splitlines() if line.strip()]
    new_rows = [json.loads(line) for line in current.decode().splitlines() if line.strip()][len(old_rows):]
    reply = new_rows[-1].get('content', '') if new_rows else ''
    checks = {
        'original_history_preserved': current.startswith(previous),
        'new_followup_recorded': bool(new_rows) and new_rows[0].get('content') == RESTART_PROMPT,
        'no_tools_needed_for_recall': bool(new_rows) and all(row.get('role') != 'tool' for row in new_rows),
        'recalled_files': bool(new_rows) and new_rows[-1].get('role') == 'assistant'
                          and 'discount.py' in reply and 'test_discount_edges.py' in reply,
    }
    result = {'ok': all(checks.values()), 'checks': checks, 'workspace': str(project),
              'initial_sha256': hashlib.sha256(previous).hexdigest(), 'reply': reply}
    (evidence / 'restart_verified.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


def independent_verify(evidence):
    from tools import execute_tool
    from workspace import use_workspace
    manifest = json.loads((evidence / 'manifest.json').read_text())
    project = Path(manifest['workspace'])
    source = APP_ROOT / 'examples/acceptance_verify/test_acceptance_independent.py.txt'
    target = project / 'test_acceptance_independent.py'
    if target.exists():
        raise ValueError('独立验证文件已存在，拒绝覆盖；如需重跑可直接调用工具')
    with target.open('xb') as file:
        file.write(source.read_bytes())
    with use_workspace(project):
        result = execute_tool('run_tests', {'path': target.name}, source='user')
    result = {**result, 'test_sha256': sha256(target), 'workspace': str(project)}
    (evidence / 'independent_test_result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


def check(evidence):
    manifest = json.loads((evidence / 'manifest.json').read_text())
    project = Path(manifest['workspace'])
    messages, executions, checks = inspect_history(project, manifest['session'])
    checks['baseline_unchanged'] = sha256(project / 'test_discount.py') == manifest['baseline_sha256']
    checks['edge_test_exists'] = (project / 'test_discount_edges.py').is_file()
    # 另进程恢复与独立边界测试必须单独运行，不能用模型声称成功代替证据。
    restart = evidence / 'restart_verified.json'
    checks['restart_verified'] = (restart.is_file() and json.loads(restart.read_text()).get('ok') is True
                                  and json.loads(restart.read_text()).get('workspace') == str(project))
    independent = evidence / 'independent_test_result.json'
    checks['independent_tests_passed'] = (independent.is_file() and json.loads(independent.read_text()).get('ok') is True
                                         and '8 passed' in json.loads(independent.read_text()).get('output', '')
                                         and json.loads(independent.read_text()).get('test_sha256')
                                         == sha256(APP_ROOT / 'examples/acceptance_verify/test_acceptance_independent.py.txt'))
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'manifest': manifest,
              'checks': checks, 'passed': all(checks.values()),
              'additional_checks': {
                  'real_mcp_add_returned_42': any(
                      item['name'] == 'mcp__demo__add' and item['result'].get('ok') is True
                      and item['arguments'] == {'a': 19, 'b': 23}
                      and item['result'].get('structured_content') == {'result': 42}
                      for item in executions)
              },
              'tool_calls': [{'name': item['name'], 'ok': item['result'].get('ok'),
                              'exit_code': item['result'].get('exit_code')} for item in executions]}
    (evidence / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    (evidence / 'session.jsonl').write_text('\n'.join(json.dumps(row, ensure_ascii=False) for row in messages) + '\n')
    for name in ('discount.py', 'test_discount.py', 'test_discount_edges.py'):
        if (project / name).is_file():
            (evidence / (name + '.txt')).write_bytes((project / name).read_bytes())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)
    subparsers.add_parser('prepare')
    checker = subparsers.add_parser('check')
    checker.add_argument('evidence', type=Path)
    for command in ('snapshot', 'restart', 'verify'):
        subparsers.add_parser(command).add_argument('evidence', type=Path)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare()
    elif args.command == 'check':
        raise SystemExit(check(args.evidence))
    elif args.command == 'snapshot':
        snapshot(args.evidence)
    elif args.command == 'restart':
        raise SystemExit(verify_restart(args.evidence))
    elif args.command == 'verify':
        raise SystemExit(independent_verify(args.evidence))
