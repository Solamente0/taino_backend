from django.urls import include, path

app_name = "analyzer"

urlpatterns = [
    path("v1/", include("apps.analyzer.api.v1.urls", namespace="analyzer_v1"), name="analyzer_v1"),
    path("admin/", include("apps.analyzer.api.admin.urls", namespace="analyzer_admin"), name="analyzer_admin"),
]
