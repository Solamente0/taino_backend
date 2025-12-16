import logging
import base64
import os
import time

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.utils import timezone
from openai import OpenAI

from apps.chat.models import ChatSession
from apps.chat.services.chat_service import ChatService

logger = logging.getLogger(__name__)
User = get_user_model()


# @shared_task
# def sync_mongo_to_postgres():
#     """
#     Sync data from MongoDB to PostgreSQL
#     This task should be run periodically
#     """
#     from apps.chat.services.mongo_sync import MongoSyncService
#
#     try:
#         MongoSyncService.sync_from_mongo_to_django()
#         return {"status": "success", "message": "MongoDB sync completed"}
#     except Exception as e:
#         logger.error(f"Error syncing from MongoDB: {e}", exc_info=True)
#         return {"status": "error", "message": str(e)}


@shared_task(bind=True, name="apps.chat.tasks.sync_mongo_to_postgres")
def sync_mongo_to_postgres():
    from django.core.management import call_command

    call_command("sync_mongo_to_postgres")


@shared_task(bind=True, name="apps.chat.tasks.update_expired_sessions")
def update_expired_sessions():
    """
    Periodic task to update expired chat sessions
    """
    from django.utils import timezone
    from apps.chat.models import ChatSession, ChatSessionStatusEnum

    now = timezone.now()

    # Find all active sessions that have passed their end_time
    expired_sessions = ChatSession.objects.filter(status=ChatSessionStatusEnum.ACTIVE, end_time__lt=now, is_deleted=False)

    # Update their status to expired
    count = expired_sessions.update(status=ChatSessionStatusEnum.EXPIRED)

    # For each expired session, create a system message
    for session in expired_sessions:
        from apps.chat.services.chat_service import ChatService

        ChatService.send_system_message(
            chat_session=session, content="جلسه گفتگو به پایان رسیده است. برای ادامه گفتگو لطفا جلسه جدیدی ایجاد کنید."
        )

    return f"Updated {count} expired chat sessions"


@shared_task
def send_proposal_notification(proposal_id):
    """ارسال نوتیفیکیشن برای پیشنهاد جدید"""
    from apps.chat.models import LawyerProposal

    try:
        proposal = LawyerProposal.objects.get(id=proposal_id)
        chat_request = proposal.chat_request

        # نوتیفیکیشن
        from apps.notification.services.alarm import NotificationService

        NotificationService.create_notification(
            to_user=chat_request.client,
            name="پیشنهاد جدید",
            description=f"{proposal.lawyer.get_full_name()} پیشنهادی برای درخواست شما ارسال کرد",
            link=f"/requests/{chat_request.pid}",
        )

        # ایمیل
        # TODO: ارسال ایمیل

    except LawyerProposal.DoesNotExist:
        pass


@shared_task
def expire_old_requests():
    """منقضی کردن درخواست‌های قدیمی"""
    from apps.chat.models import ChatRequest, ChatRequestStatusEnum

    expired_requests = ChatRequest.objects.filter(status=ChatRequestStatusEnum.PENDING, expires_at__lt=timezone.now())

    count = expired_requests.update(status=ChatRequestStatusEnum.EXPIRED)
    return f"Expired {count} requests"
