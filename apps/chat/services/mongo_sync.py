# apps/chat/services/mongo_sync.py
import logging
import pymongo
from typing import Dict, Any, Optional
from django.conf import settings
from bson import ObjectId

from apps.chat.models import ChatSession, ChatMessage

logger = logging.getLogger(__name__)

# MongoDB connection settings
try:
    MONGO_ENABLED = getattr(settings, "CHAT_MONGO_ENABLED", False)
    MONGO_URI = getattr(settings, "CHAT_MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB = getattr(settings, "CHAT_MONGO_DB", "vekalat_chat")
except ImportError:
    MONGO_ENABLED = False
    MONGO_URI = "mongodb://localhost:27017/"
    MONGO_DB = "vekalat_chat"


class MongoSyncService:
    """
    Service for synchronizing chat data with MongoDB
    """

    @staticmethod
    def get_mongo_client():
        """Get MongoDB client"""
        if not MONGO_ENABLED:
            return None

        try:
            return pymongo.MongoClient(MONGO_URI)
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return None

    @staticmethod
    def sync_chat_session_to_mongo(chat_session: ChatSession) -> Optional[str]:
        """
        Sync a chat session to MongoDB
        """
        if not MONGO_ENABLED:
            return None

        client = MongoSyncService.get_mongo_client()
        if not client:
            return None

        try:
            db = client[MONGO_DB]
            sessions_collection = db.chat_sessions

            # Prepare session data
            session_data = {
                "django_id": str(chat_session.pid),
                "client_id": str(chat_session.client.pid),
                "consultant_id": str(chat_session.consultant.pid) if chat_session.consultant else None,
                "status": chat_session.status,
                "chat_type": chat_session.chat_type,
                "title": chat_session.title,
                "fee_amount": float(chat_session.fee_amount),
                "time_limit_minutes": chat_session.time_limit_minutes,
                "start_time": chat_session.start_time,
                "end_time": chat_session.end_time,
                "created_at": chat_session.created_at,
                "updated_at": chat_session.updated_at,
                "is_active": chat_session.is_active,
                "is_deleted": chat_session.is_deleted,
                "unread_client_messages": chat_session.unread_client_messages,
                "unread_consultant_messages": chat_session.unread_consultant_messages,
                "total_messages": chat_session.total_messages,
            }

            # If session already exists in MongoDB, update it
            if chat_session.mongo_id:
                result = sessions_collection.update_one({"_id": ObjectId(chat_session.mongo_id)}, {"$set": session_data})

                if result.modified_count == 0:
                    # If not found, insert as new
                    result = sessions_collection.insert_one(session_data)
                    mongo_id = str(result.inserted_id)

                    # Update Django model with MongoDB ID
                    chat_session.mongo_id = mongo_id
                    chat_session.is_synced_to_mongo = True
                    chat_session.save(update_fields=["mongo_id", "is_synced_to_mongo"])

                    return mongo_id

                return chat_session.mongo_id

            # Insert new session
            result = sessions_collection.insert_one(session_data)
            mongo_id = str(result.inserted_id)

            # Update Django model with MongoDB ID
            chat_session.mongo_id = mongo_id
            chat_session.is_synced_to_mongo = True
            chat_session.save(update_fields=["mongo_id", "is_synced_to_mongo"])

            return mongo_id

        except Exception as e:
            logger.error(f"Failed to sync chat session to MongoDB: {e}")
            return None
        finally:
            if client:
                client.close()

    @staticmethod
    def sync_chat_message_to_mongo(message: ChatMessage) -> Optional[str]:
        """
        Sync a chat message to MongoDB
        """
        if not MONGO_ENABLED:
            return None

        client = MongoSyncService.get_mongo_client()
        if not client:
            return None

        try:
            db = client[MONGO_DB]
            messages_collection = db.chat_messages

            # Ensure the session is synced first
            session_mongo_id = message.chat_session.mongo_id
            if not session_mongo_id:
                session_mongo_id = MongoSyncService.sync_chat_session_to_mongo(message.chat_session)
                if not session_mongo_id:
                    return None

            # Prepare message data
            message_data = {
                "django_id": str(message.pid),
                "session_id": session_mongo_id,
                "sender_id": str(message.sender.pid),
                "message_type": message.message_type,
                "content": message.content,
                "attachment_id": str(message.attachment.pid) if message.attachment else None,
                "is_ai": message.is_ai,
                "is_system": message.is_system,
                "is_read_by_client": message.is_read_by_client,
                "is_read_by_consultant": message.is_read_by_consultant,
                "read_at": message.read_at,
                "created_at": message.created_at,
                "updated_at": message.updated_at,
                "is_active": message.is_active,
                "is_deleted": message.is_deleted,
                "is_failed": message.is_failed,
                "failure_reason": message.failure_reason,
            }

            # If message already exists in MongoDB, update it
            if message.mongo_id:
                result = messages_collection.update_one({"_id": ObjectId(message.mongo_id)}, {"$set": message_data})

                if result.modified_count == 0:
                    # If not found, insert as new
                    result = messages_collection.insert_one(message_data)
                    mongo_id = str(result.inserted_id)

                    # Update Django model with MongoDB ID
                    message.mongo_id = mongo_id
                    message.is_synced_to_mongo = True
                    message.save(update_fields=["mongo_id", "is_synced_to_mongo"])

                    return mongo_id

                return message.mongo_id

            # Insert new message
            result = messages_collection.insert_one(message_data)
            mongo_id = str(result.inserted_id)

            # Update Django model with MongoDB ID
            message.mongo_id = mongo_id
            message.is_synced_to_mongo = True
            message.save(update_fields=["mongo_id", "is_synced_to_mongo"])

            return mongo_id

        except Exception as e:
            logger.error(f"Failed to sync chat message to MongoDB: {e}")
            return None
        finally:
            if client:
                client.close()

    @staticmethod
    def sync_from_mongo_to_django():
        """
        Sync data from MongoDB to Django (for background job)
        """
        if not MONGO_ENABLED:
            return

        client = MongoSyncService.get_mongo_client()
        if not client:
            return

        try:
            db = client[MONGO_DB]

            # Sync messages first
            messages_collection = db.chat_messages
            unsynced_messages = messages_collection.find({"is_synced_to_django": {"$ne": True}})

            for mongo_message in unsynced_messages:
                # Find the corresponding Django message
                try:
                    django_id = mongo_message.get("django_id")
                    if django_id:
                        message = ChatMessage.objects.get(pid=django_id)

                        # Update fields
                        message.content = mongo_message.get("content", message.content)
                        message.is_read_by_client = mongo_message.get("is_read_by_client", message.is_read_by_client)
                        message.is_read_by_consultant = mongo_message.get(
                            "is_read_by_consultant", message.is_read_by_consultant
                        )
                        message.read_at = mongo_message.get("read_at", message.read_at)
                        message.is_failed = mongo_message.get("is_failed", message.is_failed)
                        message.failure_reason = mongo_message.get("failure_reason", message.failure_reason)
                        message.is_deleted = mongo_message.get("is_deleted", message.is_deleted)

                        message.save()

                        # Mark as synced in MongoDB
                        messages_collection.update_one({"_id": mongo_message["_id"]}, {"$set": {"is_synced_to_django": True}})
                except ChatMessage.DoesNotExist:
                    # Message exists in MongoDB but not in Django
                    # This is a rare case that needs handling
                    logger.warning(f"Message with ID {django_id} exists in MongoDB but not in Django")
                except Exception as e:
                    logger.error(f"Error syncing message from MongoDB: {e}")

            # Sync sessions
            sessions_collection = db.chat_sessions
            unsynced_sessions = sessions_collection.find({"is_synced_to_django": {"$ne": True}})

            for mongo_session in unsynced_sessions:
                try:
                    django_id = mongo_session.get("django_id")
                    if django_id:
                        session = ChatSession.objects.get(pid=django_id)

                        # Update fields
                        session.status = mongo_session.get("status", session.status)
                        session.unread_client_messages = mongo_session.get(
                            "unread_client_messages", session.unread_client_messages
                        )
                        session.unread_consultant_messages = mongo_session.get(
                            "unread_consultant_messages", session.unread_consultant_messages
                        )
                        session.total_messages = mongo_session.get("total_messages", session.total_messages)
                        session.end_time = mongo_session.get("end_time", session.end_time)
                        session.is_deleted = mongo_session.get("is_deleted", session.is_deleted)

                        session.save()

                        # Mark as synced in MongoDB
                        sessions_collection.update_one({"_id": mongo_session["_id"]}, {"$set": {"is_synced_to_django": True}})
                except ChatSession.DoesNotExist:
                    logger.warning(f"Session with ID {django_id} exists in MongoDB but not in Django")
                except Exception as e:
                    logger.error(f"Error syncing session from MongoDB: {e}")

        except Exception as e:
            logger.error(f"Failed to sync from MongoDB to Django: {e}")
        finally:
            if client:
                client.close()
