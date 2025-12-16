from django.urls import include, path

app_name = "ai_support"

urlpatterns = [
    path("v1/", include("apps.ai_support.api.v1.urls", namespace="ai_support_v1")),
]
