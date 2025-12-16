# apps/ai_chat/api/v1/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.ai_chat.api.v1.views import (
    AISessionViewSet,
    AIMessageViewSet,
    OCRAnalysisViewSet,
    LegalAnalysisViewSet,
    AnalysisHistoryViewSet,
    AIPricingViewSet,
)
from apps.ai_chat.api.v1.views.history import AIHistoryViewSet

app_name = "ai_chat"

router = DefaultRouter()
router.register("sessions", AISessionViewSet, basename="ai_sessions")
router.register("messages", AIMessageViewSet, basename="ai_messages")
router.register("ocr", OCRAnalysisViewSet, basename="ai_ocr")
router.register("legal", LegalAnalysisViewSet, basename="ai_legal")
router.register("history", AnalysisHistoryViewSet, basename="analysis_history")  # Add this line
router.register("ai-history", AIHistoryViewSet, basename="ai_history")  # Add this line
router.register("pricing", AIPricingViewSet, basename="ai_pricing")

urlpatterns = []
urlpatterns += router.urls
