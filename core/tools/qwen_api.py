import os
import json
import requests
import csv
from pathlib import Path

class QwenAPITool:
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY", "") or os.environ.get("QWEN_API_KEY", "")
        if not self.api_key:
            try:
                base = Path(__file__).resolve().parents[2]
                p = base / "resources" / "AccessKey.csv"
                with open(p, "r", encoding="utf-8") as f:
                    rows = list(csv.reader(f))
                    if len(rows) >= 2 and len(rows[1]) >= 2:
                        ak_id = (rows[1][0] or "").strip()
                        ak_secret = (rows[1][1] or "").strip()
                        if ak_secret:
                            self.api_key = ak_secret
                            try:
                                print("[FinMind][LLM] fallback using AccessKey.csv secret as token")
                            except Exception:
                                pass
            except Exception:
                pass
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
            content = d["output"]["choices"][0]["message"]["content"]
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
