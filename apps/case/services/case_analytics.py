from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta


class CaseAnalytics:
    """
    تحلیل‌های آماری پرونده
    """
    
    @staticmethod
    def get_case_summary(case):
        """
        خلاصه آماری پرونده
        """
        from apps.case.models import Session, Assessment, DailyLog
        
        completed_sessions = Session.objects.filter(
            case=case,
            status="completed"
        ).count()
        
        total_assessments = Assessment.objects.filter(case=case).count()
        
        daily_logs_count = DailyLog.objects.filter(case=case).count()
        
        # میانگین mood از ژورنال‌های 30 روز اخیر
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        avg_mood = DailyLog.objects.filter(
            case=case,
            log_date__gte=thirty_days_ago,
            mood_score__isnull=False
        ).aggregate(avg=Avg('mood_score'))['avg']
        
        return {
            "completed_sessions": completed_sessions,
            "total_assessments": total_assessments,
            "daily_logs_count": daily_logs_count,
            "avg_mood_30days": round(avg_mood, 2) if avg_mood else None,
            "progress_percentage": case.progress_percentage,
        }
    
    @staticmethod
    def get_mood_trend(case, days=30):
        """
        روند خلق و خو
        """
        from apps.case.models import DailyLog
        
        start_date = timezone.now().date() - timedelta(days=days)
        
        logs = DailyLog.objects.filter(
            case=case,
            log_date__gte=start_date,
            mood_score__isnull=False
        ).order_by('log_date').values('log_date', 'mood_score')
        
        return list(logs)
    
    @staticmethod
    def get_assessment_trends(case, test_type):
        """
        روند نمرات یک تست خاص
        """
        from apps.case.models import Assessment
        
        assessments = Assessment.objects.filter(
            case=case,
            test_type=test_type,
            raw_score__isnull=False
        ).order_by('date_taken').values('date_taken', 'raw_score', 'severity_level')
        
        return list(assessments)
    
    @staticmethod
    def get_treatment_goals_progress(case):
        """
        پیشرفت اهداف درمانی
        """
        try:
            treatment_plan = case.treatment_plan
            goals = treatment_plan.goals.all().values(
                'goal_type',
                'description',
                'progress_percentage',
                'is_achieved'
            )
            return list(goals)
        except:
            return []
