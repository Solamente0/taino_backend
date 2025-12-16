from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import UserNotificationTokenViewSet, UseNotificationsViewSet, get_summary, NotificationAlarmsViewSet

app_name = "notification"

router = DefaultRouter()
router.register("token", UserNotificationTokenViewSet, basename="user-notification-token")
router.register("alarms", NotificationAlarmsViewSet, basename="notification-alarms")

# router.register("requests", UserRequestsViewSet, basename="requests")
router.register("", UseNotificationsViewSet, basename="notifications")


urlpatterns = [
    path("sammary/", get_summary, name="get_summary"),
]

urlpatterns += router.urls
