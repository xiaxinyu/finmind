import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from core.services.classification_service import classify_text
from core.services.analysis_service import analyze_query

def _parse_json(request):
    if not request.body:
        return None
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None


@csrf_exempt
@require_POST
def classify(request):
    payload = _parse_json(request)
    if payload is None:
        return HttpResponseBadRequest("invalid json")
    description = payload.get("description")
    if description is None:
        return HttpResponseBadRequest("missing description")
    category = classify_text(description)
    return JsonResponse({"category": category})

@csrf_exempt
@require_POST
def chat(request):
    payload = _parse_json(request)
    if payload is None:
        return HttpResponseBadRequest("invalid json")
    query = payload.get("query")
    if query is None:
        return HttpResponseBadRequest("missing query")
    response = analyze_query(query)
    return JsonResponse({"response": response})
