import logging
from typing import Optional, Dict, Any, Tuple, List

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.court_calendar.models import CourtCalendarEvent
from apps.lawyer_office.models import Client, LawOfficeCase
from apps.messaging.models import SMSMessage, SMSBalance, SystemSMSTemplate, SMSPackage
from apps.messaging.services.sms import TainoSMSHandler
from apps.setting.services.query import GeneralSettingsQuery
from apps.wallet.models import Transaction
from apps.wallet.services.wallet import WalletService

User = get_user_model()
logger = logging.getLogger(__name__)


class SMSService:
    """
    Service class for SMS-related operations
    """

    # IDs de plantilla constantes
    COURT_SESSION_TEMPLATE_ID = "579080"
    DEADLINE_TEMPLATE_ID = "832945"

    @staticmethod
    def check_user_sms_balance(user: User) -> int:
        """
        Check the SMS balance for a user

        Args:
            user: The user to check the balance for

        Returns:
            int: The user's SMS balance
        """
        balance, created = SMSBalance.objects.get_or_create(user=user)
        return balance.balance

    @staticmethod
    def add_sms_balance(user: User, amount: int) -> int:
        """
        Add SMS credits to a user's balance

        Args:
            user: The user to add the balance for
            amount: The number of SMS credits to add

        Returns:
            int: The updated SMS balance
        """
        balance, created = SMSBalance.objects.get_or_create(user=user)
        balance.add_balance(amount)
        return balance.balance

    @staticmethod
    def purchase_sms_with_coins(user: User, coins: int) -> Tuple[bool, int, str]:
        """
        Purchase SMS messages using coins

        Args:
            user: The user making the purchase
            coins: The number of coins to spend

        Returns:
            Tuple[bool, int, str]: Success status, SMS quantity purchased, message
        """
        # Each coin gives 10 SMS messages
        sms_package = SMSPackage.objects.filter(coin_cost=coins).first()
        if sms_package:
            sms_quantity = sms_package.value
        else:
            raise ValidationError("این بخش غیر فعال است!")
        # Check if user has enough coins (implementation depends on your coin system)
        user_has_enough_coins = user.wallet.coin_balance > int(coins)

        if not user_has_enough_coins:
            return False, 0, "موجودی ناکافی"

        # Create SMS purchase record
        from apps.messaging.models import SMSPurchase

        purchase = SMSPurchase.objects.create(user=user, coins_spent=coins, sms_quantity=sms_quantity)

        # Purchase record automatically adds balance through save method
        new_balance = SMSService.check_user_sms_balance(user)

        tr = WalletService.use_coins(
            user=user,
            coin_amount=coins,
            description=f"خرید {sms_quantity} پیامک با {coins} سکه",
            reference_id=f"sms_buying",
        )

        return True, sms_quantity, f"Successfully purchased {sms_quantity} SMS messages"

    @staticmethod
    def send_sms(
        user: User,
        recipient_number: str,
        message_content: str,
        recipient_name: Optional[str] = None,
        client: Optional[Client] = None,
        case: Optional[LawOfficeCase] = None,
        calendar_event: Optional[CourtCalendarEvent] = None,
        source_type: str = "manual",
    ) -> Tuple[bool, SMSMessage]:
        """
        Send an SMS message

        Args:
            user: The user sending the message
            recipient_number: The recipient's phone number
            message_content: The content of the message
            recipient_name: The recipient's name (optional)
            client: Related client (optional)
            case: Related case (optional)
            calendar_event: Related calendar event (optional)
            source_type: Source type of the message

        Returns:
            Tuple[bool, SMSMessage]: Success status and the created message object
        """
        # Create message record
        message = SMSMessage.objects.create(
            sender=user,
            creator=user,
            recipient_number=recipient_number,
            recipient_name=recipient_name,
            content=message_content,
            client=client,
            case=case,
            calendar_event=calendar_event,
            source_type=source_type,
        )

        # Check if user has sufficient SMS balance
        balance, created = SMSBalance.objects.get_or_create(user=user)
        cost_per_message = GeneralSettingsQuery.get_message_cost()
        if balance.balance <= 0:
            message.status = "insufficient_balance"
            message.save()
            return False, message

        # Deduct from balance
        if not balance.deduct_balance(cost_per_message):
            message.status = "insufficient_balance"
            message.save()
            return False, message
        with transaction.atomic:
            tr = Transaction.objects.create(
                wallet=None,
                amount=0,
                coin_amount=0,
                sms_amount=cost_per_message,
                type="sms_usage",
                status="completed",
                reference_id="",
                description=f"کسر {cost_per_message} پیامک",
                exchange_rate=0,
            )
        # Send SMS using existing handler
        try:
            # Extract country code - assuming Iranian numbers for simplicity
            # You might need more sophisticated handling for international numbers
            dial_code = "98"

            # Clean phone number (remove leading zeros or +98)
            clean_number = recipient_number
            if clean_number.startswith("+98"):
                clean_number = clean_number[3:]
            elif clean_number.startswith("0"):
                clean_number = clean_number[1:]

            # Send SMS - send direct sms
            success = TainoSMSHandler.send_template_code(
                dial_code=dial_code,
                phone_number=clean_number,
                params=[{"name": "message", "value": message_content}],
                template_id="generic_template_id",  # Este sería un template genérico que sólo muestra el mensaje
            )

            # Update message status
            if success:
                message.status = "sent"
                message.sent_at = timezone.now()
            else:
                message.status = "failed"
                message.error_message = "Failed to send SMS"

            message.save()
            return success, message

        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            message.status = "failed"
            message.error_message = str(e)
            message.save()
            return False, message

    @staticmethod
    def send_template_sms(
        user: User,
        template_id: str,
        recipient_number: str,
        params: List[Dict[str, Any]],
        recipient_name: Optional[str] = None,
        client: Optional[Client] = None,
        case: Optional[LawOfficeCase] = None,
        calendar_event: Optional[CourtCalendarEvent] = None,
        source_type: str = "manual",
    ) -> Tuple[bool, SMSMessage]:
        """
        Send SMS using SMS.ir template system with parameters

        Args:
            user: The user sending the message
            template_id: The ID of the template to use from SMS.ir
            recipient_number: The recipient's phone number
            params: Parameters for the template in format [{"name": "NAME", "value": "VALUE"}]
            recipient_name: The recipient's name (optional)
            client: Related client (optional)
            case: Related case (optional)
            calendar_event: Related calendar event (optional)
            source_type: Source type of the message

        Returns:
            Tuple[bool, SMSMessage]: Success status and the created message object
        """
        # Create a preview of the message for our records
        # This is just for our database, actual content is handled by SMS.ir template
        preview_content = f"Template ID: {template_id} with params: {params}"

        # Create message record
        message = SMSMessage.objects.create(
            sender=user,
            creator=user,
            recipient_number=recipient_number,
            recipient_name=recipient_name,
            content=preview_content,
            client=client,
            case=case,
            calendar_event=calendar_event,
            source_type=source_type,
        )

        # Check if user has sufficient SMS balance
        balance, created = SMSBalance.objects.get_or_create(user=user)

        if balance.balance <= 0:
            message.status = "insufficient_balance"
            message.save()
            return False, message

        # Deduct from balance
        if not balance.deduct_balance(1):
            message.status = "insufficient_balance"
            message.save()
            return False, message

        # Send SMS using template
        try:
            # Extract country code - assuming Iranian numbers for simplicity
            dial_code = "98"

            # Clean phone number (remove leading zeros or +98)
            clean_number = recipient_number
            if clean_number.startswith("+98"):
                clean_number = clean_number[3:]
            elif clean_number.startswith("0"):
                clean_number = clean_number[1:]

            # Send SMS using SMS.ir template system
            success = TainoSMSHandler.send_template_code(
                dial_code=dial_code,
                phone_number=clean_number,
                params=params,
                template_id=template_id,
            )

            # Update message status
            if success:
                message.status = "sent"
                message.sent_at = timezone.now()
            else:
                message.status = "failed"
                message.error_message = "Failed to send template SMS"

            message.save()
            return success, message

        except Exception as e:
            logger.error(f"Error sending template SMS: {e}")
            message.status = "failed"
            message.error_message = str(e)
            message.save()
            return False, message

    @staticmethod
    def send_sms_with_template(
        user: User,
        template_code: str,
        recipient_number: str,
        context: Dict[str, Any],
        recipient_name: Optional[str] = None,
        client: Optional[Client] = None,
        case: Optional[LawOfficeCase] = None,
        calendar_event: Optional[CourtCalendarEvent] = None,
        source_type: str = "manual",
    ) -> Tuple[bool, SMSMessage]:
        """
        Send an SMS using a template

        Args:
            user: The user sending the message
            template_code: The code of the template to use
            recipient_number: The recipient's phone number
            context: Context variables for the template
            recipient_name: The recipient's name (optional)
            client: Related client (optional)
            case: Related case (optional)
            calendar_event: Related calendar event (optional)
            source_type: Source type of the message

        Returns:
            Tuple[bool, SMSMessage]: Success status and the created message object
        """
        try:
            # Get template
            template = SystemSMSTemplate.objects.get(code=template_code, is_active=True)

            # Format template with context
            message_content = template.template_content
            for key, value in context.items():
                placeholder = "{" + key + "}"
                message_content = message_content.replace(placeholder, str(value))

            # Send formatted message
            return SMSService.send_sms(
                user=user,
                recipient_number=recipient_number,
                message_content=message_content,
                recipient_name=recipient_name,
                client=client,
                case=case,
                calendar_event=calendar_event,
                source_type=source_type,
            )

        except SystemSMSTemplate.DoesNotExist:
            logger.error(f"SMS template with code {template_code} not found")

            # Create error message record
            message = SMSMessage.objects.create(
                sender=user,
                creator=user,
                recipient_number=recipient_number,
                recipient_name=recipient_name,
                content=f"Failed to send: Template {template_code} not found",
                client=client,
                case=case,
                calendar_event=calendar_event,
                source_type=source_type,
                status="failed",
                error_message=f"Template {template_code} not found",
            )

            return False, message

        except Exception as e:
            logger.error(f"Error sending SMS with template: {e}")

            # Create error message record
            message = SMSMessage.objects.create(
                sender=user,
                creator=user,
                recipient_number=recipient_number,
                recipient_name=recipient_name,
                content=f"Failed to send: {str(e)}",
                client=client,
                case=case,
                calendar_event=calendar_event,
                source_type=source_type,
                status="failed",
                error_message=str(e),
            )

            return False, message

    @staticmethod
    def send_court_session_reminder(event: CourtCalendarEvent) -> Tuple[bool, Optional[SMSMessage]]:
        """
        Send a court session reminder SMS

        Args:
            event: The calendar event to send a reminder for

        Returns:
            Tuple[bool, Optional[SMSMessage]]: Success status and the created message object (if any)
        """
        from base_utils.jalali import gregorian_to_jalali

        # Check if we have a client with a phone number
        if not event.client or not hasattr(event.client, "phone_number") or not event.client.phone_number:
            logger.warning(f"No client or phone number for event {event.pid}")
            return False, None

        # Check if owner has SMS balance
        if SMSService.check_user_sms_balance(event.owner) <= 0:
            logger.warning(f"Insufficient SMS balance for user {event.owner.pid}")
            return False, None

        # Prepare formatted date/time
        if event.start_datetime:
            formatted_time = event.start_datetime.strftime("%H:%M")
        else:
            formatted_time = ""

        # Get case type/subject
        case_type = ""
        if event.case and hasattr(event.case, "case_subject"):
            case_type = event.case.case_subject

        # Get client name
        client_name = event.get_client_name or ""

        # Get branch reference
        branch_ref = event.review_branch or ""

        # Format datetime for SMS template
        datetime_str = ""
        if event.start_datetime:
            # datetime_str = event.start_datetime.strftime("%Y/%m/%d %H:%M")
            datetime_str = gregorian_to_jalali(event.start_datetime)

        # Prepare parameters for SMS.ir template
        params = [
            {"name": "CASE_TYPE", "value": case_type},
            {"name": "CLIENT_NAME", "value": client_name},
            {"name": "BRANCH_REF", "value": branch_ref},
            {"name": "DATETIME", "value": datetime_str},
        ]

        # Send SMS using template
        return SMSService.send_template_sms(
            user=event.owner,
            template_id=SMSService.COURT_SESSION_TEMPLATE_ID,
            recipient_number=event.owner.phone_number,
            params=params,
            recipient_name=client_name,
            client=event.client,
            case=event.case,
            calendar_event=event,
            source_type="auto_court_session",
        )

    @staticmethod
    def send_objection_deadline_reminder(event: CourtCalendarEvent) -> Tuple[bool, Optional[SMSMessage]]:
        """
        Send an objection deadline reminder SMS

        Args:
            event: The calendar event to send a reminder for

        Returns:
            Tuple[bool, Optional[SMSMessage]]: Success status and the created message object (if any)
        """
        # Check if we have a client with a phone number
        if not event.client or not hasattr(event.client, "phone_number") or not event.client.phone_number:
            logger.warning(f"No client or phone number for event {event.pid}")
            return False, None

        # Check if owner has SMS balance
        if SMSService.check_user_sms_balance(event.owner) <= 0:
            logger.warning(f"Insufficient SMS balance for user {event.owner.pid}")
            return False, None

        # Get objection type display name
        objection_type_display = event.get_objection_type_display() if hasattr(event, "get_objection_type_display") else ""
        if not objection_type_display and event.objection_type:
            # Fallback if display method not available
            from apps.court_calendar.services.enums import ObjectionStatusEnum

            objection_types = dict(ObjectionStatusEnum.choices)
            objection_type_display = objection_types.get(event.objection_type, "")

        # Get case type/subject
        case_type = ""
        if event.case and hasattr(event.case, "case_subject"):
            case_type = event.case.case_subject

        # Get client name
        client_name = event.get_client_name or ""

        # Get branch reference
        branch_ref = event.review_branch or event.issuing_branch or ""

        # Prepare parameters for SMS.ir template
        params = [
            {"name": "OBJECTION_TYPE", "value": objection_type_display},
            {"name": "CASE_TYPE", "value": case_type},
            {"name": "CLIENT_NAME", "value": client_name},
            {"name": "BRANCH_REF", "value": branch_ref},
        ]

        # Send SMS using template
        return SMSService.send_template_sms(
            user=event.owner,
            template_id=SMSService.DEADLINE_TEMPLATE_ID,
            recipient_number=event.owner.phone_number,
            params=params,
            recipient_name=client_name,
            client=event.client,
            case=event.case,
            calendar_event=event,
            source_type="auto_objection",
        )

    @staticmethod
    def send_exchange_deadline_reminder(event: CourtCalendarEvent) -> Tuple[bool, Optional[SMSMessage]]:
        """
        Send an exchange deadline reminder SMS

        Args:
            event: The calendar event to send a reminder for

        Returns:
            Tuple[bool, Optional[SMSMessage]]: Success status and the created message object (if any)
        """
        # Check if we have a client with a phone number
        if not event.client or not hasattr(event.client, "phone_number") or not event.client.phone_number:
            logger.warning(f"No client or phone number for event {event.pid}")
            return False, None

        # Check if owner has SMS balance
        if SMSService.check_user_sms_balance(event.owner) <= 0:
            logger.warning(f"Insufficient SMS balance for user {event.owner.pid}")
            return False, None

        # Get exchange type display name
        exchange_type_display = event.get_exchange_type_display() if hasattr(event, "get_exchange_type_display") else ""
        if not exchange_type_display and event.exchange_type:
            # Fallback if display method not available
            from apps.court_calendar.services.enums import ExchangeTypeEnum

            exchange_types = dict(ExchangeTypeEnum.choices)
            exchange_type_display = exchange_types.get(event.exchange_type, "")

        # Get case type/subject
        case_type = ""
        if event.case and hasattr(event.case, "case_subject"):
            case_type = event.case.case_subject

        # Get client name
        client_name = event.get_client_name or ""

        # Get branch reference
        branch_ref = event.review_branch or event.issuing_branch or ""

        # Prepare parameters for SMS.ir template - Using the same template ID as objection
        # but with OBJECTION_TYPE replaced by exchange type
        params = [
            {"name": "OBJECTION_TYPE", "value": exchange_type_display},  # Reusing the same parameter
            {"name": "CASE_TYPE", "value": case_type},
            {"name": "CLIENT_NAME", "value": client_name},
            {"name": "BRANCH_REF", "value": branch_ref},
        ]

        # Send SMS using template
        return SMSService.send_template_sms(
            user=event.owner,
            template_id=SMSService.DEADLINE_TEMPLATE_ID,
            recipient_number=event.owner.phone_number,
            params=params,
            recipient_name=client_name,
            client=event.client,
            case=event.case,
            calendar_event=event,
            source_type="auto_exchange",
        )
