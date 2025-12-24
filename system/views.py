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
    if not data.get("categoryId") or not data.get("pattern"):
        return HttpResponseBadRequest("missing fields")
    cat = ConsumeCategory.objects.filter(id=data["categoryId"]).first()
    if cat:
        data["categoryId"] = cat.code
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
    return JsonResponse({"rows": rows})
