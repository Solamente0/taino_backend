"""
apps/crm_hub/services/notification.py
Service for sending CRM notifications through various channels
"""
import logging
from typing import Tuple, Optional

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.crm_hub.models import CRMNotificationLog, NotificationChannel
from apps.messaging.services.mail import MailManager
from apps.messaging.services.sms_service import SMSService
from apps.notification.services.notifications import NotificationPublishManager
from base_utils.services import AbstractBaseService

User = get_user_model()
logger = logging.getLogger(__name__)


class CRMNotificationService(AbstractBaseService):
    """
    Service for sending notifications through multiple channels
    """
    
    @staticmethod
    def send_campaign_notification(user: User, campaign, channel: str) -> Tuple[bool, CRMNotificationLog]:
        """
        Send a campaign notification through specified channel
        
        Returns:
            Tuple of (success: bool, log: CRMNotificationLog)
        """
        # Create log entry
        log = CRMNotificationLog.objects.create(
            user=user,
            campaign=campaign,
            channel=channel,
            status='pending'
        )
        
        try:
            # Replace placeholders in content
            context = CRMNotificationService._build_context(user, campaign)
            
            if channel == NotificationChannel.EMAIL:
                success = CRMNotificationService._send_email(user, campaign, context, log)
            elif channel == NotificationChannel.SMS:
                success = CRMNotificationService._send_sms(user, campaign, context, log)
            elif channel == NotificationChannel.PUSH:
                success = CRMNotificationService._send_push(user, campaign, context, log)
            elif channel == NotificationChannel.IN_APP:
                success = CRMNotificationService._send_in_app(user, campaign, context, log)
            elif channel == NotificationChannel.WHATSAPP:
                success = CRMNotificationService._send_whatsapp(user, campaign, context, log)
            else:
                success = False
                log.error_message = f"Unsupported channel: {channel}"
            
            if success:
                log.status = 'sent'
                log.sent_at = timezone.now()
            else:
                log.status = 'failed'
            
            log.save()
            return success, log
            
        except Exception as e:
            logger.error(f"Error sending {channel} notification to {user.pid}: {e}")
            log.status = 'failed'
            log.error_message = str(e)
            log.save()
            return False, log
    
    @staticmethod
    def _build_context(user: User, campaign) -> dict:
        """Build context dictionary for template replacement"""
        context = {
            'user_name': user.get_full_name() or user.phone_number,
            'first_name': user.first_name or 'کاربر',
            'days': campaign.trigger_days,
            'campaign_name': campaign.name,
        }
        
        # Add engagement data if available
        if hasattr(user, 'crm_engagement'):
            engagement = user.crm_engagement
            context.update({
                'engagement_score': round(engagement.engagement_score, 1),
                'activities_count': engagement.total_activities,
                'days_since_activity': (
                    (timezone.now() - engagement.last_activity_date).days
                    if engagement.last_activity_date else 0
                ),
            })
            
            if engagement.has_active_subscription:
                context['subscription_days_remaining'] = engagement.subscription_days_remaining
        
        return context
    
    @staticmethod
    def _replace_placeholders(template: str, context: dict) -> str:
        """Replace placeholders in template with context values"""
        result = template
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    @staticmethod
    def _send_email(user: User, campaign, context: dict, log: CRMNotificationLog) -> bool:
        """Send email notification"""
        if not user.email:
            log.error_message = "User has no email address"
            return False
        
        if not campaign.email_template:
            log.error_message = "Campaign has no email template"
            return False
        
        try:
            subject = CRMNotificationService._replace_placeholders(
                campaign.email_subject or campaign.name,
                context
            )
            content = CRMNotificationService._replace_placeholders(
                campaign.email_template,
                context
            )
            
            log.subject = subject
            log.content = content
            
            # Send email
            mail_manager = MailManager()
            mail_manager.send(
                to_email=user.email,
                message=content,
                title=subject
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            log.error_message = str(e)
            return False
    
    @staticmethod
    def _send_sms(user: User, campaign, context: dict, log: CRMNotificationLog) -> bool:
        """Send SMS notification"""
        if not user.phone_number:
            log.error_message = "User has no phone number"
            return False
        
        if not campaign.sms_template:
            log.error_message = "Campaign has no SMS template"
            return False
        
        try:
            content = CRMNotificationService._replace_placeholders(
                campaign.sms_template,
                context
            )
            
            log.content = content
            
            # Send SMS
            success, message = SMSService.send_sms(
                user=user,
                recipient_number=user.phone_number,
                message_content=content,
                source_type='crm_campaign'
            )
            
            if not success:
                log.error_message = f"SMS service returned failure"
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            log.error_message = str(e)
            return False
    
    @staticmethod
    def _send_push(user: User, campaign, context: dict, log: CRMNotificationLog) -> bool:
        """Send push notification"""
        if not campaign.push_title or not campaign.push_body:
            log.error_message = "Campaign has no push notification template"
            return False
        
        try:
            title = CRMNotificationService._replace_placeholders(
                campaign.push_title,
                context
            )
            body = CRMNotificationService._replace_placeholders(
                campaign.push_body,
                context
            )
            
            log.subject = title
            log.content = body
            
            # Send push notification using existing notification system
            from apps.notification.services.notifications import NotificationPublishManager
            
            notification_manager = NotificationPublishManager(
                user=user,
                name=title,
                description=body,
                link=None
            )
            notification_manager.send_mobile_notification()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            log.error_message = str(e)
            return False
    
    @staticmethod
    def _send_in_app(user: User, campaign, context: dict, log: CRMNotificationLog) -> bool:
        """Send in-app notification"""
        try:
            title = campaign.name
            content = CRMNotificationService._replace_placeholders(
                campaign.push_body or campaign.description or "",
                context
            )
            
            log.subject = title
            log.content = content
            
            # Create in-app notification
            from apps.notification.services.alarm import NotificationService
            
            NotificationService.create_notification(
                to_user=user,
                name=title,
                description=content,
                link=None
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending in-app notification: {e}")
            log.error_message = str(e)
            return False
    
    @staticmethod
    def _send_whatsapp(user: User, campaign, context: dict, log: CRMNotificationLog) -> bool:
        """Send WhatsApp notification (placeholder for future implementation)"""
        log.error_message = "WhatsApp integration not yet implemented"
        return False
    
    @staticmethod
    def send_campaign_to_users(campaign, users: list) -> dict:
        """
        Send campaign to multiple users through all configured channels
        
        Returns:
            Dictionary with statistics about sent notifications
        """
        results = {
            'total_users': len(users),
            'total_sent': 0,
            'total_failed': 0,
            'by_channel': {}
        }
        
        for channel in campaign.channels:
            results['by_channel'][channel] = {
                'sent': 0,
                'failed': 0
            }
        
        for user in users:
            for channel in campaign.channels:
                success, log = CRMNotificationService.send_campaign_notification(
                    user, campaign, channel
                )
                
                if success:
                    results['total_sent'] += 1
                    results['by_channel'][channel]['sent'] += 1
                else:
                    results['total_failed'] += 1
                    results['by_channel'][channel]['failed'] += 1
        
        return results
