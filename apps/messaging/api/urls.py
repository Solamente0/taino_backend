from django.urls import include, path

app_name = "messaging"

urlpatterns = [
    path("v1/", include("apps.messaging.api.v1.urls", namespace="messaging_v1"), name="messaging_v1"),
    path("admin/", include("apps.messaging.api.admin.urls", namespace="messaging_admin"), name="messaging_admin"),
]
