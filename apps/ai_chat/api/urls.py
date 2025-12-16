# apps/ai_chat/api/urls.py
from django.urls import include, path

app_name = "ai_chat"

urlpatterns = [
    path("v1/", include("apps.ai_chat.api.v1.urls", namespace="ai_chat_v1")),
    path("admin/", include("apps.ai_chat.api.admin.urls", namespace="ai_chat_admin")),
]
