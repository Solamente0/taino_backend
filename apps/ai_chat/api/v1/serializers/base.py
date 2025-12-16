from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.ai_chat.models import ChatAIConfig, GeneralChatAIConfig
from base_utils.base64 import Base64FileField
from base_utils.numbers import safe_decimal_to_float
from base_utils.serializers.base import TainoBaseModelSerializer, TainoBaseSerializer

User = get_user_model()


class AIUserSerializer(TainoBaseModelSerializer):
    """Serializer for user reference in AI chat"""

    class Meta:
        model = User
        fields = ["pid", "first_name", "last_name", "avatar"]


class GeneralChatAIConfigSerializer(serializers.ModelSerializer):
    """Serializer for GeneralChatAIConfig"""

    icon_url = serializers.SerializerMethodField()
    ai_configs_count = serializers.SerializerMethodField()

    class Meta:
        model = GeneralChatAIConfig
        fields = [
            "pid",
            "static_name",
            "name",
            "description",
            "max_messages_per_chat",
            "max_tokens_per_chat",
            "order",
            "icon",
            "icon_url",
            "ai_configs_count",
            "created_at",
            "updated_at",
            "is_active",
            "form_schema",
        ]

    def get_icon_url(self, obj):
        if obj.icon:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.icon.url)
        return None

    def get_ai_configs_count(self, obj):
        return obj.ai_configs.filter(is_active=True).count()


class ChatAIConfigSerializer(serializers.ModelSerializer):
    """Serializer for ChatAIConfig with all pricing information"""

    general_config = GeneralChatAIConfigSerializer(read_only=True)
    related_service = serializers.SerializerMethodField()
    strength_display = serializers.CharField(source="get_strength_display", read_only=True)
    pricing_type_display = serializers.CharField(source="get_pricing_type_display", read_only=True)

    # Pricing fields
    is_message_based = serializers.BooleanField(source="is_message_based_pricing", read_only=True)
    is_advanced_hybrid = serializers.BooleanField(source="is_advanced_hybrid_pricing", read_only=True)

    # Hybrid pricing info
    hybrid_info = serializers.SerializerMethodField()
    step_options = serializers.SerializerMethodField()

    # ✅ ADD FILE PRICING FIELDS
    cost_per_page = serializers.SerializerMethodField()
    free_pages = serializers.SerializerMethodField()
    max_pages_per_request = serializers.IntegerField(read_only=True)

    cost_per_minute = serializers.SerializerMethodField()
    free_minutes = serializers.SerializerMethodField()
    max_minutes_per_request = serializers.IntegerField(read_only=True)

    class Meta:
        model = ChatAIConfig
        fields = [
            "pid",
            "static_name",
            "general_config",
            "related_service",
            "name",
            "strength",
            "strength_display",
            "description",
            "model_name",
            "base_url",
            "default_temperature",
            "default_max_tokens",
            "rate_limit_per_minute",
            # Pricing type
            "pricing_type",
            "pricing_type_display",
            "is_message_based",
            "is_advanced_hybrid",
            # Message-based pricing
            "cost_per_message",
            # Hybrid pricing
            "hybrid_base_cost",
            "hybrid_char_per_coin",
            "hybrid_free_chars",
            "hybrid_tokens_min",
            "hybrid_tokens_max",
            "hybrid_tokens_step",
            "hybrid_cost_per_step",
            "hybrid_info",
            "step_options",
            # ✅ File pricing
            "cost_per_page",
            "free_pages",
            "max_pages_per_request",
            # Voice Pricing
            "cost_per_minute",
            "free_minutes",
            "max_minutes_per_request",
            # Meta
            "is_default",
            "order",
            "created_at",
            "updated_at",
            "is_active",
        ]

    def get_related_service(self, obj):
        if obj.related_service:
            return {"pid": obj.related_service.pid, "name": obj.related_service.name}
        return None

    def get_free_pages(self, obj):
        """Return free pages count"""
        return obj.free_pages

    def get_cost_per_page(self, obj):
        """Ctainoert cost_per_page to float"""
        return safe_decimal_to_float(obj.cost_per_page)

    def get_free_minutes(self, obj):
        """Return free pages count"""
        return obj.free_minutes

    def get_cost_per_minute(self, obj):
        """Ctainoert cost_per_page to float"""
        return safe_decimal_to_float(obj.cost_per_minute)

    def get_hybrid_info(self, obj):
        """Get detailed hybrid pricing information"""
        if not obj.is_advanced_hybrid_pricing():
            return None

        return {
            "base_cost": safe_decimal_to_float(obj.hybrid_base_cost),
            "char_pricing": {
                "chars_per_coin": obj.hybrid_char_per_coin,
                "free_chars": obj.hybrid_free_chars,
                "description": f"هر {obj.hybrid_char_per_coin} کاراکتر = 1 سکه (بعد از {obj.hybrid_free_chars} کاراکتر اول)",
            },
            "token_pricing": {
                "min_tokens": obj.hybrid_tokens_min,
                "max_tokens": obj.hybrid_tokens_max,
                "step_size": obj.hybrid_tokens_step,
                "cost_per_step": safe_decimal_to_float(obj.hybrid_cost_per_step),
                "description": f"هر {obj.hybrid_tokens_step} توکن = {safe_decimal_to_float(obj.hybrid_cost_per_step)} سکه",
            },
            "file_pricing": {
                "cost_per_page": safe_decimal_to_float(obj.cost_per_page),
                "free_pages": obj.free_pages,
                "max_pages": obj.max_pages_per_request,
                "description": f"{obj.free_pages} صفحه اول رایگان، سپس هر صفحه {safe_decimal_to_float(obj.cost_per_page)} سکه (حداکثر {obj.max_pages_per_request} صفحه)",
            },
            "voice_pricing": {
                "cost_per_minute": safe_decimal_to_float(obj.cost_per_minute),
                "free_minutes": obj.free_minutes,
                "max_minutes": obj.max_minutes_per_request,
                "description": f"{obj.free_minutes} دقیقه اول رایگان، سپس هر دقیقه {safe_decimal_to_float(obj.cost_per_minute)} سکه (حداکثر {obj.max_minutes_per_request} دقیقه)",
            },
            "how_it_works": {
                "step_1": f"هزینه پایه: {safe_decimal_to_float(obj.hybrid_base_cost)} سکه",
                "step_2": f"هزینه کاراکتر: بعد از {obj.hybrid_free_chars} کاراکتر رایگان، هر {obj.hybrid_char_per_coin} کاراکتر 1 سکه",
                "step_3": f"هزینه توکن: از {obj.hybrid_tokens_min} تا {obj.hybrid_tokens_max} توکن، هر {obj.hybrid_tokens_step} توکن {safe_decimal_to_float(obj.hybrid_cost_per_step)} سکه",
                "step_4": f"هزینه فایل: {safe_decimal_to_float(obj.cost_per_page)} سکه به ازای هر صفحه/عکس",
            },
        }

    def get_step_options(self, obj):
        """Get token step options"""
        if not obj.is_advanced_hybrid_pricing():
            return None

        return obj.get_step_options()
