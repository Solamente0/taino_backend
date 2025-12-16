from .base import TIME_ZONE
from .third_party import RABBITMQ_PORT, RABBITMQ_HOST, RABBITMQ_PASSWORD, RABBITMQ_USERNAME
from celery.schedules import crontab

CELERY_BROKER_URL = f"amqp://{RABBITMQ_USERNAME}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}"
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_RESULT_EXTENDED = True
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Fix for Celery 6.x connection retry
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

CELERY_BEAT_SCHEDULE = {
    "check_expired_subscriptions": {
        "task": "apps.subscription.tasks.check_expired_subscriptions",
        "schedule": crontab(hour="0", minute="0"),  # Run daily at midnight
    },
    # "sync-mongo-to-postgres": {
    #     "task": "apps.chat.tasks.sync_mongo_to_postgres",
    #     "schedule": crontab(minute="*/5"),  # Run every 5 minutes
    # },
    # Sync premium status daily at 2:00 AM
    "sync-premium-status": {
        "task": "apps.subscription.tasks.sync_premium_status",
        "schedule": crontab(hour="2", minute="0"),
    },
    "update-expired-ai-sessions": {
        "task": "apps.ai_chat.tasks.update_expired_ai_sessions",
        "schedule": crontab(minute="*/5"),  # Run every 5 minutes
    },
    # Run notification cleanup daily at 12:00 AM
    # "delete-old-notifications": {
    #     "task": "apps.notification.tasks.retention.delete_old_notifications_task",
    #     "schedule": crontab(hour="12", minute="00"),
    # },
    # "send-court-session-reminders": {
    #     "task": "apps.messaging.tasks.sms.send_court_session_reminders_task",
    #     "schedule": crontab(hour="12", minute="0"),
    # },
    # "send-objection-deadline-reminders": {
    #     "task": "apps.messaging.tasks.sms.send_objection_deadline_reminders_task",
    #     "schedule": crontab(hour="12", minute="0"),
    # },
    # "send-exchange-deadline-reminders": {
    #     "task": "apps.messaging.tasks.sms.send_exchange_deadline_reminders_task",
    #     "schedule": crontab(hour="12", minute="0"),
    # },
    # "send-calendar-reminder-notifications": {
    #     "task": "apps.notification.tasks.alarm.send_calendar_reminder_notifications_task",
    #     "schedule": crontab(hour="12", minute="0"),  # اجرا هر روز ساعت 12 صبح
    # },
    "delete-old-activity-logs": {
        "task": "apps.activity_log.tasks.delete_old_activity_logs",
        "schedule": crontab(hour="2", minute="0"),  # Run daily at 2 AM
    },
    "cleanup-anonymous-logs": {
        "task": "apps.activity_log.tasks.cleanup_anonymous_logs",
        "schedule": crontab(hour="3", minute="0"),  # Run daily at 3 AM
    },
    "update-all-user-engagement": {
        "task": "apps.crm_hub.tasks.update_all_user_engagement",
        "schedule": crontab(hour="1", minute="0"),
    },
    # Process CRM campaigns twice daily (morning and evening)
    "process-crm-campaigns-morning": {
        "task": "apps.crm_hub.tasks.process_crm_campaigns",
        "schedule": crontab(hour="9", minute="0"),
    },
    "process-crm-campaigns-evening": {
        "task": "apps.crm_hub.tasks.process_crm_campaigns",
        "schedule": crontab(hour="18", minute="0"),
    },
    "clean-old-crm-logs": {
        "task": "apps.crm_hub.tasks.clean_old_notification_logs",
        "schedule": crontab(hour="3", minute="0", day_of_month="1"),
    },
    # Identify high-risk users daily
    "identify-churn-risk-users": {
        "task": "apps.crm_hub.tasks.identify_churn_risk_users",
        "schedule": crontab(hour="8", minute="0"),
    },
}
