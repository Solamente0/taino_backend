from django.urls import include, path

app_name = "version"

urlpatterns = [
    path("v1/", include("apps.version.api.v1.urls", namespace="version_v1"), name="version_v1"),
    path("admin/", include("apps.version.api.admin.urls", namespace="version_admin"), name="version_admin"),
]
