"""工具参数、权限类型、准备函数和实现的唯一注册位置。"""
from copy import deepcopy

from file_tools import list_files, read_file, search_file
from patches import apply_prepared_edit, prepare_edit
from sandbox import execute_prepared_tests, prepare_tests
from skill_files import apply_prepared_skill, prepare_create_skill
from project_search import search_project
from new_files import apply_prepared_file, prepare_create_file


def string_parameter(description="", min_length=0):
    return {"type": "string", "description": description, "minLength": min_length}


def tool_spec(description, operation, properties, required, handler, prepare=None, defaults=None, details=""):
    return {
        "description": description,
        "operation": operation,
        "parameters": {
            "type": "object", "properties": properties,
            "required": required, "additionalProperties": False
        },
        "defaults": defaults or {},
        "handler": handler,
        "prepare": prepare,
        "details": details
    }


TOOL_REGISTRY = {
    "create_file": tool_spec(
        "新建项目内普通 UTF-8 文件，提供完整内容。展示 diff 并确认后创建父目录和文件；拒绝覆盖已有目标。",
        "write", {"path": string_parameter("新文件路径", 1), "new_content": string_parameter("完整 UTF-8 文字，允许空文件")},
        ["path", "new_content"], apply_prepared_file, prepare_create_file
    ),
    "search_project": tool_spec(
        "递归搜索项目 UTF-8 文本中的字面关键词，返回项目相对路径、行号和片段。"
        "可用 glob 如 '*.py' 筛选，跳过私有目录、依赖和符号链接；达到限制时返回部分结果和原因。",
        "read", {"path": string_parameter("搜索目录，默认 '.'", 1),
                 "keyword": string_parameter("区分大小写的字面关键词，不是正则表达式", 1),
                 "glob": string_parameter("文件匹配模式，默认 '*'", 1)},
        ["keyword"], search_project, defaults={"path": ".", "glob": "*"}
    ),
    "create_skill": tool_spec(
        "新建 skills/<名称>/SKILL.md。内容是任务流程说明，展示 diff 并确认后保存，不覆盖、不自动启用。",
        "write", {"path": string_parameter("skills/<名称>/SKILL.md", 1), "new_content": string_parameter("完整 Markdown 内容", 1)},
        ["path", "new_content"], apply_prepared_skill, prepare_create_skill
    ),
    "read_file": tool_spec(
        "读取项目内的 UTF-8 文本文件，返回内容或错误。", "read",
        {"path": string_parameter("文件路径", 1)}, ["path"], read_file
    ),
    "search_file": tool_spec(
        "在项目内文件中搜索关键词，返回匹配行及行号。", "read",
        {"path": string_parameter("文件路径", 1), "keyword": string_parameter("非空关键词", 1)},
        ["path", "keyword"], search_file
    ),
    "list_files": tool_spec(
        "列出项目目录的直接子项；根目录使用 '.'。受保护项目数据不展示。", "read",
        {"path": string_parameter("目录路径", 1)}, ["path"], list_files
    ),
    "edit_file": tool_spec(
        "修改已有 UTF-8 文件。先读取，再提供完整新内容。展示 diff 并由用户确认后写入；冲突时拒绝。",
        "write", {"path": string_parameter("文件路径", 1), "new_content": string_parameter("替换后的完整文字，不是 diff")},
        ["path", "new_content"], apply_prepared_edit, prepare_edit,
        details="确认后替换已有文件的完整内容"
    ),
    "run_tests": tool_spec(
        "在项目只读、默认禁网的 Linux 沙箱中运行 pytest；需要确认，返回退出码、输出和超时状态。",
        "execute", {"path": string_parameter("目录或 Python 测试文件，默认 '.'", 1)},
        [], execute_prepared_tests, prepare_tests, defaults={"path": "."}
    )
}


def get_tool_definitions():
    return [
        {"type": "function", "function": {
            "name": name, "description": spec["description"],
            "parameters": deepcopy(spec["parameters"])
        }}
        for name, spec in TOOL_REGISTRY.items()
    ]


from process_tasks import prepare_pty, start_pty, start_agent, inspect_task, send_input, cancel_task

TOOL_REGISTRY.update({
    'start_pty': tool_spec('启动只读、禁网 Linux 沙箱 PTY 命令，返回任务 ID；支持交互输入，退出 CLI 自动清理。',
        'execute', {'path': string_parameter('工作目录', 1),
                    'argv': {'type': 'array', 'items': {'type': 'string', 'minLength': 1, 'maxLength': 4096}, 'minItems': 1, 'maxItems': 64},
                    'timeout': {'type': 'integer', 'minimum': 1, 'maximum': 300}},
        ['argv'], start_pty, prepare_pty, defaults={'path': '.', 'timeout': 120}),
    'spawn_agent': tool_spec('启动独立只读子代理分析任务；可并行多个任务，使用 task_status 获取结果。不会共享聊天或修改文件。',
        'execute', {'path': string_parameter('关注目录', 1), 'task': {'type': 'string', 'minLength': 1, 'maxLength': 16000}},
        ['task'], start_agent, defaults={'path': '.'}),
    'task_status': tool_spec('查看当前 CLI 任务状态、结果及新增输出；offset 是字节偏移。',
        'read', {'task_id': string_parameter('任务 ID', 1), 'offset': {'type': 'integer', 'minimum': 0}},
        ['task_id'], inspect_task, defaults={'offset': 0}),
    'task_input': tool_spec('向 PTY 任务发送文字；换行需要包含在 text 中。需要确认。',
        'execute', {'task_id': string_parameter('任务 ID', 1), 'text': {'type': 'string', 'maxLength': 4096}},
        ['task_id', 'text'], send_input),
    'task_cancel': tool_spec('终止任务进程组并清理后代，需要确认。',
        'execute', {'task_id': string_parameter('任务 ID', 1)}, ['task_id'], cancel_task)
})
for _name in ('task_status', 'task_input', 'task_cancel'):
    TOOL_REGISTRY[_name]['kind'] = 'task'

from process_tasks import wait_task
TOOL_REGISTRY['task_wait'] = tool_spec('等待任务完成，最多等待 30 秒，未结束时返回当前状态。',
    'read', {'task_id': string_parameter('任务 ID', 1), 'seconds': {'type': 'integer', 'minimum': 1, 'maximum': 30}},
    ['task_id'], wait_task, defaults={'seconds': 10})
TOOL_REGISTRY['task_wait']['kind'] = 'task'

from agent_proposals import apply_proposal
TOOL_REGISTRY['apply_agent_proposal'] = tool_spec('申请应用已完成子代理的文件建议。内层执行器会重新检查路径、展示 diff、独立审批并验证冲突；不是直接写入。',
    'read', {'task_id': string_parameter('子代理任务 ID', 1), 'proposal_id': string_parameter('建议 ID', 1)},
    ['task_id', 'proposal_id'], apply_proposal)
TOOL_REGISTRY['apply_agent_proposal']['kind'] = 'task'
