# apps/chat/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.ai_chat.models import AISession, AIMessage
from apps.ai_chat.services.mongo_sync import MongoSyncService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=AISession)
def sync_ai_session_to_mongo(sender, instance, created, **kwargs):
    """
    Sync chat session to MongoDB
    """
    try:
        MongoSyncService.sync_ai_session_to_mongo(instance)
    except Exception as e:
        logger.error(f"Error syncing chat session to MongoDB: {e}")


@receiver(post_save, sender=AIMessage)
def sync_chat_message_to_mongo(sender, instance, created, **kwargs):
    """
    Sync chat message to MongoDB
    """
    try:
        MongoSyncService.sync_chat_message_to_mongo(instance)
    except Exception as e:
        logger.error(f"Error syncing chat message to MongoDB: {e}")
