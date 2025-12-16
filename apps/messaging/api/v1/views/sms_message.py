from django.db.models import Sum
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from rest_framework import serializers, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.messaging.api.v1.serializers import SMSMessageSerializer, SMSSendSerializer, SMSSendWithTemplateSerializer
from apps.messaging.models import SMSPurchase, SMSMessage
from apps.messaging.services.sms_service import SMSService
from apps.messaging.services.utils import validate_phone_number
from base_utils.views.mobile import TainoMobileGenericViewSet
from apps.lawyer_office.permissions import SecretaryOrLawyerPermission


class SMSMessageViewSet(TainoMobileGenericViewSet):
    """
    ViewSet for SMS messages

    Allows sending SMS messages and viewing message history.
    """

    permission_classes = [IsAuthenticated, SecretaryOrLawyerPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["recipient_number", "recipient_name", "content"]
    filterset_fields = ["status", "source_type"]
    ordering_fields = ["created_at", "sent_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Get messages sent by current user"""
        return SMSMessage.objects.filter(sender=self.request.user)

    def get_serializer_class(self):
        """Select appropriate serializer based on action"""
        if self.action == "send_sms":
            return SMSSendSerializer
        elif self.action == "send_with_template":
            return SMSSendWithTemplateSerializer
        return SMSMessageSerializer

    @extend_schema(
        summary="List sent SMS messages",
        description="Returns a paginated list of SMS messages sent by the current user",
        responses={200: SMSMessageSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name="status",
                description="Filter by status",
                required=False,
                type=str,
                enum=["pending", "sent", "failed", "insufficient_balance"],
            ),
            OpenApiParameter(
                name="source_type",
                description="Filter by source type",
                required=False,
                type=str,
                enum=["manual", "auto_court_session", "auto_objection", "auto_exchange"],
            ),
            OpenApiParameter(name="search", description="Search in recipient or content", required=False, type=str),
        ],
    )
    def list(self, request):
        """
        List user's sent SMS messages

        Returns paginated history of sent messages with filtering options.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get message details",
        description="Get detailed information about a specific SMS message",
        responses={200: SMSMessageSerializer},
    )
    def retrieve(self, request, pk=None):
        """Get details of a specific SMS message"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary="Send SMS message",
        description="Send an SMS message to a recipient",
        request=SMSSendSerializer,
        responses={
            201: inline_serializer(
                name="SMSSendResponseSerializer",
                fields={
                    "success": serializers.BooleanField(),
                    "message_id": serializers.CharField(),
                    "status": serializers.CharField(),
                    "balance": serializers.IntegerField(),
                },
            )
        },
    )
    @action(detail=False, methods=["post"], url_path="send")
    def send_sms(self, request):
        """
        Send an SMS message

        Sends a custom SMS message to a recipient.
        Requires sufficient SMS balance.
        """
        # Validate and normalize phone number
        if "recipient_number" in request.data:
            is_valid, result = validate_phone_number(request.data["recipient_number"])
            if not is_valid:
                return Response({"detail": f"Invalid phone number: {result}"}, status=status.HTTP_400_BAD_REQUEST)
            # Update with normalized number
            request.data["recipient_number"] = result

        serializer = SMSSendSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Send SMS with template",
        description="Send an SMS message using a predefined template",
        request=SMSSendWithTemplateSerializer,
        responses={
            201: inline_serializer(
                name="SMSTemplateResponseSerializer",
                fields={
                    "success": serializers.BooleanField(),
                    "message_id": serializers.CharField(),
                    "status": serializers.CharField(),
                    "balance": serializers.IntegerField(),
                },
            )
        },
    )
    @action(detail=False, methods=["post"], url_path="send-with-template")
    def send_with_template(self, request):
        """
        Send an SMS message using a template

        Uses a template with custom values to generate and send an SMS.
        Requires sufficient SMS balance.
        """
        # Validate and normalize phone number
        if "recipient_number" in request.data:
            is_valid, result = validate_phone_number(request.data["recipient_number"])
            if not is_valid:
                return Response({"detail": f"Invalid phone number: {result}"}, status=status.HTTP_400_BAD_REQUEST)
            # Update with normalized number
            request.data["recipient_number"] = result

        serializer = SMSSendWithTemplateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Get SMS statistics",
        description="Get statistics about SMS usage",
        responses={
            200: inline_serializer(
                name="SMSStatsSerializer",
                fields={
                    "balance": serializers.IntegerField(),
                    "total_sent": serializers.IntegerField(),
                    "sent_by_source": serializers.DictField(),
                    "failed": serializers.IntegerField(),
                    "total_purchased": serializers.IntegerField(),
                    "monthly_usage": serializers.ListField(child=serializers.DictField(child=serializers.IntegerField())),
                },
            )
        },
    )
    @action(detail=False, methods=["get"], url_path="statistics")
    def statistics(self, request):
        """
        Get SMS usage statistics

        Returns summary statistics about SMS usage including balance,
        sent counts, and monthly usage patterns.
        """
        user = request.user

        # Get current balance
        balance = SMSService.check_user_sms_balance(user)

        # Get total sent messages
        total_sent = SMSMessage.objects.filter(sender=user, status="sent").count()

        # Get sent by source type
        sent_by_source = {}
        for source_type, _ in SMSMessage.SOURCE_TYPE_CHOICES:
            sent_by_source[source_type] = SMSMessage.objects.filter(
                sender=user, status="sent", source_type=source_type
            ).count()

        # Get failed messages
        failed = SMSMessage.objects.filter(sender=user, status="failed").count()

        # Get total purchased
        total_purchased = (
            SMSPurchase.objects.filter(user=user, is_active=True).aggregate(total=Sum("sms_quantity"))["total"] or 0
        )

        # Get monthly usage for the past 6 months
        monthly_usage = []
        now = timezone.now()

        for i in range(5, -1, -1):
            month_start = (now - timezone.timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i > 0:
                month_end = (now - timezone.timedelta(days=30 * (i - 1))).replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
            else:
                month_end = now

            count = SMSMessage.objects.filter(
                sender=user, status="sent", created_at__gte=month_start, created_at__lt=month_end
            ).count()

            monthly_usage.append({"month": month_start.strftime("%Y-%m"), "count": count})

        return Response(
            {
                "balance": balance,
                "total_sent": total_sent,
                "sent_by_source": sent_by_source,
                "failed": failed,
                "total_purchased": total_purchased,
                "monthly_usage": monthly_usage,
            }
        )

    @extend_schema(
        summary="Bulk send SMS",
        description="Send the same SMS to multiple recipients",
        request=inline_serializer(
            name="BulkSMSSerializer",
            fields={
                "recipient_numbers": serializers.ListField(
                    child=serializers.CharField(),
                ),
                "message": serializers.CharField(),
                "client_id": serializers.CharField(required=False),
                "case_id": serializers.CharField(required=False),
            },
        ),
        responses={
            201: inline_serializer(
                name="BulkSMSResponseSerializer",
                fields={
                    "success": serializers.BooleanField(),
                    "total": serializers.IntegerField(),
                    "success_count": serializers.IntegerField(),
                    "results": serializers.ListField(),
                    "remaining_balance": serializers.IntegerField(),
                },
            )
        },
    )
    @action(detail=False, methods=["post"], url_path="bulk-send")
    def bulk_send(self, request):
        """
        Send SMS to multiple recipients

        Sends the same message to multiple recipients.
        Requires sufficient SMS balance for all messages.
        """
        from apps.messaging.services.utils import send_bulk_sms

        # Validate input
        if not request.data.get("recipient_numbers"):
            return Response({"detail": "recipient_numbers field is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not request.data.get("message"):
            return Response({"detail": "message field is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Normalize all phone numbers
        normalized_numbers = []
        invalid_numbers = []

        for number in request.data.get("recipient_numbers", []):
            is_valid, result = validate_phone_number(number)
            if is_valid:
                normalized_numbers.append(result)
            else:
                invalid_numbers.append(f"{number}: {result}")

        if invalid_numbers:
            return Response(
                {"detail": "Invalid phone numbers detected", "invalid_numbers": invalid_numbers},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Send bulk SMS
        result = send_bulk_sms(
            user_id=request.user.pid,
            recipient_numbers=normalized_numbers,
            message=request.data.get("message"),
            client_id=request.data.get("client_id"),
            case_id=request.data.get("case_id"),
        )

        if not result.get("success"):
            return Response({"detail": result.get("error", "Failed to send messages")}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_201_CREATED)
