"""可筛选、多选的附件面板；选中状态跨筛选保留。"""
from file_catalog import matching_files
from tool_display import safe_text

MAX_SELECTION = 10


def pick_files(paths, *, notice='', input=None, output=None):
    from prompt_toolkit.application import Application
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.data_structures import Point
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, HSplit, VSplit, Window
    from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
    from prompt_toolkit.layout.dimension import Dimension
    from prompt_toolkit.widgets import Label

    selected = 0
    marked = set()
    filtered = matching_files(paths, '')
    status = ''
    bindings = KeyBindings()

    def refresh(buffer):
        nonlocal filtered, selected, status
        filtered = matching_files(paths, buffer.text)
        selected = 0
        status = ''

    query = Buffer(on_text_changed=refresh)

    @bindings.add('up')
    def up(event):
        nonlocal selected
        selected = max(0, selected - 1)

    @bindings.add('down')
    def down(event):
        nonlocal selected
        selected = min(max(0, len(filtered) - 1), selected + 1)

    @bindings.add('pageup')
    def page_up(event):
        nonlocal selected
        selected = max(0, selected - 10)

    @bindings.add('pagedown')
    def page_down(event):
        nonlocal selected
        selected = min(max(0, len(filtered) - 1), selected + 10)

    @bindings.add('tab')
    def toggle(event):
        nonlocal status
        if filtered:
            path = filtered[selected]
            if path in marked:
                marked.remove(path)
            elif len(marked) < MAX_SELECTION:
                marked.add(path)
            else:
                status = '最多选择 10 个文件'

    @bindings.add('enter')
    def accept(event):
        # 已勾选时提交整个集合；否则添加当前高亮项。
        result = sorted(marked) if marked else [filtered[selected]] if filtered else []
        event.app.exit(result=result)

    @bindings.add('escape', eager=True)
    @bindings.add('c-c')
    @bindings.add('c-d')
    def cancel(event):
        event.app.exit(result=None)

    def render():
        if not filtered:
            return [('ansiyellow', '没有匹配文件；修改关键词或 Esc 取消')]
        return [
            ('reverse' if index == selected else '',
             ('› ' if index == selected else '  ') + ('[x] ' if path in marked else '[ ] ')
             + safe_text(path).replace('\n', '\\n').replace('\t', '\\t') + '\n')
            for index, path in enumerate(filtered)
        ]

    body = Window(FormattedTextControl(render, get_cursor_position=lambda: Point(x=0, y=selected)),
                  height=Dimension(min=1, max=12))
    search = Window(BufferControl(buffer=query), height=1)
    footer = Label(lambda: '匹配 ' + str(len(filtered)) + ' / 已选 ' + str(len(marked))
                   + ' · ↑/↓ 移动 · Tab 勾选 · Enter 添加 · Esc 取消\n' + status)
    layout = HSplit([Label('选择附件 · 输入文件名或路径片段（支持不连续字符）' + notice),
                     VSplit([Label('筛选: ', width=6), search]), body, footer])
    app = Application(layout=Layout(layout, focused_element=search), key_bindings=bindings,
                      full_screen=False, input=input, output=output)
    return app.run()
