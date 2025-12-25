from core.agents.classifier_agent import ClassifierAgent
from core.tools.qwen_api import QwenAPITool

def classify_text(description):
    agent = ClassifierAgent(tools={"qwen_api": QwenAPITool()})
    return agent.run(description or "")
