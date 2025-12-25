from django.core.management.base import BaseCommand
import os
import json
import requests
from dotenv import load_dotenv

class Command(BaseCommand):
    help = "Check DashScope API key validity"

    def handle(self, *args, **options):
        try:
            load_dotenv()
        except Exception:
            pass
        api_key = os.environ.get("DASHSCOPE_API_KEY", "") or os.environ.get("QWEN_API_KEY", "")
        if not api_key:
            try:
                from pathlib import Path
                import csv
                base = Path(__file__).resolve().parents[3]
                p = base / "resources" / "AccessKey.csv"
                with open(p, "r", encoding="utf-8") as f:
                    rows = list(csv.reader(f))
                    if len(rows) >= 2 and len(rows[1]) >= 2:
                        ak_secret = (rows[1][1] or "").strip()
                        if ak_secret:
                            api_key = ak_secret
                            print("使用 AccessKey.csv 中的 Secret 作为令牌进行检测")
            except Exception:
                pass
        if not api_key:
            print("DASHSCOPE_API_KEY 未设置")
            return
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {"model": os.environ.get("QWEN_MODEL", "qwen-max"), "input": {"messages": [{"role": "user", "content": "ping"}]}}
        try:
            r = requests.post(url, headers=headers, json=data, timeout=20)
            sc = r.status_code
            print(f"HTTP {sc}")
            if sc == 200:
                try:
                    d = r.json()
                    msg = d.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
                    print("密钥有效")
                    print(str(msg)[:200])
                except Exception:
                    print("密钥有效")
            elif sc == 401:
                print("DASHSCOPE_API_KEY 无效")
                txt = r.text or ""
                print(str(txt)[:200])
            else:
                print("调用失败")
                txt = r.text or ""
                print(str(txt)[:200])
        except Exception as e:
            print("网络错误")
            print(str(e)[:200])
