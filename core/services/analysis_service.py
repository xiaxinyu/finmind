from core.agents.analysis_agent import AnalysisAgent
from core.tools.qwen_api import QwenAPITool

def analyze_query(query):
    agent = AnalysisAgent(tools={"qwen_api": QwenAPITool()})
    return agent.run(query or "")
