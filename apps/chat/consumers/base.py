# apps/chat/consumers/base.py
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.chat.models import ChatSession, ChatMessage

User = get_user_model()
logger = logging.getLogger(__name__)


class BaseTainoAsyncJsonWebsocketConsumer(AsyncJsonWebsocketConsumer):
    """
    Base WebSocket consumer for chat
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.session_id = None
        self.chat_session = None
        self.room_group_name = None

    async def connect(self):
        """
        Connect to WebSocket
        """
        if not self.scope["user"].is_authenticated:
            await self.close(code=4001)
            return

        self.user = self.scope["user"]

        # Get session ID from URL route
        self.session_id = self.scope["url_route"]["kwargs"].get("session_id")
        if not self.session_id:
            await self.close(code=4002)
            return

        # Check if session exists and user has access
        self.chat_session = await self.get_chat_session()
        if not self.chat_session:
            await self.close(code=4003, reason="Error While Finding Chat Session!")
            return

        # Check if the chat session has expired
        if self.chat_session.end_time and self.chat_session.end_time < timezone.now():
            # Session has expired, close the connection
            await self.close(code=4006, reason="Chat Session Expired!")
            return

        # Join room group
        self.room_group_name = f"chat_{self.session_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        # Mark messages as read for the connected user
        await self.mark_messages_as_read()

        # Send recent messages
        await self.send_recent_messages()

    async def disconnect(self, close_code):
        """
        Disconnect from WebSocket
        """
        if self.room_group_name:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        await self.update_user_status(is_online=False)

    async def receive_json(self, content):
        """
        Receive message from WebSocket
        """
        # Check if the chat has expired before processing any messages
        if self.chat_session and self.chat_session.end_time and self.chat_session.end_time < timezone.now():
            await self.send_json(
                {
                    "type": "chat.expired",
                    "message": "This chat session has expired.",
                    "timestamp": timezone.now().isoformat(),
                }
            )
            await self.close(code=4006)
            return

        message_type = content.get("type")
        print(f"message_type:::: {message_type=}")

        if message_type == "chat.message":
            await self.handle_chat_message(content)
        elif message_type == "chat.typing":
            await self.handle_typing_status(content)
        elif message_type == "chat.read":
            await self.handle_read_receipt(content)
        else:
            logger.warning(f"Unknown message type: {message_type}")

    async def chat_message(self, event):
        """
        Send message to WebSocket
        """
        await self.send_json(event)

    async def user_typing(self, event):
        """
        Send typing status to WebSocket
        """
        print(f"enveeent::: {event=}", flush=True)
        await self.send_json(event)
        # await self.send_json(
        #     {
        #         "type": "chat.typing",  # Make sure this matches what the front-end expects
        #         "user": event.get("user"),
        #         "user_name": event.get("user_name"),
        #         "is_typing": event.get("is_typing"),
        #     }
        # )

    async def message_read(self, event):
        """
        Send read receipt to WebSocket
        """
        await self.send_json(event)

    @database_sync_to_async
    def get_chat_session(self) -> Optional[ChatSession]:
        """
        Get chat session and check user permissions
        """
        try:
            session = ChatSession.objects.get(pid=self.session_id, is_deleted=False)

            # Check if user is allowed to access this session
            if self.user != session.client and self.user != session.consultant:
                return None

            return session
        except ChatSession.DoesNotExist:
            return None

    @database_sync_to_async
    def mark_messages_as_read(self):
        """
        Mark messages as read for the connected user
        """
        if not self.chat_session:
            return

        if self.user == self.chat_session.client:
            self.chat_session.mark_all_read_for_client()
        elif self.user == self.chat_session.consultant:
            self.chat_session.mark_all_read_for_consultant()

    @database_sync_to_async
    def get_recent_messages(self, limit=20) -> list:
        """
        Get recent messages for the chat session
        """
        if not self.chat_session:
            return []
        messages = (
            ChatMessage.objects.filter(chat_session=self.chat_session, is_deleted=False)
            .select_related("sender")  # ✅ pre-fetch sender to avoid lazy loading
            .order_by("-created_at")[:limit]
        )

        # messages = ChatMessage.objects.filter(chat_session=self.chat_session, is_deleted=False).order_by("-created_at")[
        #     :limit
        # ]
        print(f"messs::: {messages=}", flush=True)
        # Ctainoert to list
        return list(reversed(messages))

    @database_sync_to_async
    def create_message(self, content) -> Optional[ChatMessage]:
        """
        Create a new message
        """
        from apps.chat.services.chat_service import ChatService

        if not self.chat_session:
            return None

        # Check if session is active
        if self.chat_session.status != "active":
            return None

        # Check if session has expired
        if self.chat_session.end_time and self.chat_session.end_time < timezone.now():
            return None

        # Check if user is part of the chat
        if self.user != self.chat_session.client and self.user != self.chat_session.consultant:
            return None

        try:
            # Check if user can send messages (subscription limits for consultant)
            if self.user == self.chat_session.consultant:
                from apps.chat.models import ChatSubscription

                subscription = ChatSubscription.objects.filter(
                    user=self.user, is_active=True, end_date__gte=timezone.now()
                ).first()

                if not subscription or subscription.remaining_minutes <= 0:
                    return None

            message_text = content.get("message", "").strip()
            message_type = content.get("message_type", "text")

            if not message_text:
                return None

            # Create message
            message = ChatMessage.objects.create(
                chat_session=self.chat_session,
                sender=self.user,
                message_type=message_type,
                content=message_text,
                is_read_by_client=self.user == self.chat_session.client,
                is_read_by_consultant=self.user == self.chat_session.consultant,
            )

            # Update unread counts
            if self.user == self.chat_session.client:
                self.chat_session.unread_consultant_messages += 1
            else:
                self.chat_session.unread_client_messages += 1

            self.chat_session.total_messages += 1
            self.chat_session.save(update_fields=["unread_client_messages", "unread_consultant_messages", "total_messages"])

            # Sync to MongoDB if enabled
            # from apps.chat.services.mongo_sync import MongoSyncService
            #
            # MongoSyncService.sync_chat_message_to_mongo(message)

            return message
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return None

    @database_sync_to_async
    def update_user_status(self, is_online=True):
        """
        Update user online status
        """
        if not self.chat_session or not self.user:
            return

        # This is just a placeholder - you would implement user online status
        # as needed for your app
        pass

    async def send_recent_messages(self):
        """
        Send recent messages to the client
        """
        messages = await self.get_recent_messages()

        for message in messages:
            await self.send_json(
                {
                    "type": "chat.message",
                    "id": str(message.pid),
                    "sender": str(message.sender.pid),
                    "sender_name": f"{message.sender.first_name} {message.sender.last_name}",
                    "message": message.content,
                    "message_type": message.message_type,
                    "timestamp": message.created_at.isoformat(),
                    "is_ai": message.is_ai,
                    "is_system": message.is_system,
                }
            )

    async def handle_chat_message(self, content):
        """
        Handle chat message
        """
        message = await self.create_message(content)

        if not message:
            await self.send_json({"type": "chat.error", "error": "Failed to send message", "original_content": content})
            return

        message_data = {
            "type": "chat.message",
            "id": str(message.pid),
            "sender": str(message.sender.pid),
            "sender_name": f"{message.sender.first_name} {message.sender.last_name}",
            "message": message.content,
            "message_type": message.message_type,
            "timestamp": message.created_at.isoformat(),
            "is_ai": message.is_ai,
            "is_system": message.is_system,
        }
        print(f"msg_data:::: {message_data=}")
        # Send message to room group
        await self.channel_layer.group_send(self.room_group_name, message_data)

        # If this is an AI chat, process the AI response
        if self.chat_session.chat_type == "ai" and not message.is_ai and not message.is_system:
            # Send typing indicator before processing

            # Process the AI response in a background task
            await self.process_ai_response(message)

    async def handle_typing_status(self, content):
        """
        Handle typing status
        """
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_typing",
                "user": str(self.user.pid),
                "user_name": f"{self.user.first_name} {self.user.last_name}",
                "is_typing": content.get("is_typing", False),
            },
        )

    async def handle_read_receipt(self, content):
        """
        Handle read receipt
        """
        if not self.chat_session:
            return

        await self.mark_messages_as_read()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "message_read",
                "user": str(self.user.pid),
                "user_name": f"{self.user.first_name} {self.user.last_name}",
                "timestamp": timezone.now().isoformat(),
            },
        )

    async def process_ai_response(self, user_message):
        """
        Process AI response for AI chat
        """
        import asyncio

        # First send the typing indicator
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_typing",
                "user": "ai",
                "user_name": "هوش مصنوعی",
                "is_typing": True,
            },
        )

        # Create a background task for AI processing (don't await it)
        asyncio.create_task(self._generate_ai_response(user_message))

        # Return immediately so we don't block the WebSocket
        return None

    async def _generate_ai_response(self, user_message):
        """
        Background task to generate AI response
        """
        from apps.chat.services.chat_service import ChatService
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Call AI service to generate response - no need to pass AI config directly
            # The service will get the appropriate config based on chat_type in ai_context
            ai_message = await ChatService.generate_response(chat_session=self.chat_session, user_message=user_message)

            if ai_message:
                # Send AI message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat.message",
                        "id": str(ai_message.pid),
                        "sender": "ai",
                        "sender_name": "هوش مصنوعی",
                        "message": ai_message.content,
                        "message_type": ai_message.message_type,
                        "timestamp": ai_message.created_at.isoformat(),
                        "is_ai": True,
                        "is_system": False,
                        "chat_type": (
                            self.chat_session.ai_context.get("chat_type", "v") if self.chat_session.ai_context else "v"
                        ),
                    },
                )
            else:
                # If there was a problem with the AI message, send an error message
                logger.error("Failed to generate AI response")

                # Send a failure message to the user
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat.message",
                        "id": "error",
                        "sender": "ai",
                        "sender_name": "هوش مصنوعی",
                        "message": "متأسفانه در حال حاضر قادر به پاسخگویی نیستم. لطفاً بعداً دوباره تلاش کنید.",
                        "message_type": "text",
                        "timestamp": datetime.now().isoformat(),
                        "is_ai": True,
                        "is_system": True,
                    },
                )
        except Exception as e:
            # Log the error
            logger.error(f"Error generating AI response: {e}")

            # Send an error message to the user
            try:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat.message",
                        "id": "error",
                        "sender": "ai",
                        "sender_name": "هوش مصنوعی",
                        "message": "متأسفانه در حال حاضر قادر به پاسخگویی نیستم. لطفاً بعداً دوباره تلاش کنید.",
                        "message_type": "text",
                        "timestamp": datetime.now().isoformat(),
                        "is_ai": True,
                        "is_system": True,
                    },
                )
            except Exception as inner_e:
                logger.error(f"Error sending error message: {inner_e}")
        finally:
            # Stop typing indicator regardless of success or failure
            try:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "user_typing",
                        "user": "ai",
                        "user_name": "هوش مصنوعی",
                        "is_typing": False,
                    },
                )
            except Exception as e:
                logger.error(f"Error stopping typing indicator: {e}")
