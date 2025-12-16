"""
apps/crm_hub/services/engagement.py
Service for tracking and calculating user engagement
"""
import logging
from datetime import timedelta
from typing import Optional

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone

from apps.activity_log.models import ActivityLog
from apps.crm_hub.models import CRMUserEngagement
from base_utils.services import AbstractBaseService

User = get_user_model()
logger = logging.getLogger(__name__)


class EngagementTrackingService(AbstractBaseService):
    """
    Service for tracking and updating user engagement metrics
    """
    
    @staticmethod
    def update_user_engagement(user: User) -> CRMUserEngagement:
        """
        Update or create engagement metrics for a user
        """
        engagement, created = CRMUserEngagement.objects.get_or_create(user=user)
        
        now = timezone.now()
        
        # Get activity data
        activities = ActivityLog.objects.filter(user=user)
        
        # Last login/activity
        last_login = activities.filter(action='login').order_by('-created_at').first()
        if last_login:
            engagement.last_login_date = last_login.created_at
        
        last_activity = activities.order_by('-created_at').first()
        if last_activity:
            engagement.last_activity_date = last_activity.created_at
        
        # Activity counts
        engagement.total_activities = activities.count()
        
        seven_days_ago = now - timedelta(days=7)
        engagement.activities_last_7_days = activities.filter(
            created_at__gte=seven_days_ago
        ).count()
        
        thirty_days_ago = now - timedelta(days=30)
        engagement.activities_last_30_days = activities.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        # Subscription data
        EngagementTrackingService._update_subscription_data(user, engagement)
        
        # Calculate scores
        engagement.engagement_score = EngagementTrackingService._calculate_engagement_score(
            engagement
        )
        engagement.churn_risk_score = EngagementTrackingService._calculate_churn_risk(
            engagement
        )
        
        engagement.save()
        return engagement
    
    @staticmethod
    def _update_subscription_data(user: User, engagement: CRMUserEngagement):
        """Update subscription-related metrics"""
        try:
            from apps.subscription.services.subscription import SubscriptionService
            
            has_subscription = SubscriptionService.has_active_subscription(user)
            engagement.has_active_subscription = has_subscription
            
            if has_subscription:
                active_sub = SubscriptionService.get_active_subscription(user)
                if active_sub:
                    engagement.subscription_expire_date = active_sub.end_date
                    
                    # Calculate days remaining
                    if active_sub.end_date:
                        delta = active_sub.end_date - timezone.now()
                        engagement.subscription_days_remaining = max(0, delta.days)
                        
                        # Calculate usage percent
                        total_days = (active_sub.end_date - active_sub.start_date).days
                        used_days = (timezone.now() - active_sub.start_date).days
                        if total_days > 0:
                            engagement.subscription_usage_percent = (used_days / total_days) * 100
        except Exception as e:
            logger.error(f"Error updating subscription data: {e}")
    
    @staticmethod
    def _calculate_engagement_score(engagement: CRMUserEngagement) -> float:
        """
        Calculate engagement score (0-100)
        Higher = more engaged
        """
        score = 0.0
        
        # Recent activity (40 points max)
        if engagement.activities_last_7_days > 0:
            score += min(40, engagement.activities_last_7_days * 4)
        
        # Total activity (20 points max)
        score += min(20, engagement.total_activities * 0.5)
        
        # Subscription status (20 points)
        if engagement.has_active_subscription:
            score += 20
        
        # Recency (20 points)
        if engagement.last_activity_date:
            days_since_activity = (timezone.now() - engagement.last_activity_date).days
            if days_since_activity == 0:
                score += 20
            elif days_since_activity <= 3:
                score += 15
            elif days_since_activity <= 7:
                score += 10
            elif days_since_activity <= 14:
                score += 5
        
        return min(100.0, score)
    
    @staticmethod
    def _calculate_churn_risk(engagement: CRMUserEngagement) -> float:
        """
        Calculate churn risk score (0-100)
        Higher = higher risk of churning
        """
        risk = 0.0
        
        # No recent activity
        if engagement.last_activity_date:
            days_since = (timezone.now() - engagement.last_activity_date).days
            if days_since > 30:
                risk += 40
            elif days_since > 14:
                risk += 30
            elif days_since > 7:
                risk += 20
            elif days_since > 3:
                risk += 10
        else:
            risk += 50  # Never active
        
        # Low activity
        if engagement.activities_last_7_days == 0:
            risk += 25
        elif engagement.activities_last_7_days < 3:
            risk += 15
        
        # Subscription expiring soon
        if engagement.has_active_subscription:
            if engagement.subscription_days_remaining is not None:
                if engagement.subscription_days_remaining <= 3:
                    risk += 20
                elif engagement.subscription_days_remaining <= 7:
                    risk += 10
        else:
            risk += 15  # No subscription = higher churn risk
        
        return min(100.0, risk)
    
    @staticmethod
    def bulk_update_engagement(user_ids: list = None):
        """
        Update engagement for multiple users
        If user_ids is None, updates all users
        """
        if user_ids:
            users = User.objects.filter(pid__in=user_ids, is_active=True)
        else:
            users = User.objects.filter(is_active=True)
        
        updated_count = 0
        for user in users:
            try:
                EngagementTrackingService.update_user_engagement(user)
                updated_count += 1
            except Exception as e:
                logger.error(f"Error updating engagement for user {user.pid}: {e}")
        
        return updated_count


class CRMTargetingService(AbstractBaseService):
    """
    Service for finding users that match campaign criteria
    """
    
    @staticmethod
    def get_campaign_targets(campaign) -> list:
        """
        Get list of users who should receive this campaign
        """
        from apps.crm_hub.models import CRMCampaign, CRMNotificationLog
        
        # Start with active users
        queryset = User.objects.filter(is_active=True)
        
        # Filter by role if specified
        if campaign.target_user_roles:
            queryset = queryset.filter(role__static_name__in=campaign.target_user_roles)
        
        # Get their engagement data
        queryset = queryset.select_related('crm_engagement')
        
        eligible_users = []
        
        for user in queryset:
            # Check if user already received this campaign max times
            sent_count = CRMNotificationLog.objects.filter(
                user=user,
                campaign=campaign
            ).count()
            
            if sent_count >= campaign.max_sends_per_user:
                continue
            
            # Check engagement criteria
            if not hasattr(user, 'crm_engagement'):
                # Create engagement data if missing
                EngagementTrackingService.update_user_engagement(user)
            
            engagement = user.crm_engagement
            
            # Check trigger days
            days_since_registration = (timezone.now() - user.created_at).days
            if days_since_registration < campaign.trigger_days:
                continue
            
            # Check activity requirement
            if campaign.require_no_activity:
                if engagement.last_activity_date:
                    days_since_activity = (
                        timezone.now() - engagement.last_activity_date
                    ).days
                    if days_since_activity < campaign.trigger_days:
                        continue
            
            # Check subscription requirement
            if campaign.require_no_subscription:
                if engagement.has_active_subscription:
                    continue
            
            # Check subscription expiration threshold
            if campaign.subscription_expire_threshold:
                if not engagement.has_active_subscription:
                    continue
                
                if engagement.subscription_usage_percent:
                    remaining = 100 - engagement.subscription_usage_percent
                    if remaining > campaign.subscription_expire_threshold:
                        continue
            
            eligible_users.append(user)
        
        return eligible_users
