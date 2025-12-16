from typing import List

import firebase_admin
from django.conf import settings
from firebase_admin import credentials, messaging

cred = credentials.Certificate(settings.BASE_DIR.joinpath("fcm.json"))
firebase_admin.initialize_app(cred)


def send_firebase_push_notifications(title: str, message: str, registration_tokens: List[str], data: dict = None):
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=message),
        data=data,
        tokens=registration_tokens,
    )

    response = messaging.send_multicast(message)
