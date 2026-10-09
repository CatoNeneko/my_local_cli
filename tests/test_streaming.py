import io
import json
from unittest.mock import Mock

import pytest

import agent
import history
import model_client
from config import model_config
from console_output import ConsoleOutput
from streaming import ModelResponseError, collect_stream


def stream_bytes(chunks):
    return b''.join(json.dumps(chunk, ensure_ascii=False).encode('utf-8') + b'\n' for chunk in chunks)


def chunk(content='', calls=None, done=False, **fields):
    message = {'content': content, **fields}
    if calls is not None:
        message['tool_calls'] = calls
    return {'message': message, 'done': done}


def call(name='read_file', arguments=None, index=0):
    return {'function': {'name': name, 'arguments': arguments or {'path': 'sample.py'}, 'index': index}}


def test_text_is_emitted_before_stream_finishes_and_thinking_is_accumulated():
    parts = [chunk(thinking='hidden '), chunk('你'), chunk('好', thinking='thought'), chunk(done=True)]
    response = io.BytesIO(stream_bytes(parts))
    emitted = []
    def show(text):
        assert response.tell() < len(response.getvalue())
        emitted.append(text)
    result = collect_stream(response, 10000, show)
    assert emitted == ['你', '好']
    assert result['content'] == '你好' and result['thinking'] == 'hidden thought'


def test_parallel_tool_calls_are_collected_from_multiple_chunks():
    first = call(index=0)
    second = call('list_files', {'path': '.'}, index=1)
    result = collect_stream(io.BytesIO(stream_bytes([
        chunk(calls=[first]), chunk(calls=[second]), chunk(done=True)
    ])), 10000)
    assert result['tool_calls'] == [first, second]


@pytest.mark.parametrize('raw', [
    stream_bytes([chunk('partial')]), b'not json\n', b'\xff\n', b'[]\n',
    stream_bytes([{'error': 'service failure'}]),
    stream_bytes([{'message': {'content': 'missing done'}}]),
    stream_bytes([chunk(calls=[{'function': {'name': 'read_file', 'arguments': '{'}}], done=True)]),
    stream_bytes([chunk(calls=[call(index=0)]), chunk(calls=[call(index=0)], done=True)])
])
def test_invalid_or_incomplete_stream_fails_explicitly(raw):
    with pytest.raises(ModelResponseError):
        collect_stream(io.BytesIO(raw), 10000)


def test_response_size_limit_and_blank_lines():
    raw = b'\n' + stream_bytes([chunk('ok', done=True)])
    assert collect_stream(io.BytesIO(raw), 10000)['content'] == 'ok'
    with pytest.raises(ModelResponseError, match='大小上限'):
        collect_stream(io.BytesIO(raw), 10)


def test_connection_reset_is_reported_and_timeout_remains_distinguishable():
    response = Mock()
    response.readline.side_effect = ConnectionResetError
    with pytest.raises(ModelResponseError, match='ConnectionResetError'):
        collect_stream(response, 10000)
    response.readline.side_effect = TimeoutError
    with pytest.raises(TimeoutError):
        collect_stream(response, 10000)


@pytest.fixture
def conversation(tmp_path, monkeypatch):
    monkeypatch.setattr(history, 'HISTORY_PATH', tmp_path / 'history.jsonl')
    monkeypatch.setitem(model_config, 'stream', True)
    messages = [{'role': 'user', 'content': 'read sample.py'}]
    history.append_messages(messages)
    return messages


def test_streaming_agent_waits_for_done_before_executing_and_prints_final_once(conversation, monkeypatch, capsys):
    first_response = io.BytesIO(stream_bytes([
        chunk('先读取。', thinking='plan'), chunk(calls=[call()]), chunk(done=True)
    ]))
    final_response = io.BytesIO(stream_bytes([chunk('变量是'), chunk('42'), chunk(done=True)]))
    responses = iter([first_response, final_response])
    requests = []
    def request(request, timeout):
        requests.append(json.loads(request.data))
        return next(responses)
    def execute(name, arguments):
        assert first_response.closed  # 请求返回、关闭响应后才执行工具。
        return {'ok': True, 'content': 'answer = 42'}
    monkeypatch.setattr(model_client.urllib.request, 'urlopen', request)
    monkeypatch.setattr(agent, 'execute_tool', execute)
    output = ConsoleOutput()
    reply = agent.run_agent(conversation, output=output)
    output.final(reply)
    assert reply == '变量是42'
    assert capsys.readouterr().out.count('变量是42') == 1
    assert all(request['stream'] for request in requests)
    assert requests[1]['messages'][-2]['thinking'] == 'plan'
    assert requests[1]['messages'][-1]['role'] == 'tool'
    assert history.load_history() == conversation
    assert len([m for m in conversation if m['role'] == 'assistant']) == 1


def test_stream_failure_never_executes_or_saves_partial_assistant(conversation, monkeypatch):
    response = io.BytesIO(stream_bytes([chunk('partial', calls=[call()])]))
    monkeypatch.setattr(model_client.urllib.request, 'urlopen', lambda *args, **kwargs: response)
    execute = Mock()
    monkeypatch.setattr(agent, 'execute_tool', execute)
    with pytest.raises(ModelResponseError):
        agent.run_agent(conversation, output=ConsoleOutput())
    execute.assert_not_called()
    assert history.load_history() == conversation
    assert len(conversation) == 1


def test_switch_stream_mode_changes_request_and_nonstream_prints_once(conversation, monkeypatch, capsys):
    requests = []
    def request(request, timeout):
        data = json.loads(request.data)
        requests.append(data)
        if data['stream']:
            return io.BytesIO(stream_bytes([chunk('one', done=True)]))
        return io.BytesIO(b'{"message":{"content":"two"}}')
    monkeypatch.setattr(model_client.urllib.request, 'urlopen', request)
    output = ConsoleOutput()
    output.final(agent.run_agent(conversation, output=output))
    monkeypatch.setitem(model_config, 'stream', False)
    output.final(agent.run_agent(conversation, output=output))
    assert [request['stream'] for request in requests] == [True, False]
    displayed = capsys.readouterr().out
    assert displayed.count('assistant: one') == 1
    assert displayed.count('assistant: two') == 1


def test_skill_generation_style_request_remains_nonstream(conversation, monkeypatch):
    requests = []
    def request(request, timeout):
        requests.append(json.loads(request.data))
        return io.BytesIO(b'{"message":{"content":"draft"}}')
    monkeypatch.setattr(model_client.urllib.request, 'urlopen', request)
    assert model_client.request_message(conversation, use_tools=False, include_context=False)['content'] == 'draft'
    assert requests[0]['stream'] is False and requests[0]['tools'] == []


def test_nonstream_response_size_limit(conversation, monkeypatch):
    monkeypatch.setitem(model_config, 'max_response_bytes', 10)
    monkeypatch.setattr(model_client.urllib.request, 'urlopen', lambda *args, **kwargs: io.BytesIO(b'x' * 100))
    with pytest.raises(ModelResponseError, match='大小上限'):
        model_client.request_message(conversation)
