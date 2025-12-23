from django.contrib import admin
from django.urls import path, include
from engine.views import hello

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("engine.urls")),
    path("", hello),
]
