from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.notification.api.v1.serializers import (
    UserNotificationTokenSerializer,
    UserNotificationListRetrieveSerializer,
    UserNotificationUpdateSerializer,
    UserRequestsListRetrieveSerializer,
    UserNotificationBulkUpdateSerializer,
)
from apps.notification.models import UserNotificationToken, UserSentRequests, UserSentNotification
from base_utils.filters import IsActiveFilterBackend
from base_utils.views.mobile import (
    TainoMobileModelViewSet,
    TainoMobileGenericViewSet,
    TainoMobileRetrieveModelMixin,
    TainoMobileUpdateModelMixin,
    TainoMobileListModelMixin,
)


class UserNotificationTokenViewSet(TainoMobileModelViewSet):
    serializer_class = UserNotificationTokenSerializer
    queryset = UserNotificationToken.objects.all()
    http_method_names = ["post"]

    # def get_queryset(self):
    #     return LoyaltyScoreLog.objects.filter(user=self.request.user)


class UseNotificationsViewSet(
    TainoMobileRetrieveModelMixin,
    TainoMobileUpdateModelMixin,
    TainoMobileListModelMixin,
    TainoMobileGenericViewSet,
):

    def get_queryset(self):
        return UserSentNotification.objects.filter(to_user=self.request.user)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return UserNotificationListRetrieveSerializer

        return UserNotificationUpdateSerializer

    @extend_schema(request=UserNotificationBulkUpdateSerializer)
    @action(detail=False, name="bulk-seen", methods=["post"], url_path="bulk-seen", url_name="bulk_seen_api")
    def bulk_seen(self, request, *args, **kwargs):
        pids = request.data.get("pids")
        self.get_queryset().filter(pid__in=pids, to_user=request.user).update(seen=True)
        return Response(status=status.HTTP_200_OK)


#
# class UserRequestsViewSet(
#     TainoMobileRetrieveModelMixin,
#     TainoMobileUpdateModelMixin,
#     TainoMobileListModelMixin,
#     TainoMobileGenericViewSet,
# ):
#
#     def get_queryset(self):
#         return UserSentRequests.objects.filter(to_user=self.request.user, is_done=False)
#
#     def get_serializer_class(self):
#         if self.action in ["list", "retrieve"]:
#             return UserRequestsListRetrieveSerializer
#
#         return UserRequestsUpdateSerializer
#
#     @extend_schema(request=UserNotificationBulkUpdateSerializer)
#     @action(detail=False, name="bulk-seen", methods=["post"], url_path="bulk-seen", url_name="bulk_seen_api")
#     def bulk_seen(self, request, *args, **kwargs):
#         pids = request.data.get("pids")
#         self.get_queryset().filter(pid__in=pids).update(seen=True)
#         return Response(status=status.HTTP_200_OK)
#


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_summary(request, **kwargs):
    from rest_framework.response import Response

    notifications = UserSentNotification.objects.filter(to_user=request.user)
    requests = UserSentRequests.objects.filter(to_user=request.user)

    context = {"request": request}
    result = {
        "notifications": {
            "unread_count": notifications.filter(seen=False).count(),
            "last_item": (
                UserNotificationListRetrieveSerializer(
                    instance=notifications.order_by("-created_at").last(), context=context
                ).data
                if notifications.order_by("-created_at").last()
                else None
            ),
        },
        "requests": {
            "unread_count": requests.filter(seen=False).count(),
            "last_item": (
                UserRequestsListRetrieveSerializer(instance=requests.order_by("-created_at").last(), context=context).data
                if requests.order_by("-created_at").last()
                else None
            ),
        },
        "orders": {
            "unread_count": 0,
            "last_item": None,
        },
    }

    return Response(result, status=status.HTTP_200_OK)


class NotificationAlarmsViewSet(
    TainoMobileRetrieveModelMixin,
    TainoMobileUpdateModelMixin,
    TainoMobileListModelMixin,
    TainoMobileGenericViewSet,
):
    """
    ViewSet for alarm-type notifications
    """

    filter_backends = [IsActiveFilterBackend, SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["name", "description", "link"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return UserSentNotification.objects.filter(to_user=self.request.user).order_by("-created_at")

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return UserNotificationListRetrieveSerializer
        return UserNotificationUpdateSerializer

    @extend_schema(request=UserNotificationBulkUpdateSerializer)
    @action(detail=False, name="bulk-seen", methods=["post"], url_path="bulk-seen", url_name="bulk_seen_api")
    def bulk_seen(self, request, *args, **kwargs):
        pids = request.data.get("pids")
        self.get_queryset().filter(pid__in=pids, to_user=request.user).update(seen=True)
        return Response(status=status.HTTP_200_OK)
