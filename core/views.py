import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from core.services.classification_service import classify_text
from core.services.analysis_service import analyze_query

@csrf_exempt
def classify(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("invalid json")
    description = payload.get("description")
    if description is None:
        return HttpResponseBadRequest("missing fields")
    category = classify_text(description)
    return JsonResponse({"category": category})

@csrf_exempt
def chat(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("invalid json")
    query = payload.get("query")
    if query is None:
        return HttpResponseBadRequest("missing fields")
    response = analyze_query(query)
    return JsonResponse({"response": response})
