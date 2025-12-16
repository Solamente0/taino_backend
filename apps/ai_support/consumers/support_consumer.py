# apps/ai_support/consumers/support_consumer.py
import json
import logging
from typing import Optional
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.ai_support.models import SupportSession, SupportMessage, SupportMessageTypeEnum

User = get_user_model()
logger = logging.getLogger(__name__)


class SupportChatConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for support chat"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.session_id = None
        self.session = None
        self.room_group_name = None
    
    async def connect(self):
        """Connect to WebSocket"""
        logger.info(f"Support chat connect attempt")
        
        if not self.scope["user"].is_authenticated:
            logger.error("User not authenticated")
            await self.close(code=4001)
            return
        
        self.user = self.scope["user"]
        self.session_id = self.scope["url_route"]["kwargs"].get("session_id")
        
        if not self.session_id:
            logger.error("No session_id provided")
            await self.close(code=4002)
            return
        
        # Get or create session
        self.session = await self.get_or_create_session()
        if not self.session:
            logger.error("Failed to get/create session")
            await self.close(code=4003)
            return
        
        # Join room group
        self.room_group_name = f"support_{self.session_id}"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Support chat connected: {self.session_id}")
        
        # Mark messages as read
        await self.mark_messages_as_read()
        
        # Send recent messages
        await self.send_recent_messages()
    
    async def disconnect(self, close_code):
        """Disconnect from WebSocket"""
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        logger.info(f"Support chat disconnected: {close_code}")
    
    async def receive_json(self, content):
        """Receive message from WebSocket"""
        message_type = content.get("type")
        logger.info(f"Received message type: {message_type}")
        
        if message_type == "support.message":
            await self.handle_chat_message(content)
        elif message_type == "support.typing":
            await self.handle_typing_status(content)
        elif message_type == "support.read":
            await self.handle_read_receipt(content)
    
    async def support_message(self, event):
        """Send message to WebSocket"""
        await self.send_json({
            "type": "support.message",
            **event.get("message", {})
        })
    
    async def user_typing(self, event):
        """Send typing status"""
        await self.send_json(event)
    
    async def message_read(self, event):
        """Send read receipt"""
        await self.send_json(event)
    
    @database_sync_to_async
    def get_or_create_session(self) -> Optional[SupportSession]:
        """Get or create support session"""
        try:
            session, created = SupportSession.objects.get_or_create(
                pid=self.session_id,
                user=self.user,
                defaults={
                    "status": "active",
                    "subject": "پشتیبانی"
                }
            )
            return session
        except Exception as e:
            logger.error(f"Error getting/creating session: {e}")
            return None
    
    @database_sync_to_async
    def mark_messages_as_read(self):
        """Mark messages as read"""
        if self.session:
            self.session.mark_all_read()
    
    @database_sync_to_async
    def get_recent_messages(self, limit=20) -> list:
        """Get recent messages"""
        if not self.session:
            return []
        
        messages = SupportMessage.objects.filter(
            session=self.session,
            is_deleted=False
        ).select_related("sender").order_by("-created_at")[:limit]
        
        return list(reversed(messages))
    
    async def send_recent_messages(self):
        """Send recent messages to client"""
        messages = await self.get_recent_messages()
        
        for message in messages:
            await self.send_json({
                "type": "support.message",
                "id": str(message.pid),
                "sender": str(message.sender.pid),
                "sender_name": f"{message.sender.first_name} {message.sender.last_name}",
                "content": message.content,
                "message_type": message.message_type,
                "timestamp": message.created_at.isoformat(),
                "is_ai": message.is_ai,
            })
    
    @database_sync_to_async
    def create_message(self, content: str, message_type: str = "text") -> Optional[SupportMessage]:
        """Create a new message"""
        try:
            if not self.session or self.session.status != "active":
                return None
            
            message = SupportMessage.objects.create(
                session=self.session,
                sender=self.user,
                content=content,
                message_type=message_type,
                is_ai=False
            )
            
            return message
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return None
    
    async def handle_chat_message(self, content):
        """Handle chat message"""
        message_text = content.get("content", "").strip()
        message_type = content.get("message_type", "text")
        
        if not message_text:
            return
        
        # Create user message
        message = await self.create_message(message_text, message_type)
        if not message:
            await self.send_json({
                "type": "support.error",
                "error": "Failed to send message"
            })
            return
        
        # Send to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "support_message",
                "message": {
                    "id": str(message.pid),
                    "sender": str(message.sender.pid),
                    "sender_name": f"{message.sender.first_name} {message.sender.last_name}",
                    "content": message.content,
                    "message_type": message.message_type,
                    "timestamp": message.created_at.isoformat(),
                    "is_ai": False,
                }
            }
        )
        
        # Trigger AI response via Celery
        from apps.ai_support.tasks import generate_ai_support_response
        generate_ai_support_response.delay(
            str(self.session.pid),
            str(message.pid)
        )
    
    async def handle_typing_status(self, content):
        """Handle typing status"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_typing",
                "user": str(self.user.pid),
                "user_name": f"{self.user.first_name} {self.user.last_name}",
                "is_typing": content.get("is_typing", False),
            }
        )
    
    async def handle_read_receipt(self, content):
        """Handle read receipt"""
        await self.mark_messages_as_read()
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "message_read",
                "user": str(self.user.pid),
                "user_name": f"{self.user.first_name} {self.user.last_name}",
                "timestamp": timezone.now().isoformat(),
            }
        )
