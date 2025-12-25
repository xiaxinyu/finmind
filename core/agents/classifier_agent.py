from .base_agent import BaseAgent
from persist.models import ConsumeRule
import re
import unicodedata

def _norm(s):
    try:
        s = unicodedata.normalize("NFKC", s or "")
    except Exception:
        s = s or ""
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

def _match(rule, text):
    pt = rule.patternType or "contains"
    pat = _norm(rule.pattern or "")
    if not pat:
        return False
    t = _norm(text or "")
    if pt == "contains":
        return pat in t
    if pt == "equals":
        return pat == t
    if pt == "startsWith":
        return t.startswith(pat)
    if pt == "endsWith":
        return t.endswith(pat)
    if pt == "regex":
        try:
            return re.search(rule.pattern or "", text or "") is not None
        except Exception:
            return False
    return False

class ClassifierAgent(BaseAgent):
    def run(self, transaction_desc):
        text = transaction_desc or ""
        rules = list(ConsumeRule.objects.filter(active=1).order_by("-priority", "pattern"))
        for r in rules:
            if _match(r, text):
                return r.categoryId
        q = self.tools.get("qwen_api")
        if q:
            try:
                return q.call(f"分类以下交易：{text}")
            except Exception:
                pass
        return "OTHER"
