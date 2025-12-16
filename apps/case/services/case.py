from django.contrib.auth import get_user_model
from apps.case.models import Case, CaseTimeline, TimelineEventType
from base_utils.services import AbstractBaseService

User = get_user_model()


class CaseService(AbstractBaseService):
    """
    سرویس برای مدیریت پرونده‌ها
    """
    
    @staticmethod
    def create_case(user, case_type, initial_complaint, **kwargs):
        """
        ایجاد پرونده جدید
        """
        case = Case.objects.create(
            user=user,
            case_type=case_type,
            initial_complaint=initial_complaint,
            **kwargs
        )
        
        # ثبت رویداد در تایم‌لاین
        CaseTimeline.objects.create(
            case=case,
            event_type=TimelineEventType.CASE_CREATED,
            title="ایجاد پرونده",
            description=f"پرونده {case.case_number} ایجاد شد",
            created_by=user,
            icon="📋",
            color="green"
        )
        
        return case
    
    @staticmethod
    def update_case_status(case, new_status, updated_by, reason=""):
        """
        بروزرسانی وضعیت پرونده
        """
        old_status = case.status
        case.status = new_status
        case.save(update_fields=['status', 'updated_at'])
        
        # ثبت در تایم‌لاین
        CaseTimeline.objects.create(
            case=case,
            event_type=TimelineEventType.CASE_STATUS_CHANGED,
            title="تغییر وضعیت پرونده",
            description=f"وضعیت از {old_status} به {new_status} تغییر کرد. {reason}",
            created_by=updated_by,
            metadata={"old_status": old_status, "new_status": new_status},
            icon="🔄",
            color="blue"
        )
        
        return case
    
    @staticmethod
    def close_case(case, closed_by, reason=""):
        """
        بستن پرونده
        """
        from django.utils import timezone
        
        case.status = "closed"
        case.close_date = timezone.now().date()
        case.save(update_fields=['status', 'close_date', 'updated_at'])
        
        CaseTimeline.objects.create(
            case=case,
            event_type=TimelineEventType.CASE_STATUS_CHANGED,
            title="بستن پرونده",
            description=f"پرونده بسته شد. دلیل: {reason}",
            created_by=closed_by,
            icon="🔒",
            color="red"
        )
        
        return case
    
    @staticmethod
    def add_timeline_event(case, event_type, title, description="", created_by=None, **kwargs):
        """
        افزودن رویداد به تایم‌لاین
        """
        return CaseTimeline.objects.create(
            case=case,
            event_type=event_type,
            title=title,
            description=description,
            created_by=created_by,
            **kwargs
        )
