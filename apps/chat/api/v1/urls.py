# apps/chat/api/v1/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.chat.api.v1.views import (
    ChatSessionViewSet,
    ChatMessageViewSet,
    ChatRequestViewSet,
    ChatSubscriptionViewSet, LawyerProposalViewSet,
)

app_name = "chat"

router = DefaultRouter()
router.register("sessions", ChatSessionViewSet, basename="chat_sessions")
router.register("messages", ChatMessageViewSet, basename="chat_messages")
router.register("requests", ChatRequestViewSet, basename="chat_requests")
router.register("subscriptions", ChatSubscriptionViewSet, basename="chat_subscriptions")
router.register("proposals", LawyerProposalViewSet, basename="lawyer_proposals")

urlpatterns = []

urlpatterns += router.urls
