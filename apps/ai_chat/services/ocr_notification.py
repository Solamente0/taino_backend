import logging
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class WebSocketNotificationService:
    """Service to send notifications via WebSocket"""

    @staticmethod
    def send_ocr_analysis_notification(ai_session_id, analysis_data):
        """
        Send OCR analysis completion notification to a specific chat session
        """
        try:
            channel_layer = get_channel_layer()
            room_group_name = f"chat_{ai_session_id}"

            # Create notification payload
            notification = {
                "type": "ocr_analysis_complete",  # Must match consumer method name
                "analysis": analysis_data.get("analysis", ""),
                "status": analysis_data.get("status", "completed"),
            }

            # Send message to room group
            async_to_sync(channel_layer.group_send)(room_group_name, notification)

            logger.info(f"Sent OCR analysis notification to {room_group_name}")
            return True
        except Exception as e:
            logger.error(f"Error sending OCR analysis notification: {e}")
            return False
