"""轻量选择面板：上下移动，Enter 确认，Esc 取消。"""
from tool_display import safe_text


def choose(title, choices, *, input=None, output=None, yes_no=False):
    from prompt_toolkit.application import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, HSplit, Window
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.layout.dimension import Dimension
    from prompt_toolkit.data_structures import Point
    from prompt_toolkit.widgets import Label

    if not choices:
        return None
    selected = 0  # 当前高亮的候选位置；初始为第一项。
    bindings = KeyBindings()

    @bindings.add('up')
    def up(event):
        nonlocal selected
        selected = max(0, selected - 1)

    @bindings.add('down')
    def down(event):
        nonlocal selected
        selected = min(len(choices) - 1, selected + 1)

    @bindings.add('enter')
    def accept(event):
        event.app.exit(result=choices[selected][0])

    @bindings.add('escape', eager=True)
    @bindings.add('c-c')
    @bindings.add('c-d')
    def cancel(event):
        event.app.exit(result=None)

    if yes_no:
        @bindings.add('y')
        def yes(event):
            event.app.exit(result=True)

        @bindings.add('n')
        def no(event):
            event.app.exit(result=False)

    def render():
        rows = []
        for index, (_, label) in enumerate(choices):
            style = 'reverse' if index == selected else ''
            display = safe_text(label).replace('\n', '\\n').replace('\t', '\\t')
            rows.append((style, ('› ' if index == selected else '  ') + display + '\n'))
        return rows

    control = FormattedTextControl(render, focusable=True,
                                   get_cursor_position=lambda: Point(x=0, y=selected))
    body = Window(control, height=Dimension(min=1, max=12))
    container = HSplit([Label(safe_text(title)), body,
                        Label('↑/↓ 选择 · Enter 确认 · Esc 取消' + (' · y/n 快捷确认' if yes_no else ''))])
    app = Application(layout=Layout(container, focused_element=body),
                      key_bindings=bindings, full_screen=False, input=input, output=output)
    return app.run()
