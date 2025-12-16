# apps/ai_chat/api/admin/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.ai_chat.api.admin.views import (
    AdminAISessionViewSet,
    AdminAIMessageViewSet,
    AdminChatAIConfigViewSet,
)

app_name = "ai_chat"

router = DefaultRouter()
router.register("sessions", AdminAISessionViewSet, basename="admin_ai_sessions")
router.register("messages", AdminAIMessageViewSet, basename="admin_ai_messages")
router.register("ai-config", AdminChatAIConfigViewSet, basename="admin_ai_config")

urlpatterns = []
urlpatterns += router.urls
