"""帮助和命令补全共用的命令说明。"""

COMMANDS = {
    "/browser": (
        "<open|read|click|fill|wait|screenshot|close>",
        "基础无头浏览器，使用页面返回的 ref 操作",
    ),
    "/compact": ("[status|auto on|auto off]", "手动压缩或管理自动上下文压缩"),
    "/approval": ("[auto|manual]", "查看或切换可信审批模式"),
    "/apply": ("<任务 ID> <建议 ID>", "审批并应用子代理文件建议"),
    "/pty": ("<命令及参数>", "启动沙箱 PTY 任务；Python 使用 python"),
    "/agent": ("<任务描述>", "启动独立开发子代理，修改经任务审批"),
    "/tasks": ("", "列出当前进程任务"),
    "/task": ("<任务 ID>", "查看输出和结果"),
    "/approve_task": ("<任务 ID> <审批 ID>", "审阅并批准子代理操作"),
    "/reject_task": ("<任务 ID> <审批 ID>", "拒绝子代理操作"),
    "/send": ("<任务 ID> <文字>", "向 PTY 发送一行输入"),
    "/cancel": ("<任务 ID>", "终止任务进程组"),
    "/help": ("", "查看帮助"),
    "/exit": ("", "退出并关闭连接"),
    "/history": ("", "查看当前历史"),
    "/clear": ("", "清空当前会话历史"),
    "/save": ("", "导出当前会话 JSON"),
    "/sessions": ("", "列出会话"),
    "/session": ("<名称>", "查看、切换或创建会话"),
    "/session rename": ("<新名称>", "重命名当前会话"),
    "/context": ("", "查看上下文预算"),
    "/model": ("[名称]", "查看或切换模型"),
    "/stream": ("[on/off]", "查看或切换流式输出"),
    "/read": ("<路径>", "读取文件"),
    "/attach": ("<路径>", "把文件加入聊天"),
    "/files": ("", "模糊搜索文件；Tab 多选，Enter 添加附件"),
    "/browse": ("", "逐层浏览目录并添加单个附件"),
    "/search": ("<文件> <关键词>", "搜索单文件"),
    "/grep": ("<目录> <关键词>", "递归搜索项目"),
    "/instructions": ("", "查看项目规则"),
    "/skills": ("", "查看 Skills"),
    "/skill": ("<名称>", "启用 Skill"),
    "/skill clear": ("", "停用当前会话 Skills"),
    "/skill generate": ("<名称> <用途>", "生成、审查并保存 Skill"),
    "/mcp tools": ("", "查看 MCP 工具"),
    "/mcp refresh": ("", "刷新或重连 MCP"),
}


def show_help():
    print("直接输入自然语言任务即可，命令主要用于查看和管理。")
    for name, (arguments, description) in COMMANDS.items():
        print((name + " " + arguments).ljust(38) + description)
    print("增强输入：Enter 发送，Alt+Enter 换行；候选出现时 ↑/↓ 选择、Enter 接受，再 Enter 发送。")
    print(
        "/read、/attach、/search、/grep 支持路径补全；/files 输入关键词筛选、Tab 多选，Esc 取消。"
    )
    print("没有候选时 ↑/↓ 浏览输入历史；权限确认默认拒绝，可用方向键或 y/n 选择。")
    print("空闲 Ctrl+C 或 Ctrl+D 退出；聊天生成中 Ctrl+C 取消当前生成。")
    print("工具执行中 Ctrl+C 停止当前任务并返回输入；已完成的写入不会回滚。")
