"""
apps/activity_log/services/query.py
Query service for activity logs
"""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Max
from django.utils import timezone

from apps.activity_log.models import ActivityLog, ActivityLogAction
from base_utils.services import AbstractBaseQuery

User = get_user_model()


class ActivityLogQuery(AbstractBaseQuery):
    """Query service for activity logs"""

    @staticmethod
    def get_user_stats(user: User, days: int = 7) -> dict:
        """
        Get activity statistics for a specific user.

        Args:
            user: User instance
            days: Number of days to look back

        Returns:
            Dictionary with statistics
        """
        cutoff_date = timezone.now() - timedelta(days=days)

        queryset = ActivityLog.objects.filter(
            user=user,
            created_at__gte=cutoff_date
        )

        total_activities = queryset.count()
        successful_activities = queryset.filter(is_successful=True).count()
        failed_activities = queryset.filter(is_successful=False).count()

        # Action breakdown
        action_breakdown = queryset.values('action').annotate(
            count=Count('id')
        ).order_by('-count')

        # Level breakdown
        level_breakdown = queryset.values('level').annotate(
            count=Count('id')
        ).order_by('-count')

        return {
            'total_activities': total_activities,
            'successful_activities': successful_activities,
            'failed_activities': failed_activities,
            'success_rate': (successful_activities / total_activities * 100) if total_activities > 0 else 0,
            'action_breakdown': list(action_breakdown),
            'level_breakdown': list(level_breakdown),
        }

    @staticmethod
    def get_system_stats(days: int = 7) -> dict:
        """
        Get system-wide activity statistics.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with statistics
        """
        cutoff_date = timezone.now() - timedelta(days=days)

        queryset = ActivityLog.objects.filter(created_at__gte=cutoff_date)

        total_activities = queryset.count()
        successful_activities = queryset.filter(is_successful=True).count()
        failed_activities = queryset.filter(is_successful=False).count()
        unique_users = queryset.values('user').distinct().count()

        # Action breakdown
        action_breakdown = queryset.values('action').annotate(
            count=Count('id')
        ).order_by('-count')

        # Level breakdown
        level_breakdown = queryset.values('level').annotate(
            count=Count('id')
        ).order_by('-count')

        return {
            'total_activities': total_activities,
            'successful_activities': successful_activities,
            'failed_activities': failed_activities,
            'unique_users': unique_users,
            'success_rate': (successful_activities / total_activities * 100) if total_activities > 0 else 0,
            'action_breakdown': list(action_breakdown),
            'level_breakdown': list(level_breakdown),
        }

    @staticmethod
    def get_users_activity_summary(limit: int = 100) -> list:
        """
        Get activity summary for multiple users.

        Args:
            limit: Maximum number of users to return

        Returns:
            List of dictionaries with user activity summaries
        """
        from django.db.models import Count, Max

        # Get users with their activity counts
        users_data = ActivityLog.objects.values('user__pid').annotate(
            total_activities=Count('id'),
            login_count=Count('id', filter=Q(action=ActivityLogAction.LOGIN)),
            last_login=Max('created_at', filter=Q(action=ActivityLogAction.LOGIN)),
            failed_activities_count=Count('id', filter=Q(is_successful=False)),
            devices_used=Count('device_id', distinct=True)
        ).order_by('-total_activities')[:limit]

        # Get most common action for each user
        summaries = []
        for user_data in users_data:
            user_pid = user_data['user__pid']

            # Get most common action
            most_common = ActivityLog.objects.filter(
                user__pid=user_pid
            ).values('action').annotate(
                count=Count('id')
            ).order_by('-count').first()

            summaries.append({
                'user_pid': user_pid,
                'total_activities': user_data['total_activities'],
                'login_count': user_data['login_count'],
                'last_login': user_data['last_login'],
                'failed_activities_count': user_data['failed_activities_count'],
                'most_common_action': most_common['action'] if most_common else None,
                'devices_used': user_data['devices_used'],
            })

        return summaries

    @staticmethod
    def get_failed_attempts(user: User = None, hours: int = 1) -> int:
        """
        Get count of failed attempts for a user or IP.

        Args:
            user: User instance (optional)
            hours: Number of hours to look back

        Returns:
            Count of failed attempts
        """
        cutoff_time = timezone.now() - timedelta(hours=hours)

        queryset = ActivityLog.objects.filter(
            created_at__gte=cutoff_time,
            is_successful=False
        )

        if user:
            queryset = queryset.filter(user=user)

        return queryset.count()

    @staticmethod
    def get_suspicious_ips(hours: int = 1, threshold: int = 5) -> list:
        """
        Get IP addresses with multiple failed attempts.

        Args:
            hours: Number of hours to look back
            threshold: Minimum number of failed attempts

        Returns:
            List of suspicious IP addresses
        """
        cutoff_time = timezone.now() - timedelta(hours=hours)

        suspicious = ActivityLog.objects.filter(
            created_at__gte=cutoff_time,
            is_successful=False
        ).values('ip_address').annotate(
            failed_count=Count('id')
        ).filter(
            failed_count__gte=threshold
        ).values_list('ip_address', flat=True)

        return list(suspicious)

    @staticmethod
    def get_user_devices(user: User) -> list:
        """
        Get list of devices used by a user.

        Args:
            user: User instance

        Returns:
            List of device information
        """
        devices = ActivityLog.objects.filter(
            user=user,
            device_id__isnull=False
        ).exclude(
            device_id=''
        ).values(
            'device_id',
            'user_agent'
        ).annotate(
            last_used=Max('created_at'),
            usage_count=Count('id')
        ).order_by('-last_used')

        return list(devices)

    @staticmethod
    def get_activity_timeline(user: User, days: int = 7):
        """
        Get activity timeline for a user.

        Args:
            user: User instance
            days: Number of days to look back

        Returns:
            QuerySet of activities ordered by time
        """
        cutoff_date = timezone.now() - timedelta(days=days)

        return ActivityLog.objects.filter(
            user=user,
            created_at__gte=cutoff_date
        ).order_by('-created_at')
