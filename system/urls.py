from django.urls import path
from .views import (
    classify_transaction, analyze_batch, insights,
    create_credit, list_credits, delete_credit,
    rule_categories, rule_list, rule_save, rule_delete, rule_counts
)

urlpatterns = [
    path("classify", classify_transaction),
    path("analyze", analyze_batch),
    path("insights", insights),
    path("credit/create", create_credit),
    path("credit/list", list_credits),
    path("credit/delete", delete_credit),
    path("rule/categories", rule_categories),
    path("rule/list", rule_list),
    path("rule/save", rule_save),
    path("rule/delete", rule_delete),
    path("rule/counts", rule_counts),
]
