from django.contrib.auth import get_user_model

from apps.notification.models import UserSentNotification

User = get_user_model()


class NotificationService:
    """
    Service for creating and managing user notifications
    """

    @staticmethod
    def create_notification(to_user, name, description, link=None):
        """
        Create a notification for a user

        Args:
            to_user: The user to notify
            name: Notification title
            description: Notification content
            link: Optional link to include

        Returns:
            UserSentNotification object
        """
        notification = UserSentNotification.objects.create(to_user=to_user, name=name, description=description, link=link)

        return notification

    @staticmethod
    def create_bulk_notifications(users, name, description, link=None):
        """
        Create notifications for multiple users

        Args:
            users: List of users to notify
            name: Notification title
            description: Notification content
            link: Optional link to include

        Returns:
            List of created UserSentNotification objects
        """
        notifications = []

        for user in users:
            notification = UserSentNotification.objects.create(to_user=user, name=name, description=description, link=link)
            notifications.append(notification)

        return notifications

    @staticmethod
    def mark_as_read(notification_id):
        """
        Mark a notification as read

        Args:
            notification_id: ID of the notification to mark as read

        Returns:
            True if successful, False otherwise
        """
        try:
            notification = UserSentNotification.objects.get(pid=notification_id)
            notification.seen = True
            notification.save()
            return True
        except UserSentNotification.DoesNotExist:
            return False
