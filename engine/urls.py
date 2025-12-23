from django.urls import path
from .views import classify_transaction, analyze_batch, insights, create_credit, list_credits, delete_credit

urlpatterns = [
    path("classify", classify_transaction),
    path("analyze", analyze_batch),
    path("insights", insights),
    path("credit/create", create_credit),
    path("credit/list", list_credits),
    path("credit/delete", delete_credit),
]
