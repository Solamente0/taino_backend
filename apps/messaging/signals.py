import logging
from datetime import timedelta, datetime, time

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.court_calendar.models import CourtCalendarEvent, CourtCalendarReminder
from apps.court_calendar.services.enums import CourtCalendarEventTypeEnum
from apps.messaging.services.sms_service import SMSService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CourtCalendarEvent)
def handle_calendar_event_created(sender, instance, created, **kwargs):
    """
    When a calendar event is created, schedule SMS reminders based on event type
    """
    print(f"here started 20", flush=True)
    if created and instance.client and hasattr(instance.client, "phone_number") and instance.client.phone_number:
        # For court sessions, schedule SMS reminder for the day before
        if instance.event_type == CourtCalendarEventTypeEnum.MEETING and instance.start_datetime:
            try:
                event_date = instance.start_datetime.date()
                reminder_date = event_date - timedelta(days=1)

                # TODO: For testing you might want to send immediately
                # SMSService.send_court_session_reminder(instance)

                # # TODO: In production
                # from apps.messaging.tasks.sms import send_court_session_reminder_task
                #
                # send_court_session_reminder_task.apply_async(
                #     kwargs={"event_id": instance.id}, eta=datetime.combine(reminder_date, time(9, 0))
                # )

                logger.info(f"Scheduled court session reminder SMS for event {instance.pid} - to be sent on {reminder_date}")
            except Exception as e:
                logger.error(f"Error scheduling court session reminder SMS: {e}")

        # For objection deadlines, schedule SMS reminder 3 days before the deadline
        elif instance.event_type == CourtCalendarEventTypeEnum.OBJECTION and instance.deadline:
            try:
                deadline_date = instance.deadline.date()
                reminder_date = deadline_date - timedelta(days=3)

                # TODO: For Testing/Development
                # SMSService.send_objection_deadline_reminder(instance)

                # TODO: In production
                # from apps.messaging.tasks.sms import send_objection_deadline_reminders_task
                #
                # # Similar to above
                # send_objection_deadline_reminders_task.delay(instance.id)
                # logger.info(
                #     f"Scheduled objection deadline reminder SMS for event {instance.pid} - to be sent on {reminder_date}"
                # )
            except Exception as e:
                logger.error(f"Error scheduling objection deadline reminder SMS: {e}")

        # For exchange deadlines, schedule SMS reminder 3 days before the deadline
        elif instance.event_type == CourtCalendarEventTypeEnum.EXCHANGE and instance.deadline:
            try:
                deadline_date = instance.deadline.date()
                reminder_date = deadline_date - timedelta(days=3)

                # TODO: FOR TESTING
                # SMSService.send_exchange_deadline_reminder(instance)

                # # TODO: In production
                # from apps.messaging.tasks.sms import send_exchange_deadline_reminders_task
                #
                # # Similar to above
                # send_exchange_deadline_reminders_task.delay(instance.id)
                # logger.info(
                #     f"Scheduled exchange deadline reminder SMS for event {instance.pid} - to be sent on {reminder_date}"
                # )
            except Exception as e:
                logger.error(f"Error scheduling exchange deadline reminder SMS: {e}")


#
# @receiver(post_save, sender=CourtCalendarReminder)
# def handle_calendar_reminder_triggered(sender, instance, **kwargs):
#     """
#     When a calendar reminder is triggered, send SMS if appropriate
#     """
#     # If the reminder is marked as sent and needs SMS
#     if instance.is_sent and instance.sms_reminder:
#         try:
#             # Get the event
#             event = instance.event
#
#             # Only send SMS if event has a client with a phone number
#             if event.owner and hasattr(event.owner, "phone_number") and event.owner.phone_number:
#                 # Check event type and send appropriate reminder
#                 if event.event_type == CourtCalendarEventTypeEnum.MEETING:
#                     success, message = SMSService.send_court_session_reminder(event)
#                     if success:
#                         logger.info(f"Successfully sent court session reminder SMS for event {event.pid}")
#                     else:
#                         logger.warning(f"Failed to send court session reminder SMS for event {event.pid}")
#
#                 elif event.event_type == CourtCalendarEventTypeEnum.OBJECTION:
#                     success, message = SMSService.send_objection_deadline_reminder(event)
#                     if success:
#                         logger.info(f"Successfully sent objection deadline reminder SMS for event {event.pid}")
#                     else:
#                         logger.warning(f"Failed to send objection deadline reminder SMS for event {event.pid}")
#
#                 elif event.event_type == CourtCalendarEventTypeEnum.EXCHANGE:
#                     success, message = SMSService.send_exchange_deadline_reminder(event)
#                     if success:
#                         logger.info(f"Successfully sent exchange deadline reminder SMS for event {event.pid}")
#                     else:
#                         logger.warning(f"Failed to send exchange deadline reminder SMS for event {event.pid}")
#
#         except Exception as e:
#             logger.error(f"Error sending SMS for calendar reminder {instance.pid}: {e}")
