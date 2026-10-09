"""当前 CLI 的有界进程任务；PTY 使用沙箱，子代理使用独立可信工作进程。"""
import atexit
import json
import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import threading
import time
import uuid

JOBS = {}
LOCK = threading.RLock()
MAX_OUTPUT = 65536


def launch(command, *, terminal=False, payload=None, timeout=120, kind='pty'):
    if kind == 'agent' and (not isinstance(payload, dict) or not all(isinstance(payload.get(key), str) for key in ('workspace', 'task'))):
        raise ValueError('子代理启动数据无效')
    with LOCK:
        if sum(job['process'].poll() is None for job in JOBS.values()) >= 4 or len(JOBS) >= 64:
            return {'ok': False, 'error': '任务数量达到上限（同时 4 个，本进程累计 64 个）'}
        master = slave = None
        if terminal:
            master, slave = pty.openpty()
        try:
            process = subprocess.Popen(command, stdin=slave if terminal else subprocess.PIPE,
                stdout=slave if terminal else subprocess.PIPE, stderr=slave if terminal else subprocess.DEVNULL,
                start_new_session=True, env=dict(os.environ) if kind == 'agent' else {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'})
        except BaseException:
            if master is not None:
                os.close(master)
            raise
        finally:
            if slave is not None:
                os.close(slave)
        identifier = uuid.uuid4().hex[:12]
        job = {'process': process, 'fd': master if terminal else process.stdout.fileno(),
               'output': bytearray(), 'reason': '', 'kind': kind, 'terminal': terminal,
               'done': False, 'lock': threading.RLock()}
        if kind == 'agent':
            from approval import current_task
            job['workspace'] = payload['workspace']
            job['task'] = current_task() or payload['task']
        JOBS[identifier] = job
    try:
        if payload is not None:
            process.stdin.write(json.dumps(payload, ensure_ascii=False).encode())
            process.stdin.close()
        thread = threading.Thread(target=_collect, args=(job, timeout), daemon=True)
        job['thread'] = thread
        thread.start()
    except BaseException:
        _kill(job)
        if process.stdin is not None and not terminal:
            try:
                process.stdin.close()
            except OSError:
                pass
        process.wait()
        _close(job)
        with LOCK:
            JOBS.pop(identifier, None)
        raise
    return {'ok': True, 'task_id': identifier, 'kind': kind, 'state': 'running'}


def _kill(job):
    try:
        os.killpg(job['process'].pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _close(job):
    if job['terminal']:
        os.close(job['fd'])
    else:
        job['process'].stdout.close()


def _collect(job, timeout):
    deadline = time.monotonic() + timeout
    try:
        while True:
            if time.monotonic() >= deadline:
                job['reason'] = 'timeout'
                _kill(job)
                break
            ready, _, _ = select.select([job['fd']], [], [], 0.1)
            if ready:
                try:
                    chunk = os.read(job['fd'], 8192)
                except OSError:
                    break
                if not chunk:
                    break
                with job['lock']:
                    remaining = MAX_OUTPUT - len(job['output'])
                    job['output'].extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        job['reason'] = 'output_limit'
                        _kill(job)
                        break
            elif job['process'].poll() is not None:
                break
    finally:
        # 给正常退出留出时间，然后清理仍占用终端的后代。
        try:
            job['process'].wait(timeout=0.2)
        except subprocess.TimeoutExpired:
            pass
        _kill(job)
        job['process'].wait()
        with job['lock']:
            _close(job)
            job['done'] = True


def inspect_task(task_id, offset=0):
    job = JOBS.get(task_id)
    if job is None:
        return {'ok': False, 'error': '未知任务 ID；任务仅在当前 CLI 进程有效'}
    with job['lock']:
        raw = bytes(job['output'])
        result = {'ok': True, 'task_id': task_id, 'kind': job['kind'],
                  'state': 'finished' if job['done'] else 'running',
                  'exit_code': job['process'].poll(), 'reason': job['reason'],
                  'output': raw[offset:offset+16000].decode('utf-8', errors='replace'),
                  'next_offset': min(len(raw), offset+16000), 'output_bytes': len(raw),
                  'more_output': len(raw) > offset+16000}
        if offset > len(raw):
            return {'ok': False, 'error': '输出偏移超过已收集长度'}
        if job['kind'] == 'agent' and job['done']:
            try:
                result['agent_result'] = json.loads(raw)
                proposals = result['agent_result'].get('proposals', [])
                result['agent_result']['proposals'] = [
                    {key: item.get(key) for key in ('proposal_id', 'tool', 'path')} for item in proposals]
                # 原始输出含建议源码；模型查询仅收到摘要，实际应用取内部完整数据。
                result['output'] = ''
                result['more_output'] = False
                reply = result['agent_result'].get('reply', '')
                if len(reply) > 16000:
                    result['agent_result']['reply'] = reply[:16000]
                    result['agent_result']['reply_truncated'] = True
            except (ValueError, UnicodeError):
                result['ok'] = False
                result['error'] = '子代理异常结束，未返回有效结果'
        return result


def send_input(task_id, text):
    job = JOBS.get(task_id)
    if job is None or not job['terminal']:
        return {'ok': False, 'error': '未知 PTY 任务'}
    with job['lock']:
        if job['done'] or job['process'].poll() is not None:
            return {'ok': False, 'error': '任务已结束'}
        data = text.encode('utf-8')
        written = os.write(job['fd'], data)
        return {'ok': written == len(data), 'bytes_written': written}


def cancel_task(task_id):
    job = JOBS.get(task_id)
    if job is None:
        return {'ok': False, 'error': '未知任务'}
    if job['done']:
        return inspect_task(task_id)
    job['reason'] = 'cancelled'
    _kill(job)
    job['thread'].join(timeout=2)
    return inspect_task(task_id)


def wait_task(task_id, seconds=10):
    job = JOBS.get(task_id)
    if job is None:
        return {'ok': False, 'error': '未知任务'}
    job['thread'].join(timeout=seconds)
    return inspect_task(task_id)


def list_tasks():
    return {'ok': True, 'tasks': [{key: value for key, value in inspect_task(identifier).items()
                                  if key in ('task_id', 'kind', 'state', 'exit_code', 'reason')}
                                 for identifier in JOBS]}


def close_tasks():
    for identifier in list(JOBS):
        cancel_task(identifier)
    JOBS.clear()


atexit.register(close_tasks)


def prepare_pty(path, argv, timeout=120):
    from sandbox import prepare_tests, build_test_command
    from permissions import PROJECT_ROOT
    checked = prepare_tests(path)
    if not checked['ok']:
        return checked
    target = Path(checked['path'])
    if not target.is_dir():
        return {'ok': False, 'error': 'PTY 工作路径必须是目录'}
    command = build_test_command(target, checked['bwrap'])
    split = command.index('--')
    # 在沙箱内恢复控制终端；在独立辅助解释器中执行，避免线程里 preexec_fn。
    helper = "import os,sys,fcntl,termios;\ntry: os.setsid()\nexcept PermissionError: pass\nfcntl.ioctl(0,termios.TIOCSCTTY,0); os.execvpe(sys.argv[1],sys.argv[1:],os.environ)"
    command = command[:split+1] + ['/usr/bin/python3', '-c', helper] + argv
    cwd_index = command.index('--chdir') + 1
    command[cwd_index] = str(Path('/workspace') / target.relative_to(PROJECT_ROOT))
    return {'ok': True, 'command': command, 'timeout': timeout,
            'details': '只读、禁网 PTY 命令: ' + json.dumps(argv, ensure_ascii=False) + '; 超时 ' + str(timeout)}


def start_pty(prepared):
    return launch(prepared['command'], terminal=True, timeout=prepared['timeout'])


def start_agent(path, task):
    from config import model_config, agent_config
    from project_instructions import build_model_messages
    from permissions import PROJECT_ROOT
    from workspace import APP_ROOT
    # 不共享父会话、MCP、可变模型配置；只读工具集合由可信工作进程确定。
    payload = {'workspace': str(PROJECT_ROOT), 'path': path, 'task': task,
               'model_config': dict(model_config), 'agent_config': dict(agent_config),
               'instructions': build_model_messages([])}
    return launch([str(APP_ROOT / '.conda-env/bin/python'), str(APP_ROOT / 'subagent_worker.py')],
                  payload=payload, kind='agent', timeout=180)
