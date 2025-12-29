import os
import json
import requests
from dotenv import load_dotenv

class QwenAPITool:
    def __init__(self, api_key=None, model=None):
        try:
            load_dotenv()
        except Exception:
            pass
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY", "") or os.environ.get("QWEN_API_KEY", "")
        self.model = model or os.environ.get("QWEN_MODEL", "qwen-max")
    def call(self, prompt):
        if not self.api_key:
            try:
                print("[FinMind][LLM] skip: no api key")
            except Exception:
                pass
            return "OTHER"
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {"model": self.model, "input": {"messages": [{"role": "user", "content": prompt}]}}
        r = requests.post(url, headers=headers, json=data)
        try:
            d = r.json()
            content = None
            try:
                content = d.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content")
            except Exception:
                pass
            if not content:
                content = d.get("output", {}).get("text")
            if not content:
                content = d.get("output", {}).get("result")
            if not content:
                content = d.get("output", {}).get("message", {}).get("content")
            if not content:
                raise ValueError("empty content")
            try:
                print(f"[FinMind][LLM] status={r.status_code} model={self.model}")
                print(f"[FinMind][LLM] prompt={str(prompt)[:200]}")
                print(f"[FinMind][LLM] response={str(content)[:200]}")
            except Exception:
                pass
            return content
        except Exception:
            try:
                sc = getattr(r, "status_code", None)
                body = r.text if hasattr(r, "text") else ""
                print(f"[FinMind][LLM] error status={sc}")
                print(f"[FinMind][LLM] body={str(body)[:200]}")
            except Exception:
                pass
            return "OTHER"
