from django.urls import include, path

app_name = "permissions"

urlpatterns = [
    path("admin/", include("apps.permissions.api.admin.urls", namespace="permission_admin"), name="permission_admin"),
    path("v1/", include("apps.permissions.api.v1.urls", namespace="permission_v1"), name="permission_v1"),
]
