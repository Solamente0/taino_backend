# apps/chat/api/admin/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.chat.api.admin.views import (
    AdminChatSessionViewSet,
    AdminChatMessageViewSet,
    AdminChatRequestViewSet,
    AdminChatSubscriptionViewSet
)

app_name = "chat"

router = DefaultRouter()
router.register("sessions", AdminChatSessionViewSet, basename="admin_chat_sessions")
router.register("messages", AdminChatMessageViewSet, basename="admin_chat_messages")
router.register("requests", AdminChatRequestViewSet, basename="admin_chat_requests")
router.register("subscriptions", AdminChatSubscriptionViewSet, basename="admin_chat_subscriptions")

urlpatterns = []

urlpatterns += router.urls
