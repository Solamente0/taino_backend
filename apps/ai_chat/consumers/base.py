# apps/ai_chat/consumers/base.py
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.ai_chat.models import AISession, AIMessage

User = get_user_model()
logger = logging.getLogger(__name__)


class BaseTainoAIAsyncJsonWebsocketConsumer(AsyncJsonWebsocketConsumer):
    """Base WebSocket consumer for AI chat"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.session_id = None
        self.ai_session = None
        self.room_group_name = None

    async def connect(self):
        """Connect to WebSocket"""
        if not self.scope["user"].is_authenticated:
            await self.close(code=4001)
            return

        self.user = self.scope["user"]

        self.session_id = self.scope["url_route"]["kwargs"].get("session_id")
        if not self.session_id:
            await self.close(code=4002)
            return

        self.ai_session = await self.get_ai_session()
        if not self.ai_session:
            await self.close(code=4003, reason="Error While Finding AI Session!")
            return

        if self.ai_session.end_date and self.ai_session.end_date < timezone.now():
            await self.close(code=4006, reason="AI Session Expired!")
            return

        self.room_group_name = f"ai_chat_{self.session_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        await self.mark_messages_as_read()
        await self.send_recent_messages()

    async def disconnect(self, close_code):
        """Disconnect from WebSocket"""
        if self.room_group_name:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive_json(self, content):
        """Receive message from WebSocket"""
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

        if message_type == "ai_chat.message":
            await self.handle_chat_message(content)
        elif message_type == "ai_chat.typing":
            await self.handle_typing_status(content)
        elif message_type == "ai_chat.read":
            await self.handle_read_receipt(content)
        else:
            logger.warning(f"Unknown message type: {message_type}")

    async def ai_chat_message(self, event):
        """Send message to WebSocket"""
        await self.send_json(event)

    async def user_typing(self, event):
        """Send typing status to WebSocket"""
        await self.send_json(event)

    async def message_read(self, event):
        """Send read receipt to WebSocket"""
        await self.send_json(event)

    @database_sync_to_async
    def get_ai_session(self) -> Optional[AISession]:
        """Get AI session and check user permissions"""
        try:
            session = AISession.objects.get(pid=self.session_id, is_deleted=False)

            if self.user != session.user:
                return None

            return session
        except AISession.DoesNotExist:
            return None

    @database_sync_to_async
    def mark_messages_as_read(self):
        """Mark messages as read for the connected user"""
        if not self.ai_session:
            return

        self.ai_session.mark_all_read()

    @database_sync_to_async
    def get_recent_messages(self, limit=20) -> list:
        """Get recent messages for the AI session"""
        if not self.ai_session:
            return []

        messages = (
            AIMessage.objects.filter(ai_session=self.ai_session, is_deleted=False)
            .select_related("sender")
            .order_by("-created_at")[:limit]
        )

        return list(reversed(messages))

    @database_sync_to_async
    def create_message(self, content) -> Optional[AIMessage]:
        """
        Create a new message with character validation for hybrid pricing
        ✅ با پشتیبانی از فایل‌های اتچ شده
        """
        from apps.ai_chat.services.ai_chat_service import AIChatService
        from apps.ai_chat.services.ai_pricing_calculator import AIPricingCalculator

        if not self.ai_session:
            return None

        if self.ai_session.status != "active":
            return None

        if self.ai_session.end_date and self.ai_session.end_date < timezone.now():
            return None

        if self.user != self.ai_session.user:
            return None
        try:
            message_text = content.get("message", "").strip()
            message_type = content.get("message_type", "text")

            # ✅ استخراج اطلاعات فایل‌ها
            image_count = content.get("image_count", 0)
            pdf_page_count = content.get("pdf_page_count", 0)

            # ✅ Base64 فایل‌ها (اگر ارسال شده باشند)
            attached_images_b64 = content.get("attached_images", [])
            attached_pdf_b64 = content.get("attached_pdf", None)

            if not message_text:
                return None

            # ═══════════════════════════════════════════════════
            # اعتبارسنجی و پیش‌شارژ برای قیمت‌گذاری هیبریدی
            # ═══════════════════════════════════════════════════
            if self.ai_session.ai_config:
                ai_config = self.ai_session.ai_config

                is_readonly, reason = self.ai_session.check_and_update_readonly()
                if is_readonly:
                    logger.warning(f"Session {self.ai_session.pid} is readonly: {reason}")
                    return None

                if ai_config.is_advanced_hybrid_pricing():
                    char_count_backend = AIPricingCalculator.count_characters(message_text)
                    char_count_frontend = content.get("character_count", char_count_backend)
                    max_tokens_requested = content.get("max_tokens", self.ai_session.max_tokens)

                    # اعتبارسنجی تطابق
                    is_valid, error_msg = AIPricingCalculator.validate_request(
                        ai_config_static_name=ai_config.static_name,
                        character_count_frontend=char_count_frontend,
                        character_count_backend=char_count_backend,
                        max_tokens_requested=max_tokens_requested,
                        tolerance=50,
                    )

                    if not is_valid:
                        logger.error(f"Character validation failed: {error_msg}")
                        return None

                    # ✅ پیش‌شارژ با در نظر گرفتن فایل‌ها
                    success, message, details = AIPricingCalculator.charge_user(
                        user=self.user,
                        ai_config_static_name=ai_config.static_name,
                        character_count=char_count_backend,
                        max_tokens_requested=max_tokens_requested,
                        image_count=image_count,
                        pdf_page_count=pdf_page_count,
                        description=f"پیام در {ai_config.name} با {image_count} عکس و {pdf_page_count} صفحه PDF",
                    )

                    if not success:
                        logger.error(f"Pre-charge failed: {message}")
                        return None

                    # ذخیره اطلاعات هزینه
                    cost_breakdown = details
                    self.ai_session.add_hybrid_usage(
                        character_count=char_count_backend, input_tokens=0, output_tokens=0, cost_breakdown=cost_breakdown
                    )

                elif ai_config.is_message_based_pricing():
                    cost = float(ai_config.cost_per_message)

                    if cost > 0:
                        from apps.wallet.services.wallet import WalletService

                        balance = WalletService.get_wallet_coin_balance(self.user)
                        if balance < cost:
                            logger.error(f"Insufficient balance: {cost} required, {balance} available")
                            return None

            # ✅ پردازش فایل‌ها (اگر نیاز باشد)
            # این بخش را بر اساس نیاز خود پیاده‌سازی کنید
            # مثلاً ذخیره در TainoDocument یا ارسال مستقیم به AI API

            attachment = None
            if attached_images_b64 or attached_pdf_b64:
                # TODO: پردازش و ذخیره فایل‌ها
                # attachment = process_attachments(attached_images_b64, attached_pdf_b64)
                pass

            # ایجاد پیام
            message = AIChatService.send_message(
                ai_session=self.ai_session,
                sender=self.user,
                content=message_text,
                message_type=message_type,
                # attachment=attachment,
            )

            return message

        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return None

    async def send_recent_messages(self):
        """Send recent messages to the client"""
        messages = await self.get_recent_messages()

        for message in messages:
            await self.send_json(
                {
                    "type": "ai_chat.message",
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
        """Handle chat message"""
        message = await self.create_message(content)

        if not message:
            await self.send_json({"type": "ai_chat.error", "error": "Failed to send message", "original_content": content})
            return

        message_data = {
            "type": "ai_chat.message",
            "id": str(message.pid),
            "sender": str(message.sender.pid),
            "sender_name": f"{message.sender.first_name} {message.sender.last_name}",
            "message": message.content,
            "message_type": message.message_type,
            "timestamp": message.created_at.isoformat(),
            "is_ai": message.is_ai,
            "is_system": message.is_system,
        }

        await self.channel_layer.group_send(self.room_group_name, message_data)

        # Process AI response if this is a user message
        if not message.is_ai and not message.is_system:
            await self.process_ai_response(message)

    async def handle_typing_status(self, content):
        """Handle typing status"""
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
        """Handle read receipt"""
        if not self.ai_session:
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
        """Process AI response for AI chat"""
        # Send typing indicator immediately
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_typing",
                "user": "ai",
                "user_name": "هوش مصنوعی",
                "is_typing": True,
            },
        )

        # Import asyncio to create background task
        import asyncio

        # Create background task for AI response generation
        asyncio.create_task(self._generate_ai_response(user_message))

    async def _generate_ai_response(self, user_message):
        """Background task to generate AI response"""
        from apps.ai_chat.services.ai_service import ChatBackendAIService

        try:
            # Generate AI response
            ai_message = await ChatBackendAIService.generate_response(ai_session=self.ai_session, user_message=user_message)

            if ai_message:
                # Send the AI response
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "ai_chat.message",
                        "id": str(ai_message.pid),
                        "sender": "ai",
                        "sender_name": "هوش مصنوعی",
                        "message": ai_message.content,
                        "message_type": ai_message.message_type,
                        "timestamp": ai_message.created_at.isoformat(),
                        "is_ai": True,
                        "is_system": False,
                        "ai_type": (self.ai_session.ai_context.get("ai_type", "v") if self.ai_session.ai_context else "v"),
                    },
                )
            else:
                logger.error("Failed to generate AI response")
                # Send error message
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "ai_chat.message",
                        "id": "error",
                        "sender": "ai",
                        "sender_name": "هوش مصنوعی",
                        "message": "متأسفانه در حال حاضر قادر به پاسخگویی نیستم. لطفاً بعداً دوباره تلاش کنید.",
                        "message_type": "text",
                        "timestamp": timezone.now().isoformat(),
                        "is_ai": True,
                        "is_system": True,
                    },
                )

        except Exception as e:
            logger.error(f"Error generating AI response: {e}", exc_info=True)

            try:
                # Send error message to user
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "ai_chat.message",
                        "id": "error",
                        "sender": "ai",
                        "sender_name": "هوش مصنوعی",
                        "message": "متأسفانه در حال حاضر قادر به پاسخگویی نیستم. لطفاً بعداً دوباره تلاش کنید.",
                        "message_type": "text",
                        "timestamp": timezone.now().isoformat(),
                        "is_ai": True,
                        "is_system": True,
                    },
                )
            except Exception as inner_e:
                logger.error(f"Error sending error message: {inner_e}")

        finally:
            # Always stop typing indicator
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
