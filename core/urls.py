from django.urls import path
from .views import classify, chat

app_name = "core"

urlpatterns = [
    path("classify", classify),
    path("chat", chat),
]
