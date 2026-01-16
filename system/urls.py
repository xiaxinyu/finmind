from django.urls import path
from .views import (
    classify_transaction, insights,
    rule_categories, rule_list, rule_save, rule_delete, rule_counts,
    dashboard_coverage, dashboard_unmatched_tops, dashboard_unmatched_dimensions, dashboard_model_metrics,
    rule_recommend, rule_unmatched_details,
    rule_batch_assign
)

app_name = "system"

urlpatterns = [
    path("classify", classify_transaction),
    path("insights", insights),
    path("rule/categories", rule_categories),
    path("rule/list", rule_list),
    path("rule/save", rule_save),
    path("rule/delete", rule_delete),
    path("rule/counts", rule_counts),
    path("rule/recommend", rule_recommend),
    path("rule/unmatched-details", rule_unmatched_details),
    path("rule/batch-assign", rule_batch_assign),
    path("dashboard/coverage", dashboard_coverage),
    path("dashboard/unmatched-tops", dashboard_unmatched_tops),
    path("dashboard/unmatched-dimensions", dashboard_unmatched_dimensions),
    path("dashboard/model-metrics", dashboard_model_metrics),
]
