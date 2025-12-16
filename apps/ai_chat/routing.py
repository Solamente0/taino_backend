# apps/chat/routing.py
from django.urls import path

from apps.ai_chat.consumers.health import HealthCheckConsumer, DebugConsumer
from apps.ai_chat.consumers.ai_chat import AIChatConsumer

websocket_urlpatterns = [
    path("ws/chat/ai/<str:session_id>/", AIChatConsumer.as_asgi()),
    path("ws/health/", HealthCheckConsumer.as_asgi()),
    path("health/", HealthCheckConsumer.as_asgi()),  # Add this without the 'ws/' prefix
    path("ws/debug/", DebugConsumer.as_asgi()),
]
