import django_filters
from django.db.models import Q

from apps.case.models import (
    Case,
    Session,
    Assessment,
    DailyLog,
    CaseDocument,
)


class CaseFilter(django_filters.FilterSet):
    """
    فیلتر برای پرونده‌ها
    """
    status = django_filters.MultipleChoiceFilter(
        choices=Case._meta.get_field('status').choices
    )
    case_type = django_filters.MultipleChoiceFilter(
        choices=Case._meta.get_field('case_type').choices
    )
    priority = django_filters.MultipleChoiceFilter(
        choices=Case._meta.get_field('priority').choices
    )
    assigned_counselor = django_filters.CharFilter(
        field_name='assigned_counselor__pid',
        lookup_expr='exact'
    )
    search = django_filters.CharFilter(method='search_filter')
    
    class Meta:
        model = Case
        fields = ['status', 'case_type', 'priority', 'assigned_counselor']
    
    def search_filter(self, queryset, name, value):
        """
        جستجو در شماره پرونده، نام کاربر، شکایت اولیه
        """
        return queryset.filter(
            Q(case_number__icontains=value) |
            Q(user__first_name__icontains=value) |
            Q(user__last_name__icontains=value) |
            Q(initial_complaint__icontains=value)
        )


class SessionFilter(django_filters.FilterSet):
    """
    فیلتر برای جلسات
    """
    case = django_filters.CharFilter(
        field_name='case__pid',
        lookup_expr='exact'
    )
    session_type = django_filters.MultipleChoiceFilter(
        choices=Session._meta.get_field('session_type').choices
    )
    status = django_filters.MultipleChoiceFilter(
        choices=Session._meta.get_field('status').choices
    )
    date_from = django_filters.DateTimeFilter(
        field_name='scheduled_datetime',
        lookup_expr='gte'
    )
    date_to = django_filters.DateTimeFilter(
        field_name='scheduled_datetime',
        lookup_expr='lte'
    )
    
    class Meta:
        model = Session
        fields = ['case', 'session_type', 'status']


class AssessmentFilter(django_filters.FilterSet):
    """
    فیلتر برای ارزیابی‌ها
    """
    case = django_filters.CharFilter(
        field_name='case__pid',
        lookup_expr='exact'
    )
    test_type = django_filters.MultipleChoiceFilter(
        choices=Assessment._meta.get_field('test_type').choices
    )
    severity_level = django_filters.MultipleChoiceFilter(
        choices=Assessment._meta.get_field('severity_level').choices
    )
    date_from = django_filters.DateFilter(
        field_name='date_taken',
        lookup_expr='gte'
    )
    date_to = django_filters.DateFilter(
        field_name='date_taken',
        lookup_expr='lte'
    )
    
    class Meta:
        model = Assessment
        fields = ['case', 'test_type', 'severity_level']


class DailyLogFilter(django_filters.FilterSet):
    """
    فیلتر برای ژورنال‌های روزانه
    """
    case = django_filters.CharFilter(
        field_name='case__pid',
        lookup_expr='exact'
    )
    date_from = django_filters.DateFilter(
        field_name='log_date',
        lookup_expr='gte'
    )
    date_to = django_filters.DateFilter(
        field_name='log_date',
        lookup_expr='lte'
    )
    
    class Meta:
        model = DailyLog
        fields = ['case']


class CaseDocumentFilter(django_filters.FilterSet):
    """
    فیلتر برای اسناد پرونده
    """
    case = django_filters.CharFilter(
        field_name='case__pid',
        lookup_expr='exact'
    )
    document_type = django_filters.MultipleChoiceFilter(
        choices=CaseDocument._meta.get_field('document_type').choices
    )
    
    class Meta:
        model = CaseDocument
        fields = ['case', 'document_type']
