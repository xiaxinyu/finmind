from django.urls import path
from .views import classify, chat

urlpatterns = [
    path("classify", classify),
    path("chat", chat),
]
