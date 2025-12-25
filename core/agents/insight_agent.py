from .base_agent import BaseAgent

class InsightAgent(BaseAgent):
    def run(self, lines):
        return {"ok": True, "lines": len(lines or [])}
