"""
apps/crm_hub/tasks.py
Celery tasks for CRM automation
"""

import logging
from celery import shared_task
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(name="apps.crm_hub.tasks.update_all_user_engagement")
def update_all_user_engagement_task():
    """
    Update engagement metrics for all active users
    Should run daily
    """
    try:
        from apps.crm_hub.services.engagement import EngagementTrackingService

        count = EngagementTrackingService.bulk_update_engagement()

        logger.info(f"Updated engagement for {count} users")
        return {"success": True, "users_updated": count}

    except Exception as e:
        logger.error(f"Error updating user engagement: {e}")
        return {"success": False, "error": str(e)}


@shared_task(name="apps.crm_hub.tasks.process_crm_campaigns")
def process_crm_campaigns_task():
    """
    Process all active CRM campaigns and send notifications
    Should run daily or multiple times per day
    """
    try:
        from apps.crm_hub.models import CRMCampaign
        from apps.crm_hub.services.engagement import CRMTargetingService
        from apps.crm_hub.services.notification import CRMNotificationService

        # Get all active campaigns
        campaigns = CRMCampaign.objects.filter(is_active=True).order_by("priority")

        total_sent = 0
        total_failed = 0
        campaign_results = []

        for campaign in campaigns:
            try:
                # Find eligible users
                eligible_users = CRMTargetingService.get_campaign_targets(campaign)

                if not eligible_users:
                    logger.info(f"No eligible users for campaign: {campaign.name}")
                    continue

                logger.info(f"Processing campaign '{campaign.name}' for {len(eligible_users)} users")

                # Send notifications
                results = CRMNotificationService.send_campaign_to_users(campaign, eligible_users)

                total_sent += results["total_sent"]
                total_failed += results["total_failed"]

                campaign_results.append(
                    {
                        "campaign": campaign.name,
                        "eligible_users": len(eligible_users),
                        "sent": results["total_sent"],
                        "failed": results["total_failed"],
                        "by_channel": results["by_channel"],
                    }
                )

            except Exception as e:
                logger.error(f"Error processing campaign {campaign.name}: {e}")
                campaign_results.append({"campaign": campaign.name, "error": str(e)})

        logger.info(f"CRM campaigns processed. Total sent: {total_sent}, Total failed: {total_failed}")

        return {
            "success": True,
            "campaigns_processed": len(campaigns),
            "total_sent": total_sent,
            "total_failed": total_failed,
            "campaign_results": campaign_results,
        }

    except Exception as e:
        logger.error(f"Error processing CRM campaigns: {e}")
        return {"success": False, "error": str(e)}


@shared_task(name="apps.crm_hub.tasks.update_user_engagement")
def update_user_engagement_task(user_pid: str):
    """
    Update engagement metrics for a specific user
    Can be triggered after user activity
    """
    try:
        from apps.crm_hub.services.engagement import EngagementTrackingService

        user = User.objects.get(pid=user_pid)
        engagement = EngagementTrackingService.update_user_engagement(user)

        return {
            "success": True,
            "user": user_pid,
            "engagement_score": engagement.engagement_score,
            "churn_risk": engagement.churn_risk_score,
        }

    except User.DoesNotExist:
        logger.error(f"User not found: {user_pid}")
        return {"success": False, "error": "User not found"}
    except Exception as e:
        logger.error(f"Error updating engagement for user {user_pid}: {e}")
        return {"success": False, "error": str(e)}


@shared_task(name="apps.crm_hub.tasks.send_campaign_to_user")
def send_campaign_to_user_task(user_pid: str, campaign_pid: str):
    """
    Send a specific campaign to a specific user
    """
    try:
        from apps.crm_hub.models import CRMCampaign
        from apps.crm_hub.services.notification import CRMNotificationService

        user = User.objects.get(pid=user_pid)
        campaign = CRMCampaign.objects.get(pid=campaign_pid)

        results = CRMNotificationService.send_campaign_to_users(campaign, [user])

        return {
            "success": True,
            "user": user_pid,
            "campaign": campaign.name,
            "sent": results["total_sent"],
            "failed": results["total_failed"],
        }

    except User.DoesNotExist:
        return {"success": False, "error": "User not found"}
    except Exception as e:
        logger.error(f"Error sending campaign: {e}")
        return {"success": False, "error": str(e)}


@shared_task(name="apps.crm_hub.tasks.identify_churn_risk_users")
def identify_churn_risk_users_task(min_risk_score: float = 70.0):
    """
    Identify users at high risk of churning
    Returns list of user PIDs with high churn risk
    """
    try:
        from apps.crm_hub.models import CRMUserEngagement

        high_risk_users = CRMUserEngagement.objects.filter(
            churn_risk_score__gte=min_risk_score, user__is_active=True
        ).select_related("user")

        result = [
            {
                "user_pid": eng.user.pid,
                "user_name": eng.user.get_full_name(),
                "churn_risk": eng.churn_risk_score,
                "engagement_score": eng.engagement_score,
                "days_since_activity": ((timezone.now() - eng.last_activity_date).days if eng.last_activity_date else None),
            }
            for eng in high_risk_users
        ]

        logger.info(f"Found {len(result)} users at high churn risk")

        return {"success": True, "count": len(result), "users": result}

    except Exception as e:
        logger.error(f"Error identifying churn risk users: {e}")
        return {"success": False, "error": str(e)}


@shared_task(name="apps.crm_hub.tasks.clean_old_notification_logs")
def clean_old_notification_logs_task(days: int = 90):
    """
    Clean notification logs older than specified days
    """
    try:
        from datetime import timedelta
        from django.utils import timezone
        from apps.crm_hub.models import CRMNotificationLog

        cutoff_date = timezone.now() - timedelta(days=days)

        deleted_count, _ = CRMNotificationLog.objects.filter(created_at__lt=cutoff_date).delete()

        logger.info(f"Deleted {deleted_count} old CRM notification logs")

        return {"success": True, "deleted_count": deleted_count}

    except Exception as e:
        logger.error(f"Error cleaning old notification logs: {e}")
        return {"success": False, "error": str(e)}
