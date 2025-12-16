# apps/ai_chat/consumers/ai_chat.py
import json
import logging
from typing import Dict, Any, Optional
from django.utils import timezone

from apps.ai_chat.consumers.base import BaseTainoAIAsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class AIChatConsumer(BaseTainoAIAsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for AI chat
    """

    async def connect(self):
        """Connect to WebSocket"""
        logger.info(f"AIChatConsumer connect attempt for session: {self.scope['url_route']['kwargs'].get('session_id')}")

        try:
            self.session_id = self.scope["url_route"]["kwargs"].get("session_id")
            logger.info(f"Extracted session_id: {self.session_id}")
        except Exception as e:
            logger.error(f"Error extracting session_id: {str(e)}")
            await self.close(code=4002)
            return

        if not self.scope["user"].is_authenticated:
            logger.error(f"User is not authenticated, closing connection with code 4001")
            await self.close(code=4001)
            return

        self.user = self.scope["user"]
        logger.info(f"Authenticated user: {self.user.pid}")

        await super().connect()

        # Check if session is an AI chat
        if self.ai_session and self.ai_session.ai_type not in ["v", "v_plus", "v_x"]:
            await self.close(code=4004)
            return

        # Check if the AI session has expired
        if self.ai_session and self.ai_session.end_date and self.ai_session.end_date < timezone.now():
            await self.send_json(
                {
                    "type": "ai_chat.expired",
                    "message": "This AI chat session has expired.",
                    "timestamp": timezone.now().isoformat(),
                }
            )
            await self.close(code=4006)
            return

    async def receive_json(self, content):
        """Receive message from WebSocket"""
        # Check if the chat has expired before processing any messages
        if self.ai_session and self.ai_session.end_date and self.ai_session.end_date < timezone.now():
            await self.send_json(
                {
                    "type": "ai_chat.expired",
                    "message": "This AI chat session has expired.",
                    "timestamp": timezone.now().isoformat(),
                }
            )
            await self.close(code=4006)
            return

        message_type = content.get("type")
        logger.info(f"Received message type: {message_type}")

        if message_type == "ai_chat.message":
            await self.handle_chat_message(content)
        elif message_type == "ai_chat.typing":
            await self.handle_typing_status(content)
        elif message_type == "ai_chat.read":
            await self.handle_read_receipt(content)
        else:
            logger.warning(f"Unknown message type: {message_type}")
