import re
import unicodedata

def _norm_text(s):
    try:
        s = unicodedata.normalize("NFKC", s or "")
    except Exception:
        s = s or ""
    return s.strip()

def extract_keywords(text, top_k=20):
    try:
        s = _norm_text(text)
        try:
            import jieba
            import jieba.analyse
            toks = jieba.analyse.extract_tags(s, topK=top_k)
        except ImportError:
            parts = []
            for m in re.finditer(r"[\u4e00-\u9fff]{2,}", s):
                parts.append(m.group(0))
            for m in re.finditer(r"[A-Za-z0-9]{2,}", s):
                parts.append(m.group(0))
            toks = parts
        stop = set([
            "支付宝","公司","有限","有限公司","发展","科技","北京","深圳","广州","上海","网络","服务","平台","交易","消费","付款","支付","中心", 
            "特约", "扫码", "银联", "商务", "管理", "技术", "分公司", "无限", "深圳市", "跨行", "连锁", "商业", "银行", "分行", "支行", 
            "股份", "集团", "餐饮", "食品", "超市", "便利店", "百货", "商场", "实业", "企业", "通讯", "通信", "移动", "联通", "电信", 
            "缴费", "代扣", "代付", "业务", "资金", "结算", "清算", "转账", "汇款", "存取", "存款", "取款", "atm", "pos", "etc",
            "快捷", "财付通", "银联", "在线", "订单", "商品", "商户", "其它", "其他"
        ])
        cleaned = []
        for t in toks:
            t = (t or "").strip().lower()
            if len(t) < 2:
                continue
            if t in stop:
                continue
            if t.isdigit() and len(t) < 4:
                continue
            cleaned.append(t)
        seen = set()
        out = []
        for t in cleaned:
            if t in seen:
                continue
            seen.add(t)
            out.append(t)
        return out[:top_k]
    except Exception:
        return []
