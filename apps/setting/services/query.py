from django.db.models import QuerySet
from django.core.cache import cache

from apps.setting.models import GeneralSettingChoices, GeneralSetting
from base_utils.services import AbstractBaseQuery


class GeneralSettingsQuery(AbstractBaseQuery):
    # Cache settings
    CACHE_PREFIX = "general_settings"
    CACHE_TTL = 60 * 60 * 24 * 365  # a year in seconds

    # Default values remain the same
    DEFAULT_AI_CHAT_PRICE_V = 1
    DEFAULT_AI_CHAT_PRICE_V_PLUS = 2
    DEFAULT_AI_CHAT_PRICE_V_X = 6

    DEFAULT_AI_CHAT_PRICE_V_MANUAL_REQUEST = 12

    DEFAULT_AI_CHAT_PRICE_V_MADE_477 = 12
    DEFAULT_AI_CHAT_PRICE_V_PREPARE_INITIAL_PETITION = 12
    DEFAULT_AI_CHAT_PRICE_V_PREPARE_APPEAL_PETITION = 12
    DEFAULT_AI_CHAT_PRICE_V_PREPARE_DEFENSE_BRIEF = 12
    DEFAULT_AI_CHAT_PRICE_V_PREPARE_CUSTOM_REQUEST = 12

    DEFAULT_AI_CHAT_PRICE_V_PRO = 5
    DEFAULT_AI_CHAT_PRICE_V_PLUS_PRO = 10
    DEFAULT_AI_CHAT_PRICE_V_X_PRO = 15

    AI_CHAT_DURATION = 6
    DEFAULT_LAWYER_REGISTER_PRIZE_COIN = 50
    DEFAULT_USER_REGISTER_PRIZE_COIN = 10
    DEFAULT_COST_PER_SMS = 2

    @classmethod
    def _get_cache_key(cls, key):
        """Generate a cache key for a setting"""
        return f"{cls.CACHE_PREFIX}:{key}"

    @classmethod
    def _get_from_cache(cls, key):
        """Get a setting value from cache"""
        cache_key = cls._get_cache_key(key)
        return cache.get(cache_key)

    @classmethod
    def _set_in_cache(cls, key, value):
        """Set a setting value in cache"""
        cache_key = cls._get_cache_key(key)
        cache.set(cache_key, value, cls.CACHE_TTL)

    @classmethod
    def _invalidate_cache(cls, key):
        """Invalidate a specific setting cache"""
        cache_key = cls._get_cache_key(key)
        cache.delete(cache_key)

    @classmethod
    def invalidate_all_caches(cls):
        """Invalidate all settings caches"""
        keys = GeneralSetting.objects.values_list("key", flat=True)
        for key in keys:
            cls._invalidate_cache(key)

    @staticmethod
    def get_visible_mobile_settings() -> QuerySet[GeneralSetting]:
        # This method returns a queryset, so we don't cache it
        return GeneralSetting.objects.filter(
            is_active=True,
            key__in=[
                GeneralSettingChoices.HELP_CENTER_FAQ.value,
                GeneralSettingChoices.HELP_CENTER_TERMS.HELP_CENTER_TERMS,
                GeneralSettingChoices.AI_CHAT_PRICE_V.value,
                GeneralSettingChoices.AI_CHAT_PRICE_V_PLUS.value,
                GeneralSettingChoices.AI_CHAT_PRICE_V_X.value,
                GeneralSettingChoices.AI_CHAT_PRICE_V_PRO.value,
                GeneralSettingChoices.AI_CHAT_PRICE_V_PLUS_PRO.value,
                GeneralSettingChoices.AI_CHAT_PRICE_V_X_PRO.value,
                GeneralSettingChoices.AI_CHAT_PRICE_V_MADE_477.value,
                GeneralSettingChoices.AI_CHAT_PRICE_V_PREPARE_INITIAL_PETITION.value,
                GeneralSettingChoices.AI_CHAT_PRICE_V_PREPARE_APPEAL_PETITION.value,
                GeneralSettingChoices.AI_CHAT_PRICE_V_PREPARE_DEFENSE_BRIEF.value,
                GeneralSettingChoices.AI_CHAT_PRICE_V_PREPARE_CUSTOM_REQUEST.value,
                GeneralSettingChoices.AI_CHAT_DURATION.value,
                GeneralSettingChoices.LAWYER_REGISTER_PRIZE_COIN.value,
                GeneralSettingChoices.USER_REGISTER_PRIZE_COIN.value,
                GeneralSettingChoices.NOTIFICATION_RETENTION_DAYS.value,
                GeneralSettingChoices.COST_PER_SMS.value,
                GeneralSettingChoices.BYPASS_PREMIUM_FEATURE_FOR_ROLES.value,
            ],
        )

    @classmethod
    def get_lawyer_register_prize_coin(cls) -> int:
        """Get prize coins for lawyer registration"""
        key = GeneralSettingChoices.LAWYER_REGISTER_PRIZE_COIN.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return cls.DEFAULT_LAWYER_REGISTER_PRIZE_COIN

    @classmethod
    def get_user_register_prize_coin(cls) -> int:
        """Get prize coins for user registration"""
        key = GeneralSettingChoices.USER_REGISTER_PRIZE_COIN.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return cls.DEFAULT_USER_REGISTER_PRIZE_COIN

    @classmethod
    def get_ai_chat_price_v(cls) -> int:
        """Get price for V AI chat"""
        key = GeneralSettingChoices.AI_CHAT_PRICE_V.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return cls.DEFAULT_AI_CHAT_PRICE_V

    @classmethod
    def get_ai_chat_price_v_plus(cls) -> int:
        """Get price for V+ AI chat"""
        key = GeneralSettingChoices.AI_CHAT_PRICE_V_PLUS.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return cls.DEFAULT_AI_CHAT_PRICE_V_PLUS

    @classmethod
    def get_ai_chat_price_v_x(cls) -> int:
        """Get price for V++ AI chat"""
        key = GeneralSettingChoices.AI_CHAT_PRICE_V_X.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return cls.DEFAULT_AI_CHAT_PRICE_V_X

    @classmethod
    def get_ai_chat_price_v_pro(cls) -> int:
        """Get price for V AI chat"""
        key = GeneralSettingChoices.AI_CHAT_PRICE_V_PRO.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return cls.DEFAULT_AI_CHAT_PRICE_V_PRO

    @classmethod
    def get_ai_chat_price_v_plus_pro(cls) -> int:
        """Get price for V+ AI chat"""
        key = GeneralSettingChoices.AI_CHAT_PRICE_V_PLUS_PRO.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return cls.DEFAULT_AI_CHAT_PRICE_V_PLUS_PRO

    @classmethod
    def get_ai_chat_price_v_manual_request(cls) -> int:
        """Get price for V Manual Request AI chat"""
        key = GeneralSettingChoices.AI_CHAT_PRICE_V_MANUAL_REQUEST.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return cls.DEFAULT_AI_CHAT_PRICE_V_MANUAL_REQUEST

    @classmethod
    def get_ai_chat_price_v_made_477(cls) -> int:
        """Get price for V Made 477 AI chat"""
        key = GeneralSettingChoices.AI_CHAT_PRICE_V_MADE_477.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return cls.DEFAULT_AI_CHAT_PRICE_V_MADE_477

    @classmethod
    def get_ai_chat_price_v_prepare_initial_petition(cls) -> int:
        """Get price for V_PREPARE_INITIAL_PETITION AI chat"""
        key = GeneralSettingChoices.AI_CHAT_PRICE_V_PREPARE_INITIAL_PETITION.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return cls.DEFAULT_AI_CHAT_PRICE_V_PREPARE_INITIAL_PETITION

    @classmethod
    def get_ai_chat_price_v_prepare_appeal_petition(cls) -> int:
        """Get price for V_PREPARE_APPEAL_PETITION AI chat"""
        key = GeneralSettingChoices.AI_CHAT_PRICE_V_PREPARE_APPEAL_PETITION.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return cls.DEFAULT_AI_CHAT_PRICE_V_PREPARE_APPEAL_PETITION

    @classmethod
    def get_ai_chat_price_v_prepare_defense_brief(cls) -> int:
        """Get price for V_PREPARE_DEFENSE_BRIEF AI chat"""
        key = GeneralSettingChoices.AI_CHAT_PRICE_V_PREPARE_DEFENSE_BRIEF.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return cls.DEFAULT_AI_CHAT_PRICE_V_PREPARE_DEFENSE_BRIEF

    @classmethod
    def get_ai_chat_price_v_prepare_custom_request(cls) -> int:
        """Get price for V_PREPARE_CUSTOM_REQUEST AI chat"""
        key = GeneralSettingChoices.AI_CHAT_PRICE_V_PREPARE_CUSTOM_REQUEST.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return cls.DEFAULT_AI_CHAT_PRICE_V_PREPARE_CUSTOM_REQUEST

    @classmethod
    def get_ai_chat_price_v_x_pro(cls) -> int:
        """Get price for VX Pro AI chat"""
        key = GeneralSettingChoices.AI_CHAT_PRICE_V_X_PRO.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return cls.DEFAULT_AI_CHAT_PRICE_V_X_PRO

    @classmethod
    def get_ai_chat_duration(cls) -> int:
        """Get duration in minutes for AI chat"""
        key = GeneralSettingChoices.AI_CHAT_DURATION.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return cls.AI_CHAT_DURATION

    @classmethod
    def get_notification_retention_days(cls) -> int:
        """Get number of days to retain notifications"""
        key = GeneralSettingChoices.NOTIFICATION_RETENTION_DAYS.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return 5  # Default to 5 days if not specified

    @classmethod
    def get_message_cost(cls) -> int:
        """Get duration in minutes for AI chat"""
        key = GeneralSettingChoices.COST_PER_SMS.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return cls.DEFAULT_COST_PER_SMS

    @classmethod
    def get_bypass_premium_feature_per_roles(cls) -> list:
        """Get duration in minutes for AI chat"""
        key = GeneralSettingChoices.BYPASS_PREMIUM_FEATURE_FOR_ROLES.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = GeneralSetting.objects.get(key=key).value
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value.split(",")
        except:
            return []

    @classmethod
    def get_disable_subscription_for_lawyer(cls) -> int:
        """Get disable_subscription_for_lawyer"""
        key = GeneralSettingChoices.DISABLE_SUBSCRIPTION_FOR_LAWYER.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return 0

    @classmethod
    def get_disable_subscription_for_client(cls) -> int:
        """Get disable_subscription_for_client"""
        key = GeneralSettingChoices.DISABLE_SUBSCRIPTION_FOR_CLIENT.value

        # Try to get from cache first
        cached_value = cls._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, get from DB
        try:
            value = int(GeneralSetting.objects.get(key=key).value)
            # Cache the result for next time
            cls._set_in_cache(key, value)
            return value
        except:
            return 0

    @staticmethod
    def get_ai_chat_price_by_type(chat_type: str) -> int:
        """Get AI chat price based on chat type"""
        if chat_type == "v":
            return GeneralSettingsQuery.get_ai_chat_price_v()
        elif chat_type == "v_plus":
            return GeneralSettingsQuery.get_ai_chat_price_v_plus()
        elif chat_type == "v_x":
            return GeneralSettingsQuery.get_ai_chat_price_v_x()
        elif chat_type == "v_pro":
            return GeneralSettingsQuery.get_ai_chat_price_v_pro()
        elif chat_type == "v_plus_pro":
            return GeneralSettingsQuery.get_ai_chat_price_v_plus_pro()
        elif chat_type == "v_manual_request":
            return GeneralSettingsQuery.get_ai_chat_price_v_manual_request()
        elif chat_type == "v_x_pro":
            return GeneralSettingsQuery.get_ai_chat_price_v_x_pro()
        elif chat_type == "v_made_477":
            return GeneralSettingsQuery.get_ai_chat_price_v_made_477()
        elif chat_type == "v_prepare_initial_petition":
            return GeneralSettingsQuery.get_ai_chat_price_v_prepare_initial_petition()
        elif chat_type == "v_prepare_appeal_petition":
            return GeneralSettingsQuery.get_ai_chat_price_v_prepare_appeal_petition()
        elif chat_type == "v_prepare_defense_brief":
            return GeneralSettingsQuery.get_ai_chat_price_v_prepare_defense_brief()
        elif chat_type == "v_prepare_custom_request":
            return GeneralSettingsQuery.get_ai_chat_price_v_prepare_custom_request()
        else:
            return GeneralSettingsQuery.DEFAULT_AI_CHAT_PRICE_V  # Default to V price
