"""可信子代理入口：独立配置、独立上下文，仅允许四种只读项目工具。"""
import contextlib
import json
import sys


def main():
    payload = json.loads(sys.stdin.buffer.read(262145))
    from config import model_config, agent_config
    from workspace import use_workspace
    from tool_registry import TOOL_REGISTRY
    from model_client import request_message
    from tool_runtime import execute_tool
    allowed = {'read_file', 'list_files', 'search_file', 'search_project'}
    for name in list(TOOL_REGISTRY):
        if name not in allowed:
            del TOOL_REGISTRY[name]
    from agent_proposals import PROPOSALS, propose_edit, propose_file
    from tool_registry import tool_spec, string_parameter
    for name, handler in (('propose_edit', propose_edit), ('propose_file', propose_file)):
        TOOL_REGISTRY[name] = tool_spec('暂存文件修改建议，不写入；必须提供完整文件内容，由父代理审批后应用。',
            'read', {'path': string_parameter('项目文件路径', 1), 'new_content': {'type': 'string', 'maxLength': 16000}},
            ['path', 'new_content'], handler)
    model_config.update(payload['model_config'])
    messages = list(payload['instructions']) + [
        {'role': 'system', 'content': '你是只读子代理。独立完成指定分析并提供文件路径和证据；你不能直接修改文件或启动其他代理；需要修改时使用 propose_edit / propose_file 提出建议。'},
        {'role': 'user', 'content': '关注目录: ' + payload['path'] + '\n任务: ' + payload['task']}]
    calls = 0
    with use_workspace(payload['workspace']), contextlib.redirect_stdout(sys.stderr):
        # 子代理不访问父会话，审计仍通过共享执行入口记录。
        for _ in range(min(8, payload['agent_config']['max_rounds'])):
            message = request_message(messages, include_context=False)
            if not message.get('tool_calls'):
                return {'ok': True, 'reply': message['content'][:4000], 'reply_truncated': len(message['content']) > 4000, 'tool_calls': calls, 'proposals': list(PROPOSALS)}
            messages.append(message)
            for call in message['tool_calls']:
                calls += 1
                if calls > min(12, payload['agent_config']['max_tool_calls']):
                    return {'ok': False, 'error': '子代理工具预算耗尽'}
                function = call['function']
                result = execute_tool(function['name'], function.get('arguments', {}))
                item = {'role': 'tool', 'tool_name': function['name'], 'content': json.dumps(result, ensure_ascii=False)}
                if call.get('id'):
                    item['tool_call_id'] = call['id']
                messages.append(item)
    return {'ok': False, 'error': '子代理轮次预算耗尽'}


if __name__ == '__main__':
    try:
        result = main()
    except Exception as error:
        result = {'ok': False, 'error': '子代理失败: ' + type(error).__name__}
    print(json.dumps(result, ensure_ascii=False))
