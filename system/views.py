from account.analyzer.BusinessAnalyzer import BusinessAnalyzer
from persist.models import Credit, AppUser, ConsumeCategory, ConsumeRule, ConsumeRuleTag, Transaction
from django.db import models
from django.conf import settings
import unicodedata
import re
import logging
import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.hashers import check_password
from account.analyzer.ConsumptionAnalyzer import ConsumptionAnalyzer

logger = logging.getLogger("finmind.auth")

def hello(request):
    return HttpResponse("Hello, World!")

def login_page(request):
    return render(request, "system/login.html")

@csrf_exempt
def authentication_form(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    username = request.POST.get("username")
    password = request.POST.get("password")
    u = AppUser.objects.filter(username=username, enabled=1).first()
    ok = False
    if u:
        stored = u.password or ""
        try:
            if stored.startswith("$2"):  # bcrypt from external system
                import bcrypt
                ok = bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
            else:
                ok = check_password(password, stored) or (stored == password)
        except Exception:
            ok = (stored == password)
    if not ok:
        logger.warning("login_failed user=%s ip=%s", username, request.META.get("REMOTE_ADDR"))
        request.session["login_error"] = "Invalid username or password"
        return redirect("/login")
    logger.info("login_success user=%s id=%s ip=%s", u.username, u.id, request.META.get("REMOTE_ADDR"))
    request.session["app_user_id"] = u.id
    request.session["app_username"] = u.username
    request.session["app_display_name"] = u.display_name or u.username
    request.session.pop("login_error", None)
    return redirect("/home")

def login_error_json(request):
    msg = request.session.get("login_error", "")
    return JsonResponse({"msg": msg or ""})

def home_page(request):
    if not request.session.get("app_user_id"):
        logger.info("home_redirect_to_login ip=%s", request.META.get("REMOTE_ADDR"))
        return redirect("/login")
    logger.info("home_access user=%s id=%s ip=%s", request.session.get("app_username"), request.session.get("app_user_id"), request.META.get("REMOTE_ADDR"))
    return render(request, "system/index.html")

def logout_view(request):
    logout(request)
    for k in ["app_user_id", "app_username", "app_display_name"]:
        request.session.pop(k, None)
    logger.info("logout user=%s ip=%s", request.session.get("app_username"), request.META.get("REMOTE_ADDR"))
    return redirect("/login")

def page_not_found(request, exception=None):
    return render(request, "errors/404.html", status=404)

def server_error(request):
    return render(request, "errors/500.html", status=500)

def app_error(request):
    return render(request, "errors/error.html")

def favicon_ico(request):
    return redirect(f"{settings.STATIC_URL}system/favicon.svg")

@csrf_exempt
def classify_transaction(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("invalid json")
    description = payload.get("description")
    money = payload.get("money")
    if description is None or money is None:
        return HttpResponseBadRequest("missing fields")
    analyzer = ConsumptionAnalyzer()
    ct = analyzer.getConsumptionType(description, money)
    return JsonResponse({"consumption": ct})

@csrf_exempt
def insights(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("invalid json")
    lines = payload.get("lines")
    if not lines or not isinstance(lines, list):
        return HttpResponseBadRequest("invalid lines")
    analyzer = BusinessAnalyzer(lines)
    result = analyzer.calculate(lines)
    
    # Calculate distribution
    # Just a mock for now or use result if applicable
    # The frontend expects { distribution: [{type, ratio}] }
    # Let's simple aggregate by consumption type (index 10)
    dist = {}
    total = 0
    for row in result:
        if len(row) > 10:
            ctype = row[10]
            try:
                amt = float(row[3])
                dist[ctype] = dist.get(ctype, 0) + amt
                total += amt
            except:
                pass
    
    out = []
    if total > 0:
        for k, v in dist.items():
            out.append({"type": k, "ratio": v/total})
    out.sort(key=lambda x: x["ratio"], reverse=True)
    
    return JsonResponse({"distribution": out})

@csrf_exempt
def rule_categories(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        return HttpResponseBadRequest("invalid json")
    
    txn_types = payload.get("txn_types") # 'all', 'expense', 'income'
    qs = ConsumeCategory.objects.filter(deleted=0)
    if txn_types and txn_types != 'all':
        # Filter by txn_types containing the type (comma separated in DB?)
        # DB field `txn_types` char(256) default 'expense'.
        # Assume it stores 'expense', 'income' or both.
        # We use icontains for simplicity.
        qs = qs.filter(txn_types__icontains=txn_types)
        
    rows = [_cat_row(x) for x in qs]
    return JsonResponse({"rows": rows})

def _cat_row(obj):
    return {
        "id": obj.id,
        "parentId": obj.parentId,
        "code": obj.code,
        "name": obj.name,
        "level": obj.level,
        "txn_types": obj.txn_types,
        "sortNo": obj.sortNo,
    }

def _rule_row(obj):
    return {
        "id": obj.id,
        "categoryId": obj.categoryId,
        "pattern": obj.pattern,
        "patternType": obj.patternType,
        "priority": obj.priority,
        "active": obj.active,
        "bankCode": obj.bankCode,
        "cardTypeCode": obj.cardTypeCode,
        "remark": obj.remark,
        "minAmount": float(obj.minAmount) if obj.minAmount is not None else None,
        "maxAmount": float(obj.maxAmount) if obj.maxAmount is not None else None,
        "startDate": obj.startDate.isoformat() if obj.startDate else None,
        "endDate": obj.endDate.isoformat() if obj.endDate else None,
    }

@csrf_exempt
def rule_list(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        return HttpResponseBadRequest("invalid json")
    cid = payload.get("categoryId")
    if not cid:
        logger.info("rule_list_empty_no_category")
        return JsonResponse({"rows": []})
    cat = ConsumeCategory.objects.filter(id=cid).first() or ConsumeCategory.objects.filter(code=cid).first()
    keys = []
    if cat:
        if cat.id: keys.append(cat.id)
        if cat.code: keys.append(cat.code)
        if cat.parentId:
            keys.append(cat.parentId)
            p = ConsumeCategory.objects.filter(id=cat.parentId).first() or ConsumeCategory.objects.filter(code=cat.parentId).first()
            if p and p.code:
                keys.append(p.code)
    else:
        keys.append(cid)
    keys = list({k for k in keys if k})
    qs = ConsumeRule.objects.filter(categoryId__in=keys).order_by("-priority", "pattern")
    try:
        sql = str(qs.query)
        logger.info("sql_rule_list keys=%s sql=%s", ",".join(keys), sql)
        print(f"sql_rule_list keys={','.join(keys)} sql={sql}")
    except Exception:
        pass
    rows = list(qs)
    ids = [x.id for x in rows]
    tags_map = {}
    if ids:
        for t in ConsumeRuleTag.objects.filter(rule_id__in=ids).values("rule_id", "tag"):
            tags_map.setdefault(t["rule_id"], []).append(t["tag"])
    data = []
    for x in rows:
        r = _rule_row(x)
        r["tags"] = tags_map.get(x.id, [])
        data.append(r)
    return JsonResponse({"rows": data})

@csrf_exempt
def rule_counts(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        return HttpResponseBadRequest("invalid json")
    codes = payload.get("codes") or []
    if not isinstance(codes, list):
        return HttpResponseBadRequest("invalid codes")
    counts = {}
    if codes:
        qs = ConsumeRule.objects.filter(categoryId__in=codes)
        agg = qs.values("categoryId").annotate(cnt=models.Count("id"))
        try:
            sql = str(agg.query)
            logger.info("sql_rule_counts codes=%s sql=%s", ",".join(codes[:10]), sql)
            print(f"sql_rule_counts codes={','.join(codes[:10])} sql={sql}")
        except Exception:
            pass
        for c in agg:
            counts[c["categoryId"]] = c["cnt"]
    return JsonResponse({"counts": counts})

@csrf_exempt
def rule_save(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("invalid json")
    rid = payload.get("id")
    fields = ["categoryId","pattern","patternType","priority","active","bankCode","cardTypeCode","remark","minAmount","maxAmount","startDate","endDate"]
    data = {k: payload.get(k) for k in fields}
    tags_payload = payload.get("tags")
    patterns = payload.get("patterns")
    if not data.get("categoryId") and not payload.get("categoryId"):
        return HttpResponseBadRequest("missing categoryId")
    cat = ConsumeCategory.objects.filter(id=data["categoryId"]).first()
    if cat:
        data["categoryId"] = cat.code
    # Batch create if patterns list provided and no rid
    if (not rid) and isinstance(patterns, list):
        created_ids = []
        for pat in patterns:
            p = (pat or "").strip()
            if not p:
                continue
            row = dict(data)
            row["pattern"] = p
            if not row.get("patternType"):
                row["patternType"] = "contains"
            if row.get("priority") is None:
                row["priority"] = 100
            import uuid
            obj = ConsumeRule.objects.create(id=str(uuid.uuid4()), **row)
            created_ids.append(obj.id)
            if tags_payload is not None:
                tags = tags_payload if isinstance(tags_payload, list) else str(tags_payload or "").split(",")
                tags = [t.strip() for t in tags if t and t.strip()]
                for t in tags:
                    ConsumeRuleTag.objects.create(rule_id=obj.id, tag=t)
        return JsonResponse({"ids": created_ids, "created": True})
    if rid:
        try:
            obj = ConsumeRule.objects.get(id=rid)
        except ConsumeRule.DoesNotExist:
            return HttpResponseBadRequest("not found")
        for k, v in data.items():
            setattr(obj, k, v)
        obj.save()
        if tags_payload is not None:
            ConsumeRuleTag.objects.filter(rule_id=obj.id).delete()
            tags = tags_payload if isinstance(tags_payload, list) else str(tags_payload or "").split(",")
            tags = [t.strip() for t in tags if t and t.strip()]
            for t in tags:
                ConsumeRuleTag.objects.create(rule_id=obj.id, tag=t)
        return JsonResponse({"id": obj.id, "updated": True})
    else:
        if not data.get("pattern"):
            return HttpResponseBadRequest("missing pattern")
        import uuid
        obj = ConsumeRule.objects.create(id=str(uuid.uuid4()), **data)
        if tags_payload is not None:
            tags = tags_payload if isinstance(tags_payload, list) else str(tags_payload or "").split(",")
            tags = [t.strip() for t in tags if t and t.strip()]
            for t in tags:
                ConsumeRuleTag.objects.create(rule_id=obj.id, tag=t)
        return JsonResponse({"id": obj.id, "created": True})

@csrf_exempt
def rule_delete(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("invalid json")
    rid = payload.get("id")
    if not rid:
        return HttpResponseBadRequest("missing id")
    try:
        obj = ConsumeRule.objects.get(id=rid)
    except ConsumeRule.DoesNotExist:
        return HttpResponseBadRequest("not found")
    obj.delete()
    return JsonResponse({"ok": True})

@csrf_exempt
def rule_recommend(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("invalid json")
    desc = (payload.get("desc") or payload.get("description") or "").strip()
    if not desc:
        return HttpResponseBadRequest("missing desc")
    try:
        from core.services.classification_service import classify_text
        cid = classify_text(desc) or ""
    except Exception:
        cid = ""
    # map LLM output to category (code/id/name contains)
    cat = None
    try:
        if cid and cid != "OTHER":
            cat = ConsumeCategory.objects.filter(code=cid).first() or ConsumeCategory.objects.filter(id=cid).first()
            if not cat:
                cat = ConsumeCategory.objects.filter(name__icontains=cid).first()
    except Exception:
        cat = None
    # build candidates from rule-based matching
    def _norm_text(s):
        try:
            import unicodedata, re as _re
            s = unicodedata.normalize("NFKC", s or "")
        except Exception:
            s = s or ""
        s = s.strip().lower()
        import re
        s = re.sub(r"\s+", " ", s)
        return s
    def _match_text(rule, text):
        pt = rule.patternType or "contains"
        pat = _norm_text(rule.pattern or "")
        if not pat:
            return False
        t = _norm_text(text or "")
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
                import re
                return re.search(rule.pattern or "", text or "") is not None
            except Exception:
                return False
        return False
    rules = list(ConsumeRule.objects.filter(active=1).only("categoryId","pattern","patternType","priority"))
    score_map = {}
    count_map = {}
    for r in rules:
        try:
            ok = _match_text(r, desc)
        except Exception:
            ok = False
        if ok:
            cid_key = r.categoryId or ""
            if not cid_key:
                continue
            base = int(r.priority or 100)
            bonus = 60
            pt = (r.patternType or "contains").lower()
            if pt == "equals":
                bonus = 100
            elif pt == "regex":
                bonus = 90
            elif pt in ("startswith","endswith"):
                bonus = 80
            score_map[cid_key] = score_map.get(cid_key, 0) + base + bonus
            count_map[cid_key] = count_map.get(cid_key, 0) + 1
    # include LLM candidate
    llm_key = None
    if cat and (cat.code or cat.id):
        llm_key = cat.code or cat.id
        score_map[llm_key] = score_map.get(llm_key, 0) + 120  # boost
        count_map[llm_key] = count_map.get(llm_key, 0)
    # remove "Other" codes
    others = set(list(ConsumeCategory.objects.filter(name__icontains="其他").values_list('code', flat=True)) + list(ConsumeCategory.objects.filter(name__icontains="Other").values_list('code', flat=True)))
    for k in list(score_map.keys()):
        if k in others:
            score_map.pop(k, None)
            count_map.pop(k, None)
    # build candidates list
    keys = sorted(score_map.keys(), key=lambda k: score_map.get(k, 0), reverse=True)
    keys = keys[:5]
    candidates = []
    for k in keys:
        cc = ConsumeCategory.objects.filter(code=k).first() or ConsumeCategory.objects.filter(id=k).first()
        if not cc:
            continue
        candidates.append({
            "categoryId": cc.code or cc.id,
            "categoryName": cc.name or (cc.code or ""),
            "score": int(score_map.get(k, 0)),
            "matches": int(count_map.get(k, 0)),
            "source": "llm" if (llm_key and k == llm_key) else "rule"
        })
    # recommendation payload using tokenizer service
    from core.services.tokenizer import extract_keywords
    kw = extract_keywords(desc, top_k=12)
    chosen_pattern = kw[0] if kw else desc
    chosen_tags = kw if kw else [desc]
    if ("万家" in kw) and ("华润" in kw):
        chosen_pattern = "万家"
        chosen_tags = ["华润"]
    rec = {
        "categoryId": (cat.code if cat and cat.code else (cat.id if cat else "")) or "",
        "categoryName": cat.name if cat else "",
        "pattern": chosen_pattern,
        "patternType": "contains",
        "priority": 80,
        "tags": chosen_tags
    }
    return JsonResponse({"recommendation": rec, "candidates": candidates})

def _norm(s):
    try:
        s = unicodedata.normalize("NFKC", s or "")
    except Exception:
        s = s or ""
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

def _amount_of(txn):
    try:
        vals = []
        if txn.income_money is not None:
            vals.append(float(txn.income_money))
        if txn.balance_money is not None:
            vals.append(float(txn.balance_money))
        vals = [abs(v) for v in vals if not (v is None)]
        if not vals:
            return None
        return max(vals)
    except Exception:
        return None

def _matches(rule, txn, tags=None):
    desc = _norm(txn.transaction_desc or "")
    opp = _norm(getattr(txn, "opponent_name", "") or "") + " " + _norm(getattr(txn, "opponent_account", "") or "")
    extra = " ".join([
        _norm(getattr(txn, "consume_name", "") or ""),
        _norm(getattr(txn, "consume_code", "") or ""),
        _norm(getattr(txn, "card_type_name", "") or ""),
        _norm(getattr(txn, "bank_card_name", "") or "")
    ]).strip()
    text = " ".join([desc, opp, extra]).strip()
    pt = rule.patternType or "contains"
    pat = rule.pattern or ""
    
    match = False
    if pt == "contains":
        if pat and _norm(pat) in text: match = True
    elif pt == "equals":
        if pat and _norm(pat) == desc: match = True
    elif pt == "startsWith":
        if pat and desc.startswith(_norm(pat)): match = True
    elif pt == "endsWith":
        if pat and desc.endswith(_norm(pat)): match = True
    elif pt == "regex":
        try:
            if pat and re.search(pat, text): match = True
        except:
            pass
    if not match and tags:
        try:
            for t in tags:
                tt = _norm(str(t or ""))
                if tt and tt in text:
                    match = True
                    break
        except Exception:
            pass
    
    if not match: return False

    has_amount_rule = (rule.minAmount is not None) or (rule.maxAmount is not None)
    if has_amount_rule:
        amt = _amount_of(txn)
        
        if amt is not None:
            if rule.minAmount is not None and amt < float(rule.minAmount): return False
            if rule.maxAmount is not None and amt > float(rule.maxAmount): return False
        # If amount is unavailable, skip amount constraints to avoid false negatives
        
    if rule.startDate or rule.endDate:
        tdate = txn.transaction_date 
        if tdate:
            d = tdate.date()
            if rule.startDate and d < rule.startDate: return False
            if rule.endDate and d > rule.endDate: return False
            
    return True

@csrf_exempt
def dashboard_coverage(request):
    rules = list(ConsumeRule.objects.filter(active=1).order_by('-priority', 'pattern'))
    txns = Transaction.objects.exclude(deleted=1).only('transaction_desc', 'income_money', 'balance_money', 'transaction_date')
    ids = [x.id for x in rules]
    tags_map = {}
    if ids:
        for t in ConsumeRuleTag.objects.filter(rule_id__in=ids).values("rule_id", "tag"):
            tags_map.setdefault(t["rule_id"], []).append(t["tag"])
    
    others = ConsumeCategory.objects.filter(name__icontains="其他").values_list('code', flat=True)
    others_en = ConsumeCategory.objects.filter(name__icontains="Other").values_list('code', flat=True)
    other_codes = set(list(others) + list(others_en))
    
    txn_list = list(txns)
    total = len(txn_list)
    
    if total == 0:
         return JsonResponse({"rate": 0, "total": 0, "covered": 0})

    covered = 0
    for t in txn_list:
        matched_cat = None
        for r in rules:
            if _matches(r, t, tags_map.get(r.id, [])):
                matched_cat = r.categoryId
                break
        
        if matched_cat:
            if matched_cat not in other_codes:
                covered += 1
            
    rate = (covered / total) * 100 if total > 0 else 0
    return JsonResponse({"rate": round(rate, 1), "total": total, "covered": covered})

@csrf_exempt
def dashboard_unmatched_tops(request):
    import time
    t0 = time.time()
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        payload = {}
    cid = payload.get("categoryId")
    base_qs = ConsumeRule.objects.filter(active=1)
    if cid:
        try:
            base_qs = base_qs.filter(categoryId=cid)
        except Exception:
            pass
    rules = list(base_qs.order_by('-priority', 'pattern'))
    txns = Transaction.objects.exclude(deleted=1).only('transaction_desc', 'income_money', 'balance_money', 'transaction_date', 'bank_card_name', 'card_type_name')
    sd = payload.get("startDate")
    ed = payload.get("endDate")
    bank = payload.get("bank")
    card = payload.get("cardType")
    if sd:
        try:
            from datetime import datetime
            sdt = datetime.fromisoformat(sd)
            txns = txns.filter(transaction_date__gte=sdt)
        except Exception:
            pass
    if ed:
        try:
            from datetime import datetime, timedelta
            edt = datetime.fromisoformat(ed) + timedelta(days=1)
            txns = txns.filter(transaction_date__lt=edt)
        except Exception:
            pass
    if bank:
        txns = txns.filter(bank_card_name__icontains=bank)
    if card:
        txns = txns.filter(card_type_name__icontains=card)
    ids = [x.id for x in rules]
    tags_map = {}
    if ids:
        for t in ConsumeRuleTag.objects.filter(rule_id__in=ids).values("rule_id", "tag"):
            tags_map.setdefault(t["rule_id"], []).append(t["tag"])
    others = ConsumeCategory.objects.filter(name__icontains="其他").values_list('code', flat=True)
    others_en = ConsumeCategory.objects.filter(name__icontains="Other").values_list('code', flat=True)
    other_codes = set(list(others) + list(others_en))
    txn_list = list(txns)
    freq = {}
    samples = {}
    for t in txn_list:
        matched_cat = None
        for r in rules:
            if _matches(r, t, tags_map.get(r.id, [])):
                matched_cat = r.categoryId
                break
        if (not matched_cat) or (matched_cat in other_codes):
            key = _norm(t.transaction_desc or "")
            if not key:
                key = "(empty)"
            freq[key] = freq.get(key, 0) + 1
            if key not in samples:
                samples[key] = t.transaction_desc or ""
    tops = sorted(freq.items(), key=lambda kv: kv[1], reverse=True)
    tops = tops[:50]
    rows = [{"desc": samples[k], "count": v} for k, v in tops]
    total = len(txn_list)
    unmatched = sum(freq.values())
    elapsed_ms = int((time.time() - t0) * 1000)
    return JsonResponse({"rows": rows, "total": total, "unmatched": unmatched, "elapsedMs": elapsed_ms})

@csrf_exempt
def dashboard_unmatched_dimensions(request):
    qs = Transaction.objects.exclude(deleted=1).only('bank_card_name', 'card_type_name', 'transaction_date')
    try:
        banks = sorted(list({(x.bank_card_name or "").strip() for x in qs if (x.bank_card_name or "").strip()}))
        cards = sorted(list({(x.card_type_name or "").strip() for x in qs if (x.card_type_name or "").strip()}))
        dates = [x.transaction_date for x in qs if x.transaction_date]
    except Exception:
        banks = []
        cards = []
        dates = []
    date_min = None
    date_max = None
    try:
        if dates:
            ds = sorted(dates)
            date_min = ds[0].date().isoformat()
            date_max = ds[-1].date().isoformat()
    except Exception:
        pass
    return JsonResponse({"banks": banks, "cardTypes": cards, "dateMin": date_min, "dateMax": date_max})

@csrf_exempt
def rule_unmatched_details(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        payload = {}
        
    target_desc = payload.get("description")
    if not target_desc:
        return JsonResponse({"rows": []})
    target_key = _norm(target_desc)
    
    # Common filtering logic
    cid = payload.get("categoryId")
    base_qs = ConsumeRule.objects.filter(active=1)
    if cid:
        try:
            base_qs = base_qs.filter(categoryId=cid)
        except Exception:
            pass
    rules = list(base_qs.order_by('-priority', 'pattern'))
    
    # Need more fields for details
    txns = Transaction.objects.exclude(deleted=1)
    
    sd = payload.get("startDate")
    ed = payload.get("endDate")
    bank = payload.get("bank")
    card = payload.get("cardType")
    
    if sd:
        try:
            from datetime import datetime
            sdt = datetime.fromisoformat(sd)
            txns = txns.filter(transaction_date__gte=sdt)
        except Exception:
            pass
    if ed:
        try:
            from datetime import datetime, timedelta
            edt = datetime.fromisoformat(ed) + timedelta(days=1)
            txns = txns.filter(transaction_date__lt=edt)
        except Exception:
            pass
    if bank:
        txns = txns.filter(bank_card_name__icontains=bank)
    if card:
        txns = txns.filter(card_type_name__icontains=card)
        
    ids = [x.id for x in rules]
    tags_map = {}
    if ids:
        for t in ConsumeRuleTag.objects.filter(rule_id__in=ids).values("rule_id", "tag"):
            tags_map.setdefault(t["rule_id"], []).append(t["tag"])
            
    others = ConsumeCategory.objects.filter(name__icontains="其他").values_list('code', flat=True)
    others_en = ConsumeCategory.objects.filter(name__icontains="Other").values_list('code', flat=True)
    other_codes = set(list(others) + list(others_en))
    
    rows = []
    # We iterate over the queryset directly to avoid loading all fields into memory if possible, 
    # but we need model instances for _matches.
    # To optimize, we first filter by description in memory (since _norm is not db-level)
    # Ideally we would do a db-level contains query first, but _norm removes spaces etc.
    # Let's stick to list(txns) as in previous method for consistency.
    txn_list = list(txns)
    
    for t in txn_list:
        # 1. Description check
        if _norm(t.transaction_desc or "") != target_key:
            continue
            
        # 2. Rule check (verify it is unmatched)
        matched_cat = None
        for r in rules:
            if _matches(r, t, tags_map.get(r.id, [])):
                matched_cat = r.categoryId
                break
                
        if (not matched_cat) or (matched_cat in other_codes):
            rows.append({
                "id": t.id,
                "cardName": t.bank_card_name,
                "postingDate": t.transaction_date,
                "txnDate": t.transaction_time, 
                "desc": t.transaction_desc,
                "currency": t.balance_currency,
                "amount": t.income_money, # We pass raw amount, frontend handles display
                "balance": t.account_balance,
                "category": t.consume_name,
                "remarks": t.demoarea
            })
            
    # Sort by date desc
    rows.sort(key=lambda x: x["postingDate"] if x["postingDate"] else "", reverse=True)
    
    return JsonResponse({"rows": rows})

@csrf_exempt
def rule_batch_assign(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        return HttpResponseBadRequest("invalid json")
    
    cat_id = payload.get("categoryId")
    if not cat_id:
        return HttpResponseBadRequest("missing categoryId")
    
    # Verify category
    cat = ConsumeCategory.objects.filter(id=cat_id).first()
    if not cat:
        cat = ConsumeCategory.objects.filter(code=cat_id).first()
    if not cat:
        return HttpResponseBadRequest("invalid category")
        
    target_code = cat.code if cat.code else cat.id
    target_name = cat.name
    
    txn_ids = payload.get("transactionIds")
    desc_str = payload.get("description")
    
    # 1. Update Transactions
    updated_count = 0
    if txn_ids and isinstance(txn_ids, list) and len(txn_ids) > 0:
        qs = Transaction.objects.filter(id__in=txn_ids)
        # Update db fields
        updated_count = qs.update(
            consume_id=target_code,
            consume_code=target_code,
            consume_name=target_name
        )
    
    # 2. Create/Update Rule (to ensure persistence)
    rule_created = False
    if desc_str:
        norm_desc = (desc_str or "").strip()
        if norm_desc:
            # Check if exact rule exists
            exist = ConsumeRule.objects.filter(pattern=norm_desc, patternType="equals").first()
            if exist:
                if exist.categoryId != target_code:
                    exist.categoryId = target_code
                    exist.active = 1
                    exist.save()
                    rule_created = True
            else:
                import uuid
                ConsumeRule.objects.create(
                    id=str(uuid.uuid4()),
                    categoryId=target_code,
                    pattern=norm_desc,
                    patternType="equals",
                    priority=100,
                    active=1
                )
                rule_created = True
                
    return JsonResponse({"updated": updated_count, "ruleCreated": rule_created})
