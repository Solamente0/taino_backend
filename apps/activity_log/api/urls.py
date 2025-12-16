from django.urls import include, path

app_name = "activity_log"

urlpatterns = [
    path("v1/", include("apps.activity_log.api.v1.urls", namespace="activity_log_v1"), name="activity_log_v1"),
    path("admin/", include("apps.activity_log.api.admin.urls", namespace="activity_log_admin"), name="activity_log_admin"),
]
