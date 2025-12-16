from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.messaging.api.admin.serializers import AdminSMSMessageSerializer, AdminSMSStatsSerializer
from apps.messaging.models import SMSMessage
from apps.messaging.services.sms_service import SMSService
from base_utils.views.admin import TainoAdminGenericViewSet

User = get_user_model()


class AdminSMSMessageViewSet(TainoAdminGenericViewSet):
    """
    Admin ViewSet for managing SMS messages
    """

    serializer_class = AdminSMSMessageSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "sender__first_name",
        "sender__last_name",
        "sender__email",
        "sender__phone_number",
        "recipient_number",
        "recipient_name",
        "content",
    ]
    filterset_fields = ["status", "source_type", "is_active", "is_deleted"]
    ordering_fields = ["created_at", "sent_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Get all SMS messages"""
        return SMSMessage.objects.all().select_related("sender", "creator", "client", "case", "calendar_event")

    @extend_schema(summary="List SMS messages", description="Admin endpoint to list all SMS messages")
    def list(self, request):
        """List all SMS messages"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(summary="Get SMS message details", description="Admin endpoint to get details of a specific SMS message")
    def retrieve(self, request, pk=None):
        """Get details of a specific SMS message"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary="Get SMS statistics",
        description="Get overall SMS usage statistics",
        request=AdminSMSStatsSerializer,
        responses={200: dict},
    )
    @action(detail=False, methods=["post"], url_path="statistics")
    def statistics(self, request):
        """Get SMS usage statistics"""
        serializer = AdminSMSStatsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result)

    @extend_schema(summary="Retry failed messages", description="Retry sending failed SMS messages", responses={200: dict})
    @action(detail=False, methods=["post"], url_path="retry-failed")
    def retry_failed(self, request):
        """Retry sending failed SMS messages"""
        # Get failed messages
        failed_messages = SMSMessage.objects.filter(status="failed", is_active=True, is_deleted=False)

        if not failed_messages.exists():
            return Response({"detail": "No failed messages to retry", "count": 0})

        # Retry each message
        success_count = 0
        results = []

        for message in failed_messages:
            try:
                # Check if sender has sufficient balance
                balance = SMSService.check_user_sms_balance(message.sender)
                if balance <= 0:
                    results.append(
                        {
                            "message_id": message.pid,
                            "recipient": message.recipient_number,
                            "success": False,
                            "reason": "Insufficient balance",
                        }
                    )
                    continue

                # Reset status and attempt to send again
                message.status = "pending"
                message.save()

                # Send the message
                success, _ = SMSService.send_sms(
                    user=message.sender,
                    recipient_number=message.recipient_number,
                    message_content=message.content,
                    recipient_name=message.recipient_name,
                    client=message.client,
                    case=message.case,
                    calendar_event=message.calendar_event,
                    source_type=message.source_type,
                )

                if success:
                    success_count += 1

                results.append(
                    {
                        "message_id": message.pid,
                        "recipient": message.recipient_number,
                        "success": success,
                        "reason": None if success else "Failed to send",
                    }
                )

            except Exception as e:
                results.append(
                    {"message_id": message.pid, "recipient": message.recipient_number, "success": False, "reason": str(e)}
                )

        return Response({"total": failed_messages.count(), "success_count": success_count, "results": results})
