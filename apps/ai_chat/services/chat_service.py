# apps/chat/services/chat_service.py
import logging
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction, models

from apps.ai_chat.models import (
    AISession,
    AIMessage,
    AIMessageTypeEnum,
    AISessionStatusEnum,
    AITypeEnum,
)
from apps.chat.services.mongo_sync import MongoSyncService
from base_utils.services import AbstractBaseService

User = get_user_model()
logger = logging.getLogger(__name__)


class ChatService(AbstractBaseService):
    """
    Service for chat functionality
    """

    @staticmethod
    def send_message(
        chat_session: AISession,
        sender: User,
        content: str,
        message_type: str = AIMessageTypeEnum.TEXT,
        attachment: Any = None,
        is_ai: bool = False,
    ) -> AIMessage:
        """
        Send a message in a chat session
        """
        # Verify the chat session is active
        if chat_session.status != AISessionStatusEnum.ACTIVE:
            raise ValueError(f"Cannot send message to a {chat_session.status} chat session.")

        # Verify sender is part of the chat
        if sender != chat_session.client and sender != chat_session.consultant:
            raise ValueError("Sender is not a participant in this chat session.")

        # Create the message
        message = AIMessage.objects.create(
            chat_session=chat_session,
            sender=sender,
            content=content,
            message_type=message_type,
            attachment=attachment,
            is_ai=is_ai,
        )

        # Sync to MongoDB if enabled
        # MongoSyncService.sync_chat_message_to_mongo(message)

        return message

    @staticmethod
    def send_system_message(chat_session: AISession, content: str) -> AIMessage:
        """
        Send a system message in a chat session
        """
        # Create a system user if needed for the sender
        system_user = User.objects.filter(email="system@taino.ir").first()

        if not system_user:
            # This is a simplification - in a real system, you'd have a proper system user
            system_user = chat_session.user

        message = AIMessage.objects.create(
            chat_session=chat_session,
            sender=system_user,
            content=content,
            message_type=AIMessageTypeEnum.SYSTEM,
            is_system=True,
            # System messages are marked as read immediately
            is_read_by_client=True,
            is_read_by_consultant=True,
        )

        # Sync to MongoDB if enabled
        MongoSyncService.sync_chat_message_to_mongo(message)

        return message

    @staticmethod
    def end_chat_session(chat_session: AISession, ended_by: User, reason: Optional[str] = None) -> AISession:
        """
        End an active chat session
        """
        if chat_session.status != AISessionStatusEnum.ACTIVE:
            raise ValueError(f"Cannot end a {chat_session.status} chat session.")

        # Calculate session duration
        end_date = timezone.now()
        chat_session.end_date = end_date
        chat_session.status = AISessionStatusEnum.COMPLETED
        chat_session.save()

        # Create a system message for session end
        end_message = f"Chat session ended by {ended_by.first_name} {ended_by.last_name}."
        if reason:
            end_message += f" Reason: {reason}"

        ChatService.send_system_message(
            chat_session=chat_session,
            content=end_message,
        )

        # Sync final state to MongoDB
        MongoSyncService.sync_chat_session_to_mongo(chat_session)

        return chat_session

    @staticmethod
    def get_user_chat_sessions(
        user: User,
        status: Optional[str] = None,
        chat_type: Optional[str] = None,
        as_consultant: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> List[AISession]:
        """
        Get chat sessions for a user
        """
        query = AISession.objects.filter(is_deleted=False)

        if as_consultant:
            query = query.filter(consultant=user)
        else:
            query = query.filter(client=user)

        if status:
            query = query.filter(status=status)

        if chat_type:
            query = query.filter(chat_type=chat_type)

        return query.order_by("-created_at")[offset : offset + limit]
