# apps/ai_chat/services/ai_chat_service.py
import logging
from typing import Optional
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.ai_chat.models import AISession, AIMessage, AIMessageTypeEnum, AISessionStatusEnum
from apps.setting.services.query import GeneralSettingsQuery
from base_utils.services import AbstractBaseService
from base_utils.subscription import check_bypass_user_payment

User = get_user_model()
logger = logging.getLogger(__name__)


class AIChatService(AbstractBaseService):
    """
    Service for AI chat functionality
    """

    @staticmethod
    def charge_for_ai_chat(user: User, ai_type: str, duration_minutes: int = 6, use_coins: bool = True) -> bool:
        """Charge user for AI chat using pricing system"""

        # Map ai_type to feature
        feature_map = {
            "v": "ai_chat_v",
            "v_plus": "ai_chat_v_plus",
            "v_x": "ai_chat_v_x",
            "v_plus_pro": "ai_chat_v_plus_pro",
            "v_x_pro": "ai_chat_v_x_pro",
        }

        feature = feature_map.get(ai_type, "ai_chat_v")

        # Get pricing
        # success, message, details = PricingService.charge_user(
        #     user=user,
        #     feature=feature,
        #     use_coins=use_coins,
        #     description=f"گفتگوی هوش مصنوعی {ai_type.upper()} به مدت {duration_minutes} دقیقه",
        # )

        # return success
        return True

    @staticmethod
    def create_ai_session(
        user: User, ai_type: str = "v", title: str = None, duration_minutes: int = 6, use_coins: bool = True
    ) -> Optional[AISession]:
        """
        Create a new AI chat session
        """
        try:
            from apps.ai_chat.models import ChatAIConfig

            # Get AI config
            ai_config = ChatAIConfig.objects.filter(static_name=ai_type, is_active=True).first()

            if not ai_config:
                ai_config = ChatAIConfig.objects.filter(is_active=True, is_default=True).first()

            if not ai_config:
                logger.error("No active AI configuration found")
                return None

            # Calculate times
            start_date = timezone.now()
            end_date = start_date + timezone.timedelta(minutes=duration_minutes)

            # Get price
            price = GeneralSettingsQuery.get_ai_chat_price_by_type(ai_type)

            # Create session
            ai_session = AISession.objects.create(
                user=user,
                ai_type=ai_type,
                status=AISessionStatusEnum.ACTIVE,
                title=title or f"AI Chat {ai_type.upper()}",
                fee_amount=price,
                duration_minutes=duration_minutes,
                start_date=start_date,
                end_date=end_date,
                paid_with_coins=use_coins,
                ai_config=ai_config,
                creator=user,
                ai_context={
                    "config_id": str(ai_config.pid),
                    "model_name": ai_config.model_name,
                    "ai_type": ai_type,
                    "duration_minutes": duration_minutes,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "price": price,
                    "use_coins": use_coins,
                },
            )

            return ai_session

        except Exception as e:
            logger.error(f"Error creating AI session: {e}")
            return None

    @staticmethod
    def send_message(
        ai_session: AISession,
        sender: User,
        content: str,
        message_type: str = AIMessageTypeEnum.TEXT,
        is_ai: bool = False,
        is_system: bool = False,
    ) -> Optional[AIMessage]:
        """
        Send a message in an AI session
        """
        if ai_session.status != AISessionStatusEnum.ACTIVE:
            raise ValueError(f"Cannot send message to a {ai_session.status} AI session.")

        if sender != ai_session.user and not is_ai and not is_system:
            raise ValueError("Sender is not the session user.")

        # Check if session has expired
        if ai_session.end_date and ai_session.end_date < timezone.now():
            raise ValueError("AI session has expired.")

        message = AIMessage.objects.create(
            ai_session=ai_session,
            sender=sender,
            content=content,
            message_type=message_type,
            is_ai=is_ai,
            is_system=is_system,
        )

        return message

    @staticmethod
    def extend_ai_session(ai_session: AISession, additional_minutes: int, use_coins: bool = False) -> bool:
        """
        Extend an AI session's duration
        """
        try:
            if ai_session.status != AISessionStatusEnum.ACTIVE:
                return False

            if ai_session.end_date and ai_session.end_date < timezone.now():
                return False

            # Charge for extension
            charge_success = AIChatService.charge_for_ai_chat(
                user=ai_session.user, ai_type=ai_session.ai_type, duration_minutes=additional_minutes, use_coins=use_coins
            )

            if not charge_success:
                return False

            # Update end_date
            current_end_date = ai_session.end_date or (timezone.now() + timezone.timedelta(minutes=30))
            new_end_date = current_end_date + timezone.timedelta(minutes=additional_minutes)

            ai_session.end_date = new_end_date
            ai_session.duration_minutes += additional_minutes

            # Update context
            if ai_session.ai_context:
                ai_context = ai_session.ai_context
                ai_context["duration_minutes"] = ai_session.duration_minutes
                ai_context["end_date"] = new_end_date.isoformat()
                ai_context["use_coins_for_extension"] = use_coins
                ai_session.ai_context = ai_context

            ai_session.save(update_fields=["end_date", "duration_minutes", "ai_context"])

            # Create system message
            payment_method = "سکه" if use_coins else "ریال"
            AIChatService.send_message(
                ai_session=ai_session,
                sender=ai_session.user,
                content=f"جلسه گفتگو به مدت {additional_minutes} دقیقه دیگر با پرداخت {payment_method} تمدید شد",
                message_type=AIMessageTypeEnum.SYSTEM,
                is_system=True,
            )

            return True

        except Exception as e:
            logger.error(f"Error extending AI session: {e}")
            return False

    @staticmethod
    def end_ai_session(ai_session: AISession, reason: str = None) -> AISession:
        """
        End an active AI session
        """
        if ai_session.status != AISessionStatusEnum.ACTIVE:
            raise ValueError(f"Cannot end a {ai_session.status} AI session.")

        end_date = timezone.now()
        ai_session.end_date = end_date
        ai_session.status = AISessionStatusEnum.COMPLETED
        ai_session.save()

        # Create end message
        end_message = f"جلسه گفتگو با هوش مصنوعی پایان یافت."
        if reason:
            end_message += f" دلیل: {reason}"

        AIChatService.send_message(
            ai_session=ai_session,
            sender=ai_session.user,
            content=end_message,
            message_type=AIMessageTypeEnum.SYSTEM,
            is_system=True,
        )

        return ai_session
