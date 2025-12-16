# apps/chat/services/chat_service.py
import logging
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction, models

from apps.chat.models import (
    ChatSession,
    ChatMessage,
    ChatRequest,
    ChatSubscription,
    MessageTypeEnum,
    ChatSessionStatusEnum,
    ChatTypeEnum,
)
from apps.chat.services.mongo_sync import MongoSyncService
from apps.setting.services.query import GeneralSettingsQuery
from base_utils.services import AbstractBaseService
from base_utils.subscription import check_bypass_user_payment

User = get_user_model()
logger = logging.getLogger(__name__)


class ChatService(AbstractBaseService):
    """
    Service for chat functionality
    """

    @staticmethod
    def create_chat_request(
        client: User,
        title: str,
        description: str,
        chat_type: str = ChatTypeEnum.LAWYER,
        proposed_fee: float = 0,
        proposed_time_minutes: int = 30,
        consultant: Optional[User] = None,
        specialization: Optional[str] = None,
        location_preference: Optional[str] = None,
        preferred_time: Optional[timezone.datetime] = None,
    ) -> ChatRequest:
        """
        Create a new chat request
        """
        # Set expiry time (default 48 hours)
        expires_at = timezone.now() + timezone.timedelta(hours=48)

        chat_request = ChatRequest.objects.create(
            client=client,
            consultant=consultant,
            title=title,
            description=description,
            chat_type=chat_type,
            proposed_fee=proposed_fee,
            proposed_time_minutes=proposed_time_minutes,
            expires_at=expires_at,
            specialization=specialization,
            location_preference=location_preference,
            preferred_time=preferred_time,
            creator=client,
        )

        return chat_request

    @staticmethod
    def accept_chat_request(
        chat_request: ChatRequest,
        consultant: User,
        response_message: Optional[str] = None,
        fee_amount: Optional[float] = None,
        time_limit_minutes: Optional[int] = None,
    ) -> ChatSession:
        """
        Accept a chat request and create a chat session
        """
        with transaction.atomic():
            # Check if the consultant has an active subscription
            subscription = ChatSubscription.objects.filter(
                user=consultant, is_active=True, end_date__gte=timezone.now()
            ).first()

            if not subscription or subscription.remaining_chats <= 0:
                raise ValueError("Consultant does not have an active subscription or has no remaining chats.")

            # Update the chat request
            chat_request.status = "accepted"
            chat_request.consultant = consultant
            chat_request.response_message = response_message
            chat_request.responded_at = timezone.now()
            chat_request.save()

            # Use proposed values if no overrides provided
            if fee_amount is None:
                fee_amount = chat_request.proposed_fee

            if time_limit_minutes is None:
                time_limit_minutes = chat_request.proposed_time_minutes

            # Create a new chat session
            chat_session = ChatSession.objects.create(
                client=chat_request.client,
                consultant=consultant,
                chat_type=chat_request.chat_type,
                status=ChatSessionStatusEnum.ACTIVE,
                title=chat_request.title,
                fee_amount=fee_amount,
                time_limit_minutes=time_limit_minutes,
                start_time=timezone.now(),
                chat_request=chat_request,
                creator=consultant,
            )

            # Update subscription usage
            subscription.used_chats += 1
            subscription.save(update_fields=["used_chats"])

            # Create a system message for the session start
            ChatService.send_system_message(
                chat_session=chat_session,
                content=f"Chat session started by {consultant.first_name} {consultant.last_name}. Duration: {time_limit_minutes} minutes.",
            )

            # Sync to MongoDB if enabled
            MongoSyncService.sync_chat_session_to_mongo(chat_session)

            return chat_session

    @staticmethod
    def reject_chat_request(chat_request: ChatRequest, consultant: User, response_message: str) -> ChatRequest:
        """
        Reject a chat request
        """
        chat_request.status = "rejected"
        chat_request.consultant = consultant
        chat_request.response_message = response_message
        chat_request.responded_at = timezone.now()
        chat_request.save()

        return chat_request

    @staticmethod
    def send_message(
        chat_session: ChatSession,
        sender: User,
        content: str,
        message_type: str = MessageTypeEnum.TEXT,
        attachment: Any = None,
        is_ai: bool = False,
    ) -> ChatMessage:
        """
        Send a message in a chat session
        """
        # Verify the chat session is active
        if chat_session.status != ChatSessionStatusEnum.ACTIVE:
            raise ValueError(f"Cannot send message to a {chat_session.status} chat session.")

        # Verify sender is part of the chat
        if sender != chat_session.client and sender != chat_session.consultant:
            raise ValueError("Sender is not a participant in this chat session.")

        # Check if consultant has exceeded their time limit
        if sender == chat_session.consultant:
            subscription = ChatSubscription.objects.filter(user=sender, is_active=True, end_date__gte=timezone.now()).first()

            if not subscription or subscription.remaining_minutes <= 0:
                raise ValueError("Consultant has exceeded their subscription time limit.")

        # Create the message
        message = ChatMessage.objects.create(
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
    def send_system_message(chat_session: ChatSession, content: str) -> ChatMessage:
        """
        Send a system message in a chat session
        """
        # Create a system user if needed for the sender
        system_user = User.objects.filter(email="system@vekalat-online.com").first()

        if not system_user:
            # This is a simplification - in a real system, you'd have a proper system user
            system_user = chat_session.client

        message = ChatMessage.objects.create(
            chat_session=chat_session,
            sender=system_user,
            content=content,
            message_type=MessageTypeEnum.SYSTEM,
            is_system=True,
            # System messages are marked as read immediately
            is_read_by_client=True,
            is_read_by_consultant=True,
        )

        # Sync to MongoDB if enabled
        MongoSyncService.sync_chat_message_to_mongo(message)

        return message

    @staticmethod
    def end_chat_session(chat_session: ChatSession, ended_by: User, reason: Optional[str] = None) -> ChatSession:
        """
        End an active chat session
        """
        if chat_session.status != ChatSessionStatusEnum.ACTIVE:
            raise ValueError(f"Cannot end a {chat_session.status} chat session.")

        # Calculate session duration
        end_time = timezone.now()
        chat_session.end_time = end_time
        chat_session.status = ChatSessionStatusEnum.COMPLETED
        chat_session.save()

        # Create a system message for session end
        end_message = f"Chat session ended by {ended_by.first_name} {ended_by.last_name}."
        if reason:
            end_message += f" Reason: {reason}"

        ChatService.send_system_message(
            chat_session=chat_session,
            content=end_message,
        )

        # Update subscription usage for the consultant if applicable
        if chat_session.consultant:
            # Calculate minutes used (rounded up)
            import math

            start_time = chat_session.start_time or chat_session.created_at
            duration_minutes = math.ceil((end_time - start_time).total_seconds() / 60)

            subscription = ChatSubscription.objects.filter(
                user=chat_session.consultant, is_active=True, end_date__gte=timezone.now()
            ).first()

            if subscription:
                subscription.used_minutes += duration_minutes
                subscription.save(update_fields=["used_minutes"])

            # Sync final state to MongoDB
        MongoSyncService.sync_chat_session_to_mongo(chat_session)

        return chat_session

    @staticmethod
    def mark_messages_as_read(chat_session: ChatSession, user: User) -> int:
        """
        Mark all unread messages as read for a user
        """
        count = 0

        if user == chat_session.client:
            # Mark messages from consultant as read by client
            count = chat_session.messages.filter(sender=chat_session.consultant, is_read_by_client=False).update(
                is_read_by_client=True, read_at=timezone.now()
            )

            if count > 0:
                chat_session.unread_client_messages = 0
                chat_session.save(update_fields=["unread_client_messages"])

        elif user == chat_session.consultant:
            # Mark messages from client as read by consultant
            count = chat_session.messages.filter(sender=chat_session.client, is_read_by_consultant=False).update(
                is_read_by_consultant=True, read_at=timezone.now()
            )

            if count > 0:
                chat_session.unread_consultant_messages = 0
                chat_session.save(update_fields=["unread_consultant_messages"])

        return count

    @staticmethod
    def get_user_chat_sessions(
        user: User,
        status: Optional[str] = None,
        chat_type: Optional[str] = None,
        as_consultant: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ChatSession]:
        """
        Get chat sessions for a user
        """
        query = ChatSession.objects.filter(is_deleted=False)

        if as_consultant:
            query = query.filter(consultant=user)
        else:
            query = query.filter(client=user)

        if status:
            query = query.filter(status=status)

        if chat_type:
            query = query.filter(chat_type=chat_type)

        return query.order_by("-created_at")[offset : offset + limit]

    @staticmethod
    def get_unread_messages_count(user: User) -> Dict[str, int]:
        """
        Get count of unread messages for a user
        """
        client_unread = ChatSession.objects.filter(client=user, is_deleted=False, unread_client_messages__gt=0).aggregate(
            total=models.Sum("unread_client_messages")
        )

        consultant_unread = ChatSession.objects.filter(
            consultant=user, is_deleted=False, unread_consultant_messages__gt=0
        ).aggregate(total=models.Sum("unread_consultant_messages"))

        return {
            "client_unread": client_unread["total"] or 0,
            "consultant_unread": consultant_unread["total"] or 0,
            "total": (client_unread["total"] or 0) + (consultant_unread["total"] or 0),
        }

    @staticmethod
    def can_user_chat_with_consultant(client: User, consultant: User) -> bool:
        """
        Check if a user can start a chat with a consultant
        """
        # Check if the consultant has an active subscription
        subscription = ChatSubscription.objects.filter(user=consultant, is_active=True, end_date__gte=timezone.now()).first()

        if not subscription or subscription.remaining_chats <= 0:
            return False

        # Check if there's already an active chat between them
        existing_chat = ChatSession.objects.filter(
            client=client, consultant=consultant, status=ChatSessionStatusEnum.ACTIVE, is_deleted=False
        ).exists()

        if existing_chat:
            return False

        return True
