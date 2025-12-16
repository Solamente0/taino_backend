# apps/chat/api/urls.py
from django.urls import include, path

app_name = "chat"

urlpatterns = [
    path("v1/", include("apps.chat.api.v1.urls", namespace="chat_v1"), name="chat_v1"),
    path("admin/", include("apps.chat.api.admin.urls", namespace="chat_admin"), name="chat_admin"),
]
