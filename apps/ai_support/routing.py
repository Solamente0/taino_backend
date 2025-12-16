from django.urls import path
from apps.ai_support.consumers.support_consumer import SupportChatConsumer

websocket_urlpatterns = [
    path("ws/support/<str:session_id>/", SupportChatConsumer.as_asgi()),
]
