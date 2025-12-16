from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.messaging.api.v1.serializers import SMSBalanceSerializer, SMSMessageSerializer
from apps.messaging.models import SMSBalance, SMSMessage
from base_utils.views.mobile import TainoMobileGenericViewSet
from apps.lawyer_office.permissions import SecretaryOrLawyerPermission


class SMSBalanceViewSet(TainoMobileGenericViewSet):
    """
    ViewSet for managing user's SMS balance

    Provides endpoints for checking and managing SMS credit balance.
    """

    serializer_class = SMSBalanceSerializer
    permission_classes = [IsAuthenticated, SecretaryOrLawyerPermission]

    def get_queryset(self):
        """Get balance for current user"""
        return SMSBalance.objects.filter(user=self.request.user)

    @extend_schema(
        summary="Get current user's SMS balance",
        description="Returns the current SMS balance for the authenticated user",
        responses={200: SMSBalanceSerializer},
    )
    @action(detail=False, methods=["get"], url_path="my-balance")
    def my_balance(self, request):
        """
        Get current user's SMS balance

        Creates balance record if it doesn't exist yet.
        """
        balance, created = SMSBalance.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(balance)
        return Response(serializer.data)

    @extend_schema(
        summary="Get SMS usage summary",
        description="Returns a summary of SMS usage including balance, messages sent, and recent activity",
        responses={
            200: inline_serializer(
                name="SMSUsageSummarySerializer",
                fields={
                    "balance": serializers.IntegerField(),
                    "total_sent": serializers.IntegerField(),
                    "today_sent": serializers.IntegerField(),
                    "this_month_sent": serializers.IntegerField(),
                    "recent_messages": SMSMessageSerializer(many=True),
                },
            )
        },
    )
    @action(detail=False, methods=["get"], url_path="usage-summary")
    def usage_summary(self, request):
        """
        Get a summary of user's SMS usage

        Includes balance, message counts, and recent activity.
        """
        # Get balance
        balance, created = SMSBalance.objects.get_or_create(user=request.user)

        # Calculate date ranges
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)

        # Count messages
        messages = SMSMessage.objects.filter(sender=request.user)
        total_sent = messages.filter(status="sent").count()

        today_sent = messages.filter(status="sent", created_at__date=today).count()

        this_month_sent = messages.filter(status="sent", created_at__date__gte=first_day_of_month).count()

        # Get recent messages
        recent_messages = messages.order_by("-created_at")[:5]

        return Response(
            {
                "balance": balance.balance,
                "total_sent": total_sent,
                "today_sent": today_sent,
                "this_month_sent": this_month_sent,
                "recent_messages": SMSMessageSerializer(recent_messages, many=True).data,
            }
        )
