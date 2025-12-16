from rest_framework import serializers

from apps.lawyer_office.api.v1.serializers.base import LawyerOfficeUserMinimalSerializer
from apps.messaging.models import SMSBalance, SMSTemplate, SMSPurchase, SMSMessage, SystemSMSTemplate
from base_utils.serializers.base import TainoBaseModelSerializer, TainoBaseSerializer


class SMSSendSerializer(TainoBaseSerializer):
    """Serializer for sending SMS messages"""

    recipient_number = serializers.CharField(max_length=20)
    recipient_name = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    message = serializers.CharField()
    client_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    case_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    calendar_event_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_recipient_number(self, value):
        # Basic validation for recipient number
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid phone number")
        return value

    def validate(self, attrs):
        # Additional validation if needed
        return attrs

    def create(self, validated_data):
        from apps.messaging.services.sms_service import SMSService
        from apps.lawyer_office.models import Client, LawOfficeCase
        from apps.court_calendar.models import CourtCalendarEvent

        user = self.context["request"].user
        recipient_number = validated_data.get("recipient_number")
        recipient_name = validated_data.get("recipient_name")
        message = validated_data.get("message")

        # Get related objects if IDs are provided
        client = None
        case = None
        calendar_event = None

        if validated_data.get("client_id"):
            try:
                client = Client.objects.get(pid=validated_data.get("client_id"))
            except Client.DoesNotExist:
                pass

        if validated_data.get("case_id"):
            try:
                case = LawOfficeCase.objects.get(pid=validated_data.get("case_id"))
            except LawOfficeCase.DoesNotExist:
                pass

        if validated_data.get("calendar_event_id"):
            try:
                calendar_event = CourtCalendarEvent.objects.get(pid=validated_data.get("calendar_event_id"))
            except CourtCalendarEvent.DoesNotExist:
                pass

        # Send SMS
        success, sms_message = SMSService.send_sms(
            user=user,
            recipient_number=recipient_number,
            message_content=message,
            recipient_name=recipient_name,
            client=client,
            case=case,
            calendar_event=calendar_event,
        )

        # Check balance first before attempting to send
        if sms_message.status == "insufficient_balance":
            raise serializers.ValidationError(
                {"detail": "Insufficient SMS balance", "balance": SMSService.check_user_sms_balance(user)}
            )

        # Return result
        return {
            "success": success,
            "message_id": sms_message.pid,
            "status": sms_message.status,
            "balance": SMSService.check_user_sms_balance(user),
        }

    def to_representation(self, instance):
        return instance


class SMSSendWithTemplateSerializer(TainoBaseSerializer):
    """Serializer for sending SMS messages using templates"""

    template_code = serializers.CharField()
    recipient_number = serializers.CharField(max_length=20)
    recipient_name = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    context = serializers.DictField()
    client_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    case_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    calendar_event_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_template_code(self, value):
        # Check if template exists
        try:
            SystemSMSTemplate.objects.get(code=value, is_active=True)
        except SystemSMSTemplate.DoesNotExist:
            raise serializers.ValidationError(f"Template with code '{value}' does not exist")
        return value

    def create(self, validated_data):
        from apps.messaging.services.sms_service import SMSService
        from apps.lawyer_office.models import Client, LawOfficeCase
        from apps.court_calendar.models import CourtCalendarEvent

        user = self.context["request"].user
        template_code = validated_data.get("template_code")
        recipient_number = validated_data.get("recipient_number")
        recipient_name = validated_data.get("recipient_name")
        context = validated_data.get("context")

        # Get related objects if IDs are provided
        client = None
        case = None
        calendar_event = None

        if validated_data.get("client_id"):
            try:
                client = Client.objects.get(pid=validated_data.get("client_id"))
            except Client.DoesNotExist:
                pass

        if validated_data.get("case_id"):
            try:
                case = LawOfficeCase.objects.get(pid=validated_data.get("case_id"))
            except LawOfficeCase.DoesNotExist:
                pass

        if validated_data.get("calendar_event_id"):
            try:
                calendar_event = CourtCalendarEvent.objects.get(pid=validated_data.get("calendar_event_id"))
            except CourtCalendarEvent.DoesNotExist:
                pass

        # Send SMS with template
        success, sms_message = SMSService.send_sms_with_template(
            user=user,
            template_code=template_code,
            recipient_number=recipient_number,
            context=context,
            recipient_name=recipient_name,
            client=client,
            case=case,
            calendar_event=calendar_event,
        )

        # Check balance first
        if sms_message.status == "insufficient_balance":
            raise serializers.ValidationError(
                {"detail": "Insufficient SMS balance", "balance": SMSService.check_user_sms_balance(user)}
            )

        # Return result
        return {
            "success": success,
            "message_id": sms_message.pid,
            "status": sms_message.status,
            "balance": SMSService.check_user_sms_balance(user),
        }

    def to_representation(self, instance):
        return instance


class SystemSMSTemplateSerializer(TainoBaseModelSerializer):
    """Serializer for system SMS templates"""

    class Meta:
        model = SystemSMSTemplate
        fields = ["pid", "code", "name", "template_content", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = fields
