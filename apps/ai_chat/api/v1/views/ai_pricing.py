# apps/ai_chat/api/v1/views.py
import logging

from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, inline_serializer
from base_utils.permissions import HasTainoMobileUserPermission
from base_utils.views.mobile import TainoMobileGenericViewSet

from apps.ai_chat.api.v1.serializers import (
    ChatAIConfigSerializer,
    AIPricingPreviewSerializer,
    AIPricingResponseSerializer,
    StepOptionsRequestSerializer,
    StepOptionsResponseSerializer,
    AIChargeRequestSerializer,
)


from apps.ai_chat.services.ai_pricing_calculator import AIPricingCalculator

logger = logging.getLogger(__name__)


class AIPricingViewSet(TainoMobileGenericViewSet):
    """
    ViewSet برای عملیات قیمت‌گذاری هوش مصنوعی
    """

    permission_classes = [IsAuthenticated, HasTainoMobileUserPermission]

    @extend_schema(
        request=AIPricingPreviewSerializer,
        responses={200: AIPricingResponseSerializer},
        description="پیش‌نمایش هزینه قبل از ارسال درخواست به هوش مصنوعی",
    )
    @action(detail=False, methods=["POST"], url_path="preview")
    def preview_cost(self, request):
        """
        پیش‌نمایش هزینه

        این endpoint برای نمایش هزینه به کاربر قبل از ارسال درخواست استفاده می‌شود.
        """
        serializer = AIPricingPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = AIPricingCalculator.preview_cost(
            ai_config_static_name=serializer.validated_data["ai_config_static_name"],
            character_count=serializer.validated_data["character_count"],
            max_tokens_requested=serializer.validated_data.get("max_tokens_requested"),
        )

        return Response(result)

    @extend_schema(
        request=AIPricingPreviewSerializer,
        responses={200: AIPricingResponseSerializer},
        description="محاسبه هزینه با در نظر گرفتن اشتراک و شرایط بای‌پس",
    )
    @action(detail=False, methods=["POST"], url_path="calculate")
    def calculate_with_bypass(self, request):
        """
        محاسبه هزینه با بررسی شرایط بای‌پس

        این endpoint علاوه بر محاسبه هزینه، اشتراک کاربر و شرایط ویژه را نیز بررسی می‌کند.
        """
        serializer = AIPricingPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = AIPricingCalculator.calculate_with_bypass(
            user=request.user,
            ai_config_static_name=serializer.validated_data["ai_config_static_name"],
            character_count=serializer.validated_data["character_count"],
            max_tokens_requested=serializer.validated_data.get("max_tokens_requested"),
        )

        return Response(result)

    @extend_schema(
        request=AIChargeRequestSerializer,
        responses={200: AIPricingResponseSerializer},
        description="شارژ کاربر و کسر هزینه از کیف پول",
    )
    @action(detail=False, methods=["POST"], url_path="charge")
    def charge_user(self, request):
        """
        شارژ کاربر

        این endpoint برای کسر هزینه از کیف پول کاربر استفاده می‌شود.
        قبل از شارژ، تطابق تعداد کاراکترهای فرانت و بک را بررسی می‌کند.
        """
        serializer = AIChargeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # اعتبارسنجی تطابق فرانت و بک
        is_valid, error = AIPricingCalculator.validate_request(
            ai_config_static_name=serializer.validated_data["ai_config_static_name"],
            character_count_frontend=serializer.validated_data["character_count_frontend"],
            character_count_backend=serializer.validated_data["character_count_backend"],
            max_tokens_requested=serializer.validated_data.get("max_tokens_requested"),
        )

        if not is_valid:
            return Response({"success": False, "error": error}, status=status.HTTP_400_BAD_REQUEST)

        # شارژ کاربر
        success, message, details = AIPricingCalculator.charge_user(
            user=request.user,
            ai_config_static_name=serializer.validated_data["ai_config_static_name"],
            character_count=serializer.validated_data["character_count_backend"],
            max_tokens_requested=serializer.validated_data.get("max_tokens_requested"),
            description=serializer.validated_data.get("description"),
        )

        if not success:
            return Response({"success": False, "error": message, **details}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"success": True, "message": message, **details})

    @extend_schema(
        request=StepOptionsRequestSerializer,
        responses={200: StepOptionsResponseSerializer},
        description="دریافت گزینه‌های استپ برای انتخاب max_tokens",
    )
    @action(detail=False, methods=["POST"], url_path="step-options")
    def get_step_options(self, request):
        """
        دریافت گزینه‌های استپ

        این endpoint لیست گزینه‌های قابل انتخاب برای max_tokens را به همراه
        هزینه هر گزینه برمی‌گرداند.

        فقط برای کانفیگ‌های هیبریدی کار می‌کند.
        """
        serializer = StepOptionsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = AIPricingCalculator.get_step_options(
            ai_config_static_name=serializer.validated_data["ai_config_static_name"]
        )

        if not result.get("success"):
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(result)

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {"success": {"type": "boolean"}, "configs": {"type": "array", "items": {"type": "object"}}},
            }
        },
        description="دریافت لیست تمام کانفیگ‌های فعال با جزئیات قیمت‌گذاری",
    )
    @action(detail=False, methods=["GET"], url_path="configs")
    def list_configs(self, request):
        """
        لیست کانفیگ‌های فعال

        این endpoint لیست تمام کانفیگ‌های هوش مصنوعی فعال را به همراه
        جزئیات قیمت‌گذاری هر یک برمی‌گرداند.
        """
        from apps.ai_chat.models import ChatAIConfig

        configs = ChatAIConfig.objects.filter(is_active=True).select_related("general_config").order_by("order", "strength")

        serializer = ChatAIConfigSerializer(configs, many=True)

        return Response({"success": True, "configs": serializer.data})

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "character_count": {"type": "integer"},
                    "validation": {
                        "type": "object",
                        "properties": {"is_valid": {"type": "boolean"}, "message": {"type": "string"}},
                    },
                },
            }
        },
        description="شمارش کاراکترها و اعتبارسنجی متن",
    )
    @action(detail=False, methods=["POST"], url_path="count-characters")
    def count_characters(self, request):
        """
        شمارش کاراکترها

        این endpoint برای تست و اعتبارسنجی شمارش کاراکترها در فرانت استفاده می‌شود.
        """
        text = request.data.get("text", "")

        if not text:
            return Response(
                {"character_count": 0, "validation": {"is_valid": False, "message": "متن خالی است"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        char_count = AIPricingCalculator.count_characters(text)

        return Response(
            {
                "character_count": char_count,
                "text_length": len(text),
                "validation": {"is_valid": True, "message": "شمارش موفق"},
            }
        )

    @extend_schema(
        request=inline_serializer(
            name="RealtimeCostPreviewRequest",
            fields={
                "ai_config_static_name": serializers.CharField(required=True),
                "message_text": serializers.CharField(required=True),
                "max_tokens_requested": serializers.IntegerField(required=False),
            },
        ),
        responses={200: AIPricingResponseSerializer},
        description="محاسبه هزینه در زمان واقعی هنگام تایپ کاربر",
    )
    @action(detail=False, methods=["POST"], url_path="realtime-preview")
    def realtime_cost_preview(self, request):
        """
        محاسبه و نمایش هزینه در زمان واقعی

        این endpoint برای فراخوانی در زمان تایپ کاربر طراحی شده
        و باید خیلی سریع پاسخ دهد.
        """
        try:
            ai_config_static_name = request.data.get("ai_config_static_name")
            message_text = request.data.get("message_text", "")
            max_tokens_requested = request.data.get("max_tokens_requested")

            if not ai_config_static_name:
                return Response(
                    {"success": False, "error": "ai_config_static_name الزامی است"}, status=status.HTTP_400_BAD_REQUEST
                )

            # شمارش کاراکترها
            character_count = AIPricingCalculator.count_characters(message_text)

            # محاسبه با بررسی بای‌پس
            result = AIPricingCalculator.calculate_with_bypass(
                user=request.user,
                ai_config_static_name=ai_config_static_name,
                character_count=character_count,
                max_tokens_requested=max_tokens_requested,
            )

            if not result.get("success"):
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

            # افزودن اطلاعات اضافی برای UI
            result["character_count"] = character_count
            result["message_length"] = len(message_text)

            # اگر قیمت‌گذاری هیبریدی است، جزئیات بیشتر
            if result.get("pricing_type") == "advanced_hybrid":
                # محاسبه درصد استفاده از کاراکترهای رایگان
                ai_config = AIPricingCalculator.get_ai_config(ai_config_static_name)
                if ai_config:
                    free_char_usage_percent = min(
                        100, (character_count / ai_config.hybrid_free_chars * 100) if ai_config.hybrid_free_chars > 0 else 0
                    )
                    result["free_char_usage_percent"] = round(free_char_usage_percent, 1)

            return Response(result)

        except Exception as e:
            logger.error(f"Error in realtime cost preview: {e}")
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        request=inline_serializer(
            name="BatchCostPreviewRequest",
            fields={
                "ai_config_static_name": serializers.CharField(required=True),
                "messages": serializers.ListField(
                    child=inline_serializer(
                        name="MessageItem",
                        fields={"text": serializers.CharField(), "max_tokens": serializers.IntegerField(required=False)},
                    )
                ),
            },
        ),
        responses={200: serializers.ListField(child=AIPricingResponseSerializer())},
        description="محاسبه هزینه برای چند پیام به صورت یکجا",
    )
    @action(detail=False, methods=["POST"], url_path="batch-preview")
    def batch_cost_preview(self, request):
        """
        محاسبه هزینه برای چند پیام به صورت یکجا

        برای نمایش پیش‌نمایش هزینه در سناریوهایی که کاربر
        می‌خواهد چند پیام پشت سر هم بفرستد.
        """
        try:
            ai_config_static_name = request.data.get("ai_config_static_name")
            messages = request.data.get("messages", [])

            if not ai_config_static_name:
                return Response(
                    {"success": False, "error": "ai_config_static_name الزامی است"}, status=status.HTTP_400_BAD_REQUEST
                )

            results = []
            total_cost = 0

            for i, msg in enumerate(messages, 1):
                message_text = msg.get("text", "")
                max_tokens = msg.get("max_tokens")

                char_count = AIPricingCalculator.count_characters(message_text)

                result = AIPricingCalculator.calculate_with_bypass(
                    user=request.user,
                    ai_config_static_name=ai_config_static_name,
                    character_count=char_count,
                    max_tokens_requested=max_tokens,
                )

                result["message_index"] = i
                result["character_count"] = char_count

                if result.get("success") and not result.get("is_free"):
                    total_cost += result.get("total_cost", 0)

                results.append(result)

            return Response({"success": True, "messages": results, "total_cost": total_cost, "message_count": len(messages)})

        except Exception as e:
            logger.error(f"Error in batch cost preview: {e}")
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
