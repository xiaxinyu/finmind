from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from system.views import login_page, authentication_form, login_error_json, home_page, logout_view, favicon_ico
from system import views as system_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("system.urls")),
    path("", login_page),
    path("login", login_page),
    path("authentication/form", authentication_form),
    path("login-error.json", login_error_json),
    path("home", home_page),
    path("logout", logout_view),
    path("favicon.ico", favicon_ico),
]

# error handlers
handler404 = system_views.page_not_found
handler500 = system_views.server_error

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
