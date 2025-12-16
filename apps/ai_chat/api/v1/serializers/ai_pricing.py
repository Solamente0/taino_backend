from rest_framework import serializers

from base_utils.serializers.base import TainoBaseSerializer


class AIPricingPreviewSerializer(TainoBaseSerializer):
    """سریالایزر برای درخواست پیش‌نمایش قیمت"""

    ai_config_static_name = serializers.CharField(
        required=True, help_text="نام استاتیک کانفیگ (مثل: 'chat_with_ai_very_strong')"
    )

    # برای قیمت‌گذاری هیبریدی
    character_count = serializers.IntegerField(required=True, min_value=0, help_text="تعداد کاراکترهای متن ورودی")

    max_tokens_requested = serializers.IntegerField(
        required=False, allow_null=True, min_value=100, help_text="مقدار max_tokens درخواستی (برای هیبریدی)"
    )


class AIPricingResponseSerializer(TainoBaseSerializer):
    """سریالایزر برای پاسخ قیمت"""

    success = serializers.BooleanField()
    error = serializers.CharField(required=False, allow_null=True)

    # اطلاعات کانفیگ
    ai_config = serializers.DictField(required=False)

    # اطلاعات قیمت
    pricing_type = serializers.CharField(required=False)
    is_free = serializers.BooleanField(required=False, default=False)
    bypass_reason = serializers.CharField(required=False, allow_null=True)

    # جزئیات هزینه - قیمت ثابت
    cost = serializers.FloatField(required=False)

    # جزئیات هزینه - قیمت هیبریدی
    character_count = serializers.IntegerField(required=False)
    max_tokens_requested = serializers.IntegerField(required=False)
    base_cost = serializers.FloatField(required=False)
    char_cost = serializers.FloatField(required=False)
    step_cost = serializers.FloatField(required=False)
    total_cost = serializers.FloatField(required=False)

    # پیام
    message = serializers.CharField(required=False)
    warning = serializers.CharField(required=False)


class AIChargeRequestSerializer(TainoBaseSerializer):
    """سریالایزر برای درخواست شارژ"""

    ai_config_static_name = serializers.CharField(required=True, help_text="نام استاتیک کانفیگ")

    character_count_frontend = serializers.IntegerField(
        required=True, min_value=0, help_text="تعداد کاراکترهای شمارش شده در فرانت"
    )

    character_count_backend = serializers.IntegerField(
        required=True, min_value=0, help_text="تعداد کاراکترهای شمارش شده در بک (برای اعتبارسنجی)"
    )

    max_tokens_requested = serializers.IntegerField(
        required=False, allow_null=True, min_value=100, help_text="مقدار max_tokens درخواستی (برای هیبریدی)"
    )

    description = serializers.CharField(required=False, allow_blank=True, help_text="توضیحات تراکنش")


class StepOptionsRequestSerializer(TainoBaseSerializer):
    """سریالایزر برای درخواست گزینه‌های استپ"""

    ai_config_static_name = serializers.CharField(required=True, help_text="نام استاتیک کانفیگ")


class StepOptionsResponseSerializer(TainoBaseSerializer):
    """سریالایزر برای پاسخ گزینه‌های استپ"""

    success = serializers.BooleanField()
    error = serializers.CharField(required=False, allow_null=True)

    min_tokens = serializers.IntegerField(required=False)
    max_tokens = serializers.IntegerField(required=False)
    step_size = serializers.IntegerField(required=False)
    cost_per_step = serializers.FloatField(required=False)

    options = serializers.ListField(child=serializers.DictField(), required=False)
