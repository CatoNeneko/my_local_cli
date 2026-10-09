"""终端输入适配：TTY 使用补全和多行编辑，管道或 --plain 使用 input。"""
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from command_help import COMMANDS
from config import model_config
from path_input import PATH_COMMANDS, path_candidates
from tool_display import safe_text

enhanced_confirmation = ContextVar('enhanced_confirmation', default=False)


def request_confirmation(prompt):
    if enhanced_confirmation.get():
        from terminal_dialog import choose
        return choose(prompt, [(False, '拒绝（默认）'), (True, '允许本次操作')], yes_no=True) is True
    return input(safe_text(prompt) + '\n允许吗？[y/N] ').strip().lower() == 'y'


def create_completer():
    from prompt_toolkit.completion import Completer, Completion, WordCompleter

    class ProjectCompleter(Completer):
        def get_completions(self, document, complete_event):
            text = document.text_before_cursor
            command, separator, argument = text.partition(' ')
            if command not in PATH_COMMANDS or not separator:
                yield from WordCompleter(list(COMMANDS), sentence=True).get_completions(document, complete_event)
                return
            # 路径是第一个参数；完整闭合引号后不再补全关键词。
            quote = argument[:1] if argument[:1] in ('"', "'") else ''
            typed = argument[1:] if quote else argument
            if (quote and quote in typed) or (not quote and any(char.isspace() for char in typed)):
                return
            parent, _, prefix = typed.rpartition('/')
            directory = parent + '/' if '/' in typed else '.'
            candidates, _ = path_candidates(directory, prefix, directories_only=command == '/grep')
            for relative, is_directory in candidates:
                candidate = relative + ('/' if is_directory else '')
                # 含空格的文件用引号包裹；目录末尾保留开引号以便继续补全。
                delimiter = quote or ('"' if any(char.isspace() for char in candidate) else '')
                if '"' in candidate or "'" in candidate or any(ord(char) < 32 for char in candidate):
                    continue
                replacement = delimiter + candidate + (delimiter if delimiter and not is_directory else '')
                yield Completion(replacement, start_position=-len(argument),
                                 display=safe_text(candidate), display_meta='目录' if is_directory else '文件')

    return ProjectCompleter()


def create_key_bindings():
    from prompt_toolkit.key_binding import KeyBindings
    bindings = KeyBindings()

    @bindings.add("enter")
    def submit(event):
        if event.current_buffer.complete_state is not None:
            if event.current_buffer.complete_state.current_completion is None:
                event.current_buffer.go_to_completion(0)
            event.current_buffer.complete_state = None
            return
        event.current_buffer.validate_and_handle()

    @bindings.add("escape", "enter")
    def newline(event):
        event.current_buffer.insert_text("\n")

    return bindings


class TerminalInput:
    def __init__(self, plain=False):
        self.session = None
        if not plain and sys.stdin.isatty() and sys.stdout.isatty():
            from prompt_toolkit import PromptSession
            from prompt_toolkit.history import InMemoryHistory
            self.session = PromptSession(
                multiline=True, key_bindings=create_key_bindings(),
                completer=create_completer(),
                complete_while_typing=True, history=InMemoryHistory()
            )

    @contextmanager
    def confirmations(self):
        token = enhanced_confirmation.set(self.session is not None)
        try:
            yield
        finally:
            enhanced_confirmation.reset(token)

    def pick_file(self):
        import permissions
        from terminal_dialog import choose
        directory = '.'
        while True:
            candidates, truncated = path_candidates(directory)
            choices = []
            if directory != '.':
                parent = str(Path(directory).parent)
                choices.append(((parent, True), '../ 返回上一级'))
            choices.extend(((path, is_directory), ('📁 ' if is_directory else '   ') + Path(path).name)
                           for path, is_directory in candidates)
            title = '选择附件 · ' + directory
            if truncated:
                title += '（候选已限制，请用路径补全定位其他文件）'
            if not choices:
                print('没有可选择的文件')
                return None
            if self.session is not None:
                selected = choose(title, choices)
            else:
                print(title)
                for index, (_, label) in enumerate(choices, 1):
                    print(str(index) + '. ' + safe_text(label))
                answer = input('输入编号，留空取消: ').strip()
                if not answer:
                    return None
                if not answer.isdigit() or not 1 <= int(answer) <= len(choices):
                    print('无效编号')
                    continue
                selected = choices[int(answer) - 1][0]
            if selected is None:
                return None
            path, is_directory = selected
            checked = permissions.resolve_project_path(path)
            if not checked['ok']:
                print(checked['error'])
                continue
            if is_directory:
                directory = path
            else:
                return path

    def pick_files(self):
        from file_catalog import scan_files, matching_files
        from file_picker import MAX_SELECTION, pick_files
        catalog = scan_files()
        for warning in catalog['warnings']:
            print(safe_text(warning))
        notice = '（索引不完整: ' + catalog['reason'] + '）' if catalog['truncated'] else ''
        if not catalog['files']:
            print('没有可选择的文件' + notice)
            return None
        if self.session is not None:
            return pick_files(catalog['files'], notice=notice)
        filtered = catalog['files']
        while True:
            print('选择附件' + notice)
            for index, path in enumerate(filtered[:200], 1):
                print(str(index) + '. ' + safe_text(path))
            print('匹配数量:', len(filtered), '（最多显示 200 项）')
            answer = input('编号可用逗号分隔；/关键词 筛选；留空取消: ').strip()
            if not answer:
                return None
            if answer.startswith('/'):
                filtered = matching_files(catalog['files'], answer[1:])
                continue
            numbers = answer.split(',')
            if (len(numbers) <= MAX_SELECTION and all(value.strip().isdigit()
                    and 1 <= int(value.strip()) <= min(len(filtered), 200) for value in numbers)):
                return list(dict.fromkeys(filtered[int(value.strip()) - 1] for value in numbers))
            print('无效编号；最多选择 10 个文件')

    def read(self, session_name):
        label = "你[" + session_name + "]: "
        if self.session is None:
            return input(label)
        def toolbar():
            mode = "开" if model_config["stream"] else "关"
            return "会话 " + session_name + " | 模型 " + model_config["model"] + " | 流式 " + mode + " | /help 查看帮助"
        return self.session.prompt(label, bottom_toolbar=toolbar)
