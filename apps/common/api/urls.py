from django.urls import include, path

app_name = "common"

urlpatterns = [
    path("v1/", include("apps.common.api.v1.urls", namespace="common_v1"), name="common_v1"),
    path("admin/", include("apps.common.api.admin.urls", namespace="common_admin"), name="common_admin"),
]
