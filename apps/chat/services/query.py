# apps/chat/services/query.py
from django.db.models import QuerySet, Q, Count, Sum
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.chat.models import ChatSession, ChatMessage, ChatRequest, ChatSubscription, ChatSessionStatusEnum, ChatTypeEnum
from base_utils.services import AbstractBaseQuery

User = get_user_model()


class ChatQuery(AbstractBaseQuery):
    """
    Query service for chat data
    """

    @staticmethod
    def get_active_chat_sessions() -> QuerySet[ChatSession]:
        """
        Get all active chat sessions
        """
        return ChatSession.objects.filter(status=ChatSessionStatusEnum.ACTIVE, is_deleted=False)

    @staticmethod
    def get_user_chat_sessions(
        user_id: str, as_consultant: bool = False, chat_type: str = None, status: str = None
    ) -> QuerySet[ChatSession]:
        """
        Get chat sessions for a user
        """
        query = Q(is_deleted=False)

        if as_consultant:
            query &= Q(consultant__pid=user_id)
        else:
            query &= Q(client__pid=user_id)

        if chat_type:
            query &= Q(chat_type=chat_type)

        if status:
            query &= Q(status=status)

        return ChatSession.objects.filter(query).order_by("-created_at")

    @staticmethod
    def get_user_chat_requests(user_id: str, as_consultant: bool = False, status: str = None) -> QuerySet[ChatRequest]:
        """
        Get chat requests for a user
        """
        query = Q(is_deleted=False)

        if as_consultant:
            query &= Q(consultant__pid=user_id)
        else:
            query &= Q(client__pid=user_id)

        if status:
            query &= Q(status=status)

        return ChatRequest.objects.filter(query).order_by("-created_at")

    @staticmethod
    def get_chat_messages(chat_session_id: str, limit: int = 50, before_message_id: str = None) -> QuerySet[ChatMessage]:
        """
        Get messages for a chat session with pagination
        """
        query = Q(chat_session__pid=chat_session_id, is_deleted=False)

        if before_message_id:
            before_message = ChatMessage.objects.get(pid=before_message_id)
            query &= Q(created_at__lt=before_message.created_at)

        return ChatMessage.objects.filter(query).order_by("-created_at")[:limit]

    @staticmethod
    def get_consultants_available_for_chat(specialization: str = None, location: str = None) -> QuerySet[User]:
        """
        Get consultants who are available for chat
        """
        # Find consultants with active subscriptions and remaining chats
        consultants = User.objects.filter(
            chat_subscriptions__is_active=True,
            chat_subscriptions__end_date__gt=timezone.now(),
            chat_subscriptions__remaining_chats__gt=0,
        )

        if specialization:
            # This would be implemented based on lawyer specialization field
            # This is just a placeholder based on the available data
            pass

        if location:
            # This would be implemented based on lawyer location field
            # This is just a placeholder based on the available data
            pass

        return consultants.distinct()

    @staticmethod
    def get_unread_messages_count(user_id: str) -> int:
        """
        Get count of unread messages for a user
        """
        client_unread = ChatSession.objects.filter(client__pid=user_id, is_deleted=False).aggregate(
            total=Sum("unread_client_messages")
        )

        consultant_unread = ChatSession.objects.filter(consultant__pid=user_id, is_deleted=False).aggregate(
            total=Sum("unread_consultant_messages")
        )

        return (client_unread["total"] or 0) + (consultant_unread["total"] or 0)

    @staticmethod
    def get_chat_session_by_id(session_id: str) -> ChatSession:
        """
        Get a chat session by ID
        """
        return ChatSession.objects.filter(pid=session_id, is_deleted=False).first()

    @staticmethod
    def get_chat_request_by_id(request_id: str) -> ChatRequest:
        """
        Get a chat request by ID
        """
        return ChatRequest.objects.filter(pid=request_id, is_deleted=False).first()

    @staticmethod
    def get_active_user_subscription(user_id: str) -> ChatSubscription:
        """
        Get active subscription for a user
        """
        return ChatSubscription.objects.filter(user__pid=user_id, is_active=True, end_date__gt=timezone.now()).first()
