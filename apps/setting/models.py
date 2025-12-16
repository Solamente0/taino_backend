from django.contrib.auth import get_user_model
from django.db import models

from base_utils.base_models import (
    TimeStampModel,
    CreatorModel,
    ActivableModel,
)


class GeneralSettingChoices(models.TextChoices):
    HELP_CENTER_TERMS = "help_center.terms", "help_center.terms"
    HELP_CENTER_FAQ = "help_center.faq", "help_center.faq"

    # AI Chat Pricing Settings
    AI_CHAT_PRICE_V = "ai_chat.price.v", "قیمت هوش مصنوعی وی"
    AI_CHAT_PRICE_V_PLUS = "ai_chat.price.v_plus", "قیمت هوش مصنوعی وی پلاس"
    AI_CHAT_PRICE_V_X = "ai_chat.price.v_x", "قیمت هوش مصنوعی وی ایکس"

    AI_CHAT_PRICE_V_PRO = "ai_chat.price.v_pro", "قیمت هوش مصنوعی وی پرو"
    AI_CHAT_PRICE_V_PLUS_PRO = "ai_chat.price.v_plus_pro", "قیمت هوش مصنوعی وی پلاس پرو"
    AI_CHAT_PRICE_V_X_PRO = "ai_chat.price.v_x_pro", "قیمت هوش مصنوعی وی ایکس پرو"

    AI_CHAT_PRICE_V_MANUAL_REQUEST = "ai_chat.price.v_manual_request", "قیمت هوش مصنوعی درخواست دستی"

    AI_CHAT_PRICE_V_MADE_477 = "ai_chat.price.v_made_477", "قیمت هوش مصنوعی ماده ۴۴۷"
    AI_CHAT_PRICE_V_PREPARE_INITIAL_PETITION = "ai_chat.price.v_prepare_initial_petition", "قیمت هوش مصنوعی تنظیم دادخواست"
    AI_CHAT_PRICE_V_PREPARE_APPEAL_PETITION = (
        "ai_chat.price.v_prepare_appeal_petition",
        "قیمت هوش مصنوعی تنظیم تجدید نظر خواهی",
    )
    AI_CHAT_PRICE_V_PREPARE_DEFENSE_BRIEF = "ai_chat.price.v_prepare_defense_brief", "قیمت هوش مصنوعی تنظیم لایحه دفاعی"
    AI_CHAT_PRICE_V_PREPARE_CUSTOM_REQUEST = "ai_chat.price.v_prepare_custom_request", "قیمت هوش مصنوعی سایر درخواست ها"

    AI_CHAT_DURATION = "ai_chat.duration", "مدت زمان چت با هوش مصنوعی"

    LAWYER_REGISTER_PRIZE_COIN = "wallet.lawyer_register_prize_coin", "سکه هدیه برای ثبت نام وکیل"
    USER_REGISTER_PRIZE_COIN = "wallet.user_register_prize_coin", "سکه هدیه برای ثبت نام کاربر عادی"

    NOTIFICATION_RETENTION_DAYS = "notification.retention_days", "حداقل روز پاک شدن آلارم"

    COST_PER_SMS = "messaging.cost_per_sms", "تعداد پیام کسر شونده"

    BYPASS_PREMIUM_FEATURE_FOR_ROLES = (
        "subscription.bypass_premium_feature_per_roles",
        "نقشهایی که با داشتن اشتراک دسترسی بدون مصرف سکه دارند",
    )

    DISABLE_SUBSCRIPTION_FOR_LAWYER = (
        "subscription.disable_subscription_for_lawyer",
        "غیر فعال سازی اشتراک در کل سیستم برای وکلا",
    )

    DISABLE_SUBSCRIPTION_FOR_CLIENT = (
        "subscription.disable_subscription_for_client",
        "غیر فعال سازی اشتراک در کل سیستم برای کل مشتری ها",
    )


class GeneralSetting(TimeStampModel, CreatorModel, ActivableModel):
    creator = models.ForeignKey(to=get_user_model(), null=True, on_delete=models.CASCADE, related_name="%(class)s_creator")
    key = models.CharField(max_length=255, choices=GeneralSettingChoices.choices, unique=True, db_index=True)
    value = models.CharField(max_length=255)

    class Meta:
        verbose_name = "تنظیم عمومی"
        verbose_name_plural = "تنظیمات عمومی"
