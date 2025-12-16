from django.contrib.auth import get_user_model

from apps.notification.models import UserSentNotification, UserNotificationToken
from apps.notification.tasks.notifications import send_firebase_notifications_task

User = get_user_model()


class NotificationPublishManager:

    def __init__(self, user=None, name="", description="", link=None):
        self.user = user
        self.name = name
        self.description = description
        self.link = link

    def create_notification(self, to_user) -> UserSentNotification:
        """
        Create a notification for a specific user
        """
        notification = UserSentNotification.objects.create(
            name=self.name, description=self.description, to_user=to_user, link=self.link
        )
        # Send push notification if enabled
        self._send_push_notification(to_user)
        return notification

    def create_bulk_notifications(self, users) -> list:
        """
        Create notifications for multiple users
        """
        notifications = []
        for user in users:
            notifications.append(
                UserSentNotification(name=self.name, description=self.description, to_user=user, link=self.link)
            )

        # Bulk create notifications
        created = UserSentNotification.objects.bulk_create(notifications)

        # Send push notifications
        for user in users:
            self._send_push_notification(user)

        return created

    def _send_push_notification(self, user):
        """
        Send push notification to user's registered devices
        """
        tokens = list(UserNotificationToken.objects.filter(user=user).values_list("token", flat=True))
        for token in tokens:
            send_firebase_notifications_task.apply_async(
                kwargs={
                    "title": str(self.name),
                    "message": str(self.description),
                    "registration_token": str(token),
                }
            )

    def save_notification(self, channel) -> UserSentNotification:
        sent_notification = UserSentNotification.objects.create(
            name=self.name, description=self.description, user=self.user, channel=channel
        )
        return sent_notification

    def send_mobile_notification(self):
        tokens = list(UserNotificationToken.objects.filter(user=self.user).values_list("token", flat=True))
        for token in tokens:
            send_firebase_notifications_task.apply_async(
                kwargs={
                    "title": str(self.name),
                    "message": str(self.description),
                    "registration_token": str(token),
                }
            )

    def send_email_notification(self):
        # sent_notification = self.save_notification(NotificationChannelChoices.EMAIL)
        # send_email_notifications_task.apply_async(
        #     kwargs={
        #         "to_user_id": self.user.id,
        #         "email_body": sent_notification.description,
        #         "email_subject": self.notification.name,
        #     }
        # )
        pass

    def send_sms_notification(self):
        # sent_notification = self.save_notification(NotificationChannelChoices.SMS)
        # send_sms_notification_task.apply_async(
        #     kwargs={
        #         "recipients": [self.user.mobile_number],
        #         "messages": [self.notification.name + "\n\n" + sent_notification.description],
        #     }
        # )
        pass
