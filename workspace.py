"""一次 CLI 运行的项目路径绑定，与助手安装目录和运行环境分开。"""
from contextlib import contextmanager
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent


@contextmanager
def use_workspace(directory):
    import audit
    import history
    import permissions
    import sandbox
    from project_instructions import instruction_state
    from skills import active_skills

    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        raise ValueError('工作目录不存在或不是目录: ' + str(root))
    # 保持原仓库历史位置兼容；外部项目使用被工具屏蔽的私有目录。
    state = root if root == APP_ROOT else root / '.ai-cli'
    if state.is_symlink():
        raise ValueError('项目状态目录不能是符号链接')
    if state.exists() and not state.is_dir():
        raise ValueError('项目状态路径不是目录: ' + str(state))
    for path in (state / 'history.jsonl', state / 'tool_events.jsonl', state / 'sessions'):
        if path.is_symlink():
            raise ValueError('项目状态路径不能是符号链接: ' + str(path))
        if path.exists() and ((path.name == 'sessions' and not path.is_dir())
                              or (path.name != 'sessions' and not path.is_file())):
            raise ValueError('项目状态路径类型无效: ' + str(path))
    old = (permissions.PROJECT_ROOT, sandbox.PROJECT_ROOT, history.HISTORY_PATH, audit.LOG_PATH,
           dict(instruction_state), dict(active_skills))
    permissions.PROJECT_ROOT = sandbox.PROJECT_ROOT = root
    history.HISTORY_PATH = state / 'history.jsonl'
    audit.LOG_PATH = state / 'tool_events.jsonl'
    active_skills.clear()
    instruction_state.update(status='missing', content='', message='尚未加载项目规则')
    try:
        yield root
    finally:
        permissions.PROJECT_ROOT, sandbox.PROJECT_ROOT, history.HISTORY_PATH, audit.LOG_PATH = old[:4]
        instruction_state.clear()
        instruction_state.update(old[4])
        active_skills.clear()
        active_skills.update(old[5])
