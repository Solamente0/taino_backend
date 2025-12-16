from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta
from django.utils import timezone

from apps.court_calendar.models import CourtCalendarEvent
from apps.court_calendar.services.enums import CourtCalendarEventTypeEnum
from apps.messaging.services import TainoSMSHandler
from apps.messaging.services.sms_service import SMSService

logger = get_task_logger(__name__)


@shared_task(bind=True)
def send_verification_sms_task(self, dial_code, code, mobile_number):
    try:
        result = TainoSMSHandler.send_verification_code(dial_code=dial_code, code=code, phone_number=mobile_number)
        return result
    except Exception as exc:
        # https://docs.celeryq.dev/en/stable/userguide/tasks.html#retrying
        logger.warning(f"Exception occurred while sending sms: {exc}")
        self.retry(exc=exc, max_retries=1, countdown=5)


@shared_task(bind=True)
def send_sms_with_template_task(
    self,
    user_id,
    template_id,
    recipient_number,
    params,
    recipient_name=None,
    client_id=None,
    case_id=None,
    calendar_event_id=None,
    source_type="manual",
):
    """
    Task to send SMS using template
    """
    try:
        from django.contrib.auth import get_user_model
        from apps.lawyer_office.models import Client, LawOfficeCase

        User = get_user_model()

        # Get related objects if IDs are provided
        user = User.objects.get(id=user_id)
        client = Client.objects.get(id=client_id) if client_id else None
        case = LawOfficeCase.objects.get(id=case_id) if case_id else None
        calendar_event = CourtCalendarEvent.objects.get(id=calendar_event_id) if calendar_event_id else None

        # Send SMS
        success, message = SMSService.send_template_sms(
            user=user,
            template_id=template_id,
            recipient_number=recipient_number,
            params=params,
            recipient_name=recipient_name,
            client=client,
            case=case,
            calendar_event=calendar_event,
            source_type=source_type,
        )

        return {
            "success": success,
            "message_id": message.id if message else None,
            "status": message.status if message else None,
        }

    except Exception as exc:
        logger.error(f"Error in send_sms_with_template_task: {exc}")
        self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task(bind=True)
def send_court_session_reminder_task(self, event_id=None):
    """
    Task to send court session reminder SMS for upcoming events

    If event_id is provided, sends reminder for that specific event.
    Otherwise, finds all court sessions scheduled for tomorrow.
    """
    try:
        now = timezone.now()

        if event_id:
            # Send reminder for a specific event
            try:
                event = CourtCalendarEvent.objects.get(id=event_id, is_deleted=False)
                success, message = SMSService.send_court_session_reminder(event)
                return {"processed": 1, "sent": 1 if success else 0, "failed": 0 if success else 1}
            except CourtCalendarEvent.DoesNotExist:
                logger.error(f"Court calendar event with ID {event_id} not found")
                return {"processed": 0, "sent": 0, "failed": 1}
        else:
            # Find court sessions scheduled for tomorrow
            tomorrow = now + timedelta(days=1)
            tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)

            # Find court sessions scheduled for tomorrow
            court_sessions = CourtCalendarEvent.objects.filter(
                event_type=CourtCalendarEventTypeEnum.MEETING,
                start_datetime__gte=tomorrow_start,
                start_datetime__lte=tomorrow_end,
                is_deleted=False,
            )

            sent_count = 0
            failed_count = 0

            for event in court_sessions:
                success, message = SMSService.send_court_session_reminder(event)
                if success:
                    sent_count += 1
                    logger.info(f"Successfully sent court session reminder for event {event.pid}")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to send court session reminder for event {event.pid}")

            return {"processed": len(court_sessions), "sent": sent_count, "failed": failed_count}

    except Exception as exc:
        logger.error(f"Error in send_court_session_reminders_task: {exc}")
        self.retry(exc=exc, countdown=300, max_retries=3)


@shared_task(bind=True)
def send_court_session_reminder_for_event_task(self, event_id):
    """
    Task to send a court session reminder SMS for a specific event
    """
    try:
        try:
            event = CourtCalendarEvent.objects.get(id=event_id, is_deleted=False)
            success, message = SMSService.send_court_session_reminder(event)
            return {
                "event_id": event_id,
                "success": success,
                "message_id": message.id if message else None,
                "status": message.status if message else None,
            }
        except CourtCalendarEvent.DoesNotExist:
            logger.error(f"Court calendar event with ID {event_id} not found")
            return {"event_id": event_id, "success": False, "error": "Event not found"}

    except Exception as exc:
        logger.error(f"Error in send_court_session_reminder_for_event_task: {exc}")
        self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task(bind=True)
