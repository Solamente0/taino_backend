from typing import List

from celery import shared_task
from django.contrib.auth import get_user_model

from apps.notification.services.firebase import send_firebase_push_notifications

User = get_user_model()


@shared_task
def send_firebase_notifications_task(title: str, message: str, registration_token: str):
    send_firebase_push_notifications(title, message, [registration_token])


@shared_task
def send_email_notifications_task(to_user_id: int, email_body: str, email_subject: str):
    # to_user = get_user_model().objects.get(id=to_user_id)
    pass


@shared_task
def send_sms_notification_task(recipients: List[str], messages: List[str]):
    pass
