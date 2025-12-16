# apps/ai_support/tasks.py
import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from apps.ai_support.models import SupportSession, SupportMessage, SupportMessageTypeEnum
from apps.ai_support.services.ai_service import OpenRouterAIService

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, name="apps.ai_support.tasks.generate_ai_support_response")
def generate_ai_support_response(self, session_pid: str, user_message_pid: str):
    """
    Generate AI response for support message
    This task is called asynchronously via Celery
    """
    try:
        # Get session and message
        session = SupportSession.objects.get(pid=session_pid, is_deleted=False)
        user_message = SupportMessage.objects.get(pid=user_message_pid, is_deleted=False)
        
        # Generate AI response
        ai_response_text = OpenRouterAIService.generate_response(
            session=session,
            user_message=user_message.content
        )
        
        if not ai_response_text:
            logger.error("Failed to generate AI response")
            return {"status": "error", "message": "Failed to generate response"}
        
        # Create AI message
        ai_message = SupportMessage.objects.create(
            session=session,
            sender=session.user,  # AI messages use user as sender
            content=ai_response_text,
            message_type=SupportMessageTypeEnum.TEXT,
            is_ai=True
        )
        
        # Send via WebSocket
        channel_layer = get_channel_layer()
        room_group_name = f"support_{session_pid}"
        
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                "type": "support_message",
                "message": {
                    "id": str(ai_message.pid),
                    "sender": str(ai_message.sender.pid),
                    "sender_name": f"{ai_message.sender.first_name} {ai_message.sender.last_name}",
                    "content": ai_message.content,
                    "message_type": ai_message.message_type,
                    "timestamp": ai_message.created_at.isoformat(),
                    "is_ai": True,
                }
            }
        )
        
        return {
            "status": "success",
            "message_id": str(ai_message.pid),
            "content": ai_response_text
        }
        
    except SupportSession.DoesNotExist:
        logger.error(f"Support session {session_pid} not found")
        return {"status": "error", "message": "Session not found"}
    
    except SupportMessage.DoesNotExist:
        logger.error(f"Support message {user_message_pid} not found")
        return {"status": "error", "message": "Message not found"}
    
    except Exception as e:
        logger.error(f"Error generating AI support response: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
