from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.ai_support.api.v1.views import (
    SupportSessionViewSet,
    SupportMessageViewSet,
    SupportAIConfigViewSet
)

app_name = "ai_support"

router = DefaultRouter()
router.register("configs", SupportAIConfigViewSet, basename="support_configs")
router.register("sessions", SupportSessionViewSet, basename="support_sessions")
router.register("messages", SupportMessageViewSet, basename="support_messages")

urlpatterns = router.urls
