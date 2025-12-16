from django.urls import include, path

app_name = "notification"

urlpatterns = [
    path("v1/", include("apps.notification.api.v1.urls", namespace="notification"), name="notification_v1"),
]
