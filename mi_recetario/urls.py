from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/", include("recetas.api_urls")),
    path("cuentas/", include("django.contrib.auth.urls")),  # login, logout, etc.
    path("", include("recetas.urls")),
]
