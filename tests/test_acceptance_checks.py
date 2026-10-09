import json

from scripts.acceptance import inspect_history


def save_history(project, executions, final='完成'):
    path = project / '.ai-cli/sessions/acceptance.jsonl'
    path.parent.mkdir(parents=True)
    rows = [{'role': 'user', 'content': '修复任务'}]
    for name, args, result in executions:
        rows.append({'role': 'assistant', 'content': '', 'tool_calls': [
            {'function': {'name': name, 'arguments': args}}
        ]})
        rows.append({'role': 'tool', 'tool_name': name, 'content': json.dumps(result)})
    rows.append({'role': 'assistant', 'content': final})
    path.write_text('\n'.join(json.dumps(row) for row in rows) + '\n')
    return path


def workflow():
    return [
        ('run_tests', {'path': '.'}, {'ok': False, 'exit_code': 1, 'output': '2 failed'}),
        ('edit_file', {'path': 'discount.py'}, {'ok': True, 'changed': True}),
        ('create_file', {'path': 'test_discount_edges.py'}, {'ok': True, 'changed': True}),
        ('run_tests', {'path': '.'}, {'ok': True, 'exit_code': 0, 'output': '8 passed'}),
    ]


def test_claimed_success_without_tools_does_not_pass(tmp_path):
    save_history(tmp_path, [], final='全部测试通过，文件已修复')
    _, calls, checks = inspect_history(tmp_path)
    assert calls == []
    assert not checks['failure_before_first_write'] and not checks['passed_after_last_write']
    assert not checks['edit_executed'] and not checks['create_executed']


def test_real_result_sequence_passes_workflow_checks(tmp_path):
    save_history(tmp_path, workflow())
    _, _, checks = inspect_history(tmp_path)
    assert all(checks.values())


def test_failure_after_write_does_not_meet_initial_failure_criterion(tmp_path):
    calls = workflow()
    calls[0], calls[1] = calls[1], calls[0]
    save_history(tmp_path, calls)
    assert not inspect_history(tmp_path)[2]['failure_before_first_write']


def test_wrong_new_file_does_not_meet_required_file_criterion(tmp_path):
    calls = workflow()
    calls[2] = ('create_file', {'path': 'irrelevant.py'}, {'ok': True, 'changed': True})
    save_history(tmp_path, calls)
    assert not inspect_history(tmp_path)[2]['create_executed']


def test_unfinished_tool_chain_is_not_accepted(tmp_path):
    path = save_history(tmp_path, [])
    with path.open('a') as file:
        file.write(json.dumps({'role': 'assistant', 'content': '', 'tool_calls': [
            {'function': {'name': 'run_tests', 'arguments': {'path': '.'}}}
        ]}) + '\n')
    assert not inspect_history(tmp_path)[2]['tool_chain_complete']
