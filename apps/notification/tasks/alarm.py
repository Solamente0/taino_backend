from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import timedelta
from django.utils import timezone

from apps.court_calendar.models import CourtCalendarEvent
from apps.court_calendar.services.enums import CourtCalendarEventTypeEnum
from apps.notification.services.alarm import NotificationService
from base_utils.jalali import gregorian_to_jalali

logger = get_task_logger(__name__)


@shared_task(bind=True)
def send_calendar_reminder_notifications_task(self):
    """
    تسک ارسال یادآوری برای رویدادهای تقویم قضایی:
    - برای رویدادهای نوع جلسه: ارسال یادآوری یک روز قبل
    - برای رویدادهای اعتراض و تبادل لوایح: ارسال یادآوری سه روز مانده به مهلت
    """
    try:
        now = timezone.now()
        total_notifications = 0

        # جلسات فردا
        tomorrow = now + timedelta(days=1)
        tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)

        meeting_events = CourtCalendarEvent.objects.filter(
            event_type=CourtCalendarEventTypeEnum.MEETING,
            start_datetime__gte=tomorrow_start,
            start_datetime__lte=tomorrow_end,
            is_deleted=False,
        )

        # یادآوری جلسات
        for event in meeting_events:
            if not hasattr(event, "case") or not event.case:
                continue

            case = event.case
            client_name = event.client.full_name if hasattr(event.client, "full_name") else event.get_client_name

            desc = f"یادآوری جلسه رسیدگی فردا پرونده {case.case_subject} موکل {client_name} شعبه {event.review_branch} زمان {gregorian_to_jalali(event.start_datetime)}"

            # ارسال به وکیل اصلی
            NotificationService.create_notification(
                to_user=event.owner,
                name=f"یادآوری جلسه: {event.title}",
                description=desc,
                link=f"/?events={event.pid}",
            )
            total_notifications += 1

            # ارسال به وکیل دوم
            if event.second_lawyer:
                NotificationService.create_notification(
                    to_user=event.second_lawyer,
                    name=f"یادآوری جلسه: {event.title}",
                    description=desc,
                    link=f"/?events={event.pid}",
                )
                total_notifications += 1

            # ارسال به سایر مشارکت‌کنندگان
            for participant in event.participants.all():
                if participant != event.owner and participant != getattr(event, "second_lawyer", None):
                    NotificationService.create_notification(
                        to_user=participant,
                        name=f"یادآوری جلسه: {event.title}",
                        description=desc,
                        link=f"/?events={event.pid}",
                    )
                    total_notifications += 1

            logger.info(f"یادآوری جلسه برای رویداد {event.pid} ارسال شد")

        # سررسیدهای سه روز آینده (اعتراض و تبادل لوایح)
        three_days_later = now + timedelta(days=3)
        three_days_later_date = three_days_later.date()

        deadline_events = CourtCalendarEvent.objects.filter(
            event_type__in=[CourtCalendarEventTypeEnum.OBJECTION, CourtCalendarEventTypeEnum.EXCHANGE],
            deadline__date=three_days_later_date,
            is_deleted=False,
        )

        # یادآوری سررسیدها
        for event in deadline_events:
            if not hasattr(event, "case") or not event.case:
                continue

            case = event.case
            client_name = event.client.full_name if hasattr(event.client, "full_name") else event.get_client_name

            if event.event_type == CourtCalendarEventTypeEnum.OBJECTION:
                desc = f"سه روز مانده به انقضا مهلت {event.objection_type} پرونده {case.case_subject} موکل {client_name} شعبه {event.review_branch}"
            elif event.event_type == CourtCalendarEventTypeEnum.EXCHANGE:
                desc = f"سه روز مانده به انقضا مهلت {event.exchange_type} پرونده {case.case_subject} موکل {client_name} شعبه {event.review_branch}"
            else:
                desc = ""

            if desc:
                # ارسال به وکیل اصلی
                NotificationService.create_notification(
                    to_user=event.owner,
                    name=f"یادآوری مهلت: {event.title}",
                    description=desc,
                    link=f"/?events={event.pid}",
                )
                total_notifications += 1

                # ارسال به وکیل دوم
                if event.second_lawyer:
                    NotificationService.create_notification(
                        to_user=event.second_lawyer,
                        name=f"یادآوری مهلت: {event.title}",
                        description=desc,
                        link=f"/?events={event.pid}",
                    )
                    total_notifications += 1

                # ارسال به سایر مشارکت‌کنندگان
                for participant in event.participants.all():
                    if participant != event.owner and participant != getattr(event, "second_lawyer", None):
                        NotificationService.create_notification(
                            to_user=participant,
                            name=f"یادآوری مهلت: {event.title}",
                            description=desc,
                            link=f"/?events={event.pid}",
                        )
                        total_notifications += 1

                logger.info(f"یادآوری مهلت برای رویداد {event.pid} ارسال شد")

        return {
            "meeting_notifications": len(meeting_events),
            "deadline_notifications": len(deadline_events),
            "total_notifications": total_notifications,
        }

    except Exception as exc:
        logger.error(f"خطا در تسک ارسال یادآوری رویدادها: {exc}")
        self.retry(exc=exc, countdown=300, max_retries=3)
