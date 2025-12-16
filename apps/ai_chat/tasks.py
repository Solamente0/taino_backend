import logging

from celery import shared_task
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


# @shared_task
# def sync_mongo_to_postgres():
#     """
#     Sync data from MongoDB to PostgreSQL
#     This task should be run periodically
#     """
#     from apps.ai_chat.services.mongo_sync import MongoSyncService
#
#     try:
#         MongoSyncService.sync_from_mongo_to_django()
#         return {"status": "success", "message": "MongoDB sync completed"}
#     except Exception as e:
#         logger.error(f"Error syncing from MongoDB: {e}", exc_info=True)
#         return {"status": "error", "message": str(e)}


@shared_task(bind=True, name="apps.ai_chat.tasks.sync_mongo_to_postgres")
def sync_mongo_to_postgres():
    from django.core.management import call_command

    call_command("sync_mongo_to_postgres")


@shared_task(bind=True, name="apps.ai_chat.tasks.update_expired_ai_sessions")
def update_expired_ai_sessions():
    """
    Periodic task to update expired AI chat sessions
    """
    from django.utils import timezone
    from apps.ai_chat.models import AISession, AISessionStatusEnum
    from apps.ai_chat.services.ai_chat_service import AIChatService

    now = timezone.now()

    expired_sessions = AISession.objects.filter(status=AISessionStatusEnum.ACTIVE, end_date__lt=now, is_deleted=False)

    count = expired_sessions.update(status=AISessionStatusEnum.EXPIRED)

    for session in expired_sessions:
        AIChatService.send_message(
            ai_session=session,
            sender=session.user,
            content="جلسه گفتگو به پایان رسیده است. برای ادامه گفتگو لطفا جلسه جدیدی ایجاد کنید.",
            message_type="system",
            is_system=True,
        )

    return f"Updated {count} expired AI sessions"
