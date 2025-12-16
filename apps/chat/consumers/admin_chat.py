# apps/chat/consumers/admin_chat.py
import json
import logging
from typing import Dict, Any, Optional

from apps.chat.consumers.base import BaseTainoAsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class AdminChatConsumer(BaseTainoAsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for admin-client chat
    """

    async def connect(self):
        """
        Connect to WebSocket
        """
        await super().connect()

        # Check if session is an admin chat
        if self.chat_session and self.chat_session.chat_type != "admin":
            await self.close(code=4004)
            return

        # Check if user is admin (for the consultant side)
        if self.user == self.chat_session.consultant and not self.user.is_admin:
            await self.close(code=4005)
            return
