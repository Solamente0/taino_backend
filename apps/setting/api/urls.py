from django.urls import include, path

app_name = "setting"

urlpatterns = [
    path(
        "admin/",
        include("apps.setting.api.admin.urls", namespace="setting_admin"),
        name="setting_admin",
    ),
    path(
        "v1/",
        include("apps.setting.api.v1.urls", namespace="setting_v1"),
        name="setting_v1",
    ),
]
