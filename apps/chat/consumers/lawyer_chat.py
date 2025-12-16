import json
import logging
from typing import Dict, Any, Optional

from apps.chat.consumers.base import BaseTainoAsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class LawyerChatConsumer(BaseTainoAsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for lawyer-client chat
    """

    async def connect(self):
        """
        Connect to WebSocket
        """
        await super().connect()

        # Check if session is a lawyer chat
        if self.chat_session and self.chat_session.chat_type != "lawyer":
            await self.close(code=4004)
            return
