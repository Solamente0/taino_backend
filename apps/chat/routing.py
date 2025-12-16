# apps/chat/routing.py
from django.urls import path

from apps.chat.consumers.health import HealthCheckConsumer, DebugConsumer
from apps.chat.consumers.lawyer_chat import LawyerChatConsumer
from apps.chat.consumers.admin_chat import AdminChatConsumer

websocket_urlpatterns = [
    path("ws/chat/lawyer/<str:session_id>/", LawyerChatConsumer.as_asgi()),
    path("ws/chat/admin/<str:session_id>/", AdminChatConsumer.as_asgi()),
    path("ws/health/", HealthCheckConsumer.as_asgi()),
    path("health/", HealthCheckConsumer.as_asgi()),  # Add this without the 'ws/' prefix
    path("ws/debug/", DebugConsumer.as_asgi()),
]
