class BaseAgent:
    def __init__(self, tools=None):
        self.tools = tools or {}
    def run(self, task):
        raise NotImplementedError