def send_objection_deadline_reminders_task(self, event_id=None):
    """
    Task to send objection deadline reminder SMS

    If event_id is provided, sends reminder for that specific event.
    Otherwise, finds all objection events with deadlines 3 days from now.
    """
    try:
        if event_id:
            try:
                event = CourtCalendarEvent.objects.get(id=event_id, is_deleted=False)
                success, message = SMSService.send_objection_deadline_reminder(event)
                return {"processed": 1, "sent": 1 if success else 0, "failed": 0 if success else 1}
            except CourtCalendarEvent.DoesNotExist:
                logger.error(f"Court calendar event with ID {event_id} not found")
                return {"processed": 0, "sent": 0, "failed": 1}
        else:
            now = timezone.now()
            three_days_later = now + timedelta(days=3)
            target_date = three_days_later.date()

            # Find objection events with deadlines 3 days from now
            objection_events = CourtCalendarEvent.objects.filter(
                event_type=CourtCalendarEventTypeEnum.OBJECTION, deadline__date=target_date, is_deleted=False
            )

            sent_count = 0
            failed_count = 0

            for event in objection_events:
                success, message = SMSService.send_objection_deadline_reminder(event)
                if success:
                    sent_count += 1
                    logger.info(f"Successfully sent objection deadline reminder for event {event.pid}")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to send objection deadline reminder for event {event.pid}")

            return {"processed": len(objection_events), "sent": sent_count, "failed": failed_count}

    except Exception as exc:
        logger.error(f"Error in send_objection_deadline_reminders_task: {exc}")
        self.retry(exc=exc, countdown=300, max_retries=3)


@shared_task(bind=True)
def send_objection_deadline_reminder_for_event_task(self, event_id):
    """
    Task to send an objection deadline reminder SMS for a specific event
    """
    try:
        try:
            event = CourtCalendarEvent.objects.get(id=event_id, is_deleted=False)
            success, message = SMSService.send_objection_deadline_reminder(event)
            return {
                "event_id": event_id,
                "success": success,
                "message_id": message.id if message else None,
                "status": message.status if message else None,
            }
        except CourtCalendarEvent.DoesNotExist:
            logger.error(f"Court calendar event with ID {event_id} not found")
            return {"event_id": event_id, "success": False, "error": "Event not found"}

    except Exception as exc:
        logger.error(f"Error in send_objection_deadline_reminder_for_event_task: {exc}")
        self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task(bind=True)
def send_exchange_deadline_reminders_task(self, event_id=None):
    """
    Task to send exchange deadline reminder SMS

    If event_id is provided, sends reminder for that specific event.
    Otherwise, finds all exchange events with deadlines 3 days from now.
    """
    try:
        if event_id:
            try:
                event = CourtCalendarEvent.objects.get(id=event_id, is_deleted=False)
                success, message = SMSService.send_exchange_deadline_reminder(event)
                return {"processed": 1, "sent": 1 if success else 0, "failed": 0 if success else 1}
            except CourtCalendarEvent.DoesNotExist:
                logger.error(f"Court calendar event with ID {event_id} not found")
                return {"processed": 0, "sent": 0, "failed": 1}
        else:
            now = timezone.now()
            three_days_later = now + timedelta(days=3)
            target_date = three_days_later.date()

            # Find exchange events with deadlines 3 days from now
            exchange_events = CourtCalendarEvent.objects.filter(
                event_type=CourtCalendarEventTypeEnum.EXCHANGE, deadline__date=target_date, is_deleted=False
            )

            sent_count = 0
            failed_count = 0

            for event in exchange_events:
                success, message = SMSService.send_exchange_deadline_reminder(event)
                if success:
                    sent_count += 1
                    logger.info(f"Successfully sent exchange deadline reminder for event {event.pid}")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to send exchange deadline reminder for event {event.pid}")

            return {"processed": len(exchange_events), "sent": sent_count, "failed": failed_count}

    except Exception as exc:
        logger.error(f"Error in send_exchange_deadline_reminders_task: {exc}")
        self.retry(exc=exc, countdown=300, max_retries=3)


@shared_task(bind=True)
def send_exchange_deadline_reminder_for_event_task(self, event_id):
    """
    Task to send an exchange deadline reminder SMS for a specific event
    """
    try:
        try:
            event = CourtCalendarEvent.objects.get(id=event_id, is_deleted=False)
            success, message = SMSService.send_exchange_deadline_reminder(event)
            return {
                "event_id": event_id,
                "success": success,
                "message_id": message.id if message else None,
                "status": message.status if message else None,
            }
        except CourtCalendarEvent.DoesNotExist:
            logger.error(f"Court calendar event with ID {event_id} not found")
            return {"event_id": event_id, "success": False, "error": "Event not found"}

    except Exception as exc:
        logger.error(f"Error in send_exchange_deadline_reminder_for_event_task: {exc}")
        self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task(bind=True)
def initialize_system_sms_templates_task(self):
    """
    Task to initialize the default system SMS templates
    """
    try:
        from apps.messaging.models import SystemSMSTemplate

        SystemSMSTemplate.initialize_default_templates()
        return {"status": "success", "message": "System SMS templates initialized"}

    except Exception as exc:
        logger.error(f"Error initializing system SMS templates: {exc}")
        self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task(bind=True)
def send_template_code_task(self, dial_code, phone_number, params, template_id):
    """
    Task to send an SMS using SMS.ir template system
    """
    try:
        result = TainoSMSHandler.send_template_code(
            dial_code=dial_code, phone_number=phone_number, params=params, template_id=template_id
        )
        return {"success": result}
    except Exception as exc:
        logger.error(f"Error in send_template_code_task: {exc}")
        self.retry(exc=exc, countdown=60, max_retries=3)
