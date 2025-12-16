from django.db.models import QuerySet, Count, Q, Avg
from apps.case.models import Case, Session, Assessment
from base_utils.services import AbstractBaseQuery


class CaseQuery(AbstractBaseQuery):
    """
    کوئری‌های پرونده
    """
    
    @staticmethod
    def get_user_cases(user, status=None):
        """
        دریافت پرونده‌های یک کاربر
        """
        queryset = Case.objects.filter(
            Q(user=user) | Q(partner=user)
        ).select_related('user', 'partner', 'assigned_counselor')
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    @staticmethod
    def get_counselor_cases(counselor, status=None):
        """
        دریافت پرونده‌های یک مشاور
        """
        queryset = Case.objects.filter(
            assigned_counselor=counselor
        ).select_related('user', 'partner')
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    @staticmethod
    def get_case_with_relations(case_id):
        """
        دریافت پرونده با تمام روابط
        """
        return Case.objects.select_related(
            'user',
            'partner',
            'assigned_counselor',
            'treatment_plan'
        ).prefetch_related(
            'sessions',
            'assessments',
            'daily_logs',
            'documents',
            'ai_analyses',
            'timeline_events',
            'treatment_plan__goals'
        ).get(pid=case_id)
    
    @staticmethod
    def get_active_cases():
        """
        دریافت پرونده‌های فعال
        """
        return Case.objects.filter(
            status="active",
            is_active=True
        )
    
    @staticmethod
    def search_cases(query_string):
        """
        جستجو در پرونده‌ها
        """
        return Case.objects.filter(
            Q(case_number__icontains=query_string) |
            Q(user__first_name__icontains=query_string) |
            Q(user__last_name__icontains=query_string) |
            Q(initial_complaint__icontains=query_string) |
            Q(tags__contains=[query_string])
        ).distinct()


class SessionQuery(AbstractBaseQuery):
    """
    کوئری‌های جلسات
    """
    
    @staticmethod
    def get_case_sessions(case, status=None):
        """
        دریافت جلسات یک پرونده
        """
        queryset = Session.objects.filter(case=case)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-scheduled_datetime')
    
    @staticmethod
    def get_completed_sessions_count(case):
        """
        تعداد جلسات انجام شده
        """
        return Session.objects.filter(
            case=case,
            status="completed"
        ).count()


class AssessmentQuery(AbstractBaseQuery):
    """
    کوئری‌های ارزیابی
    """
    
    @staticmethod
    def get_case_assessments(case, test_type=None):
        """
        دریافت ارزیابی‌های یک پرونده
        """
        queryset = Assessment.objects.filter(case=case)
        
        if test_type:
            queryset = queryset.filter(test_type=test_type)
        
        return queryset.order_by('-date_taken')
    
    @staticmethod
    def get_assessment_progress(case, test_type):
        """
        دریافت روند پیشرفت یک تست خاص
        """
        return Assessment.objects.filter(
            case=case,
            test_type=test_type
        ).order_by('date_taken').values('date_taken', 'raw_score')
