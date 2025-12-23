import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from account.analyzer.ConsumptionAnalyzer import ConsumptionAnalyzer
from account.analyzer.BusinessAnalyzer import BusinessAnalyzer
from persist.models import Credit

def hello(request):
    return HttpResponse("Hello, World!")

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
def analyze_batch(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("invalid json")
    lines = payload.get("lines")
    if not isinstance(lines, list) or len(lines) == 0:
        return HttpResponseBadRequest("invalid lines")
    analyzer = BusinessAnalyzer(lines)
    result = analyzer.calculate(lines)
    return JsonResponse({"lines": result})

@csrf_exempt
def insights(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("invalid json")
    lines = payload.get("lines")
    if not isinstance(lines, list) or len(lines) == 0:
        return HttpResponseBadRequest("invalid lines")
    analyzer = BusinessAnalyzer(lines)
    processed = analyzer.calculate(lines)
    index_name = "消费类型名称"
    total = 0.0
    stats = {}
    for i, row in enumerate(processed):
        if i == analyzer.headerRowIndex:
            continue
        try:
            ctype = row[-3]
            amount = float(row[analyzer.transactionColumnIndex])
        except Exception:
            ctype = "未知"
            amount = 0.0
        stats[ctype] = stats.get(ctype, 0.0) + amount
        total += amount
    distribution = []
    for k, v in stats.items():
        p = 0.0
        if total > 0:
            p = v / total
        distribution.append({"type": k, "amount": v, "ratio": p})
    return JsonResponse({"total": total, "distribution": distribution})

@csrf_exempt
def create_credit(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("invalid json")
    required = ["source", "transaction_date", "bookkeeping_date", "card_id", "transaction_money", "balance_currency", "balance_money", "transaction_desc", "payment_type_id", "payment_type_name", "card_type_id", "card_type_name", "consumption_name", "consumption_id", "consume_name", "consume_id", "keyword", "demoarea"]
    for k in required:
        if payload.get(k) is None:
            return HttpResponseBadRequest("missing fields")
    obj = Credit.objects.create(
        source=payload["source"],
        transaction_date=payload["transaction_date"],
        bookkeeping_date=payload["bookkeeping_date"],
        card_id=payload["card_id"],
        transaction_money=payload["transaction_money"],
        balance_currency=payload["balance_currency"],
        balance_money=payload["balance_money"],
        transaction_desc=payload["transaction_desc"],
        payment_type_id=payload["payment_type_id"],
        payment_type_name=payload["payment_type_name"],
        card_type_id=payload["card_type_id"],
        card_type_name=payload.get("card_type_name", "Credit Card"),
        consumption_name=payload["consumption_name"],
        consumption_id=payload["consumption_id"],
        consume_name=payload["consume_name"],
        consume_id=payload["consume_id"],
        keyword=payload["keyword"],
        demoarea=payload["demoarea"],
        recordid=payload.get("recordid", "no record id"),
        version=payload.get("version", 0),
        createuser=payload.get("createuser", "system"),
        updateuser=payload.get("updateuser", "system"),
    )
    return JsonResponse({"id": obj.id})

def _row(obj):
    return {
        "id": obj.id,
        "source": obj.source,
        "transaction_date": obj.transaction_date,
        "bookkeeping_date": obj.bookkeeping_date,
        "card_id": obj.card_id,
        "transaction_money": float(obj.transaction_money),
        "balance_currency": obj.balance_currency,
        "balance_money": float(obj.balance_money),
        "transaction_desc": obj.transaction_desc,
        "payment_type_id": obj.payment_type_id,
        "payment_type_name": obj.payment_type_name,
        "card_type_id": obj.card_type_id,
        "card_type_name": obj.card_type_name,
        "deleted": obj.deleted,
        "consumption_name": obj.consumption_name,
        "consumption_id": obj.consumption_id,
        "consume_name": obj.consume_name,
        "consume_id": obj.consume_id,
        "keyword": obj.keyword,
        "demoarea": obj.demoarea,
        "recordid": obj.recordid,
        "version": obj.version,
        "createuser": obj.createuser,
        "createtime": obj.createtime,
        "updateuser": obj.updateuser,
        "updatetime": obj.updatetime,
    }

@csrf_exempt
def list_credits(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        return HttpResponseBadRequest("invalid json")
    qs = Credit.objects.filter(deleted=0)
    start = payload.get("start")
    end = payload.get("end")
    if start:
        qs = qs.filter(transaction_date__gte=start)
    if end:
        qs = qs.filter(transaction_date__lte=end)
    data = [_row(x) for x in qs.order_by("-transaction_date")[:500]]
    return JsonResponse({"rows": data})

@csrf_exempt
def delete_credit(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("invalid json")
    cid = payload.get("id")
    if not cid:
        return HttpResponseBadRequest("missing id")
    try:
        obj = Credit.objects.get(id=cid)
    except Credit.DoesNotExist:
        return HttpResponseBadRequest("not found")
    obj.deleted = 1
    obj.save(update_fields=["deleted"])
    return JsonResponse({"ok": True})
