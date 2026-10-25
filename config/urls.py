from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Authentication APIs
    path("api/auth/", include("accounts.urls")),

    # Event and booking APIs
    path("api/events/", include("events.urls")),

    # API schema and documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        TemplateView.as_view(template_name="redoc.html"),
        name="redoc",
    ),
]
