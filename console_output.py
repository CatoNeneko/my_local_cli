"""终端输出状态：每轮响应重置，避免流式显示后重复打印最终文字。"""


class ConsoleOutput:
    def __init__(self):
        self.begin()

    def begin(self):
        self.content = ""
        self.started = False

    def write(self, text):
        if not text:
            return
        if not self.started:
            print("assistant: ", end="", flush=True)
            self.started = True
        self.content += text
        print(text, end="", flush=True)

    def end(self):
        if self.started:
            print()

    def final(self, reply):
        if not self.started or reply != self.content:
            print("assistant:", reply)
