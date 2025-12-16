from django.urls import include, path

app_name = "user"

urlpatterns = [
    path("v1/", include("apps.user.api.v1.urls", namespace="user_v1"), name="user_v1"),
    path("admin/", include("apps.user.api.admin.urls", namespace="user_admin"), name="user_admin"),
]
