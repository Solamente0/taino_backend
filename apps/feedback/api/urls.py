from django.urls import include, path

app_name = "feedback"

urlpatterns = [
    path("v1/", include("apps.feedback.api.v1.urls", namespace="feedback_v1"), name="feedback_v1"),
    path("admin/", include("apps.feedback.api.admin.urls", namespace="feedback_admin"), name="feedback_admin"),
]
