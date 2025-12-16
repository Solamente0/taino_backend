from django.urls import include, path

app_name = "authentication"

urlpatterns = [
    path("v1/", include("apps.authentication.api.v1.urls", namespace="authentication_v1"), name="authentication_v1"),
    path("admin/", include("apps.authentication.api.admin.urls", namespace="auth_admin"), name="auth_admin"),
]
