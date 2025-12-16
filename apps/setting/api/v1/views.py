from base_utils.views.mobile import TainoMobileListModelMixin, TainoMobileGenericViewSet
from .serializers import GeneralSettingMobileSerializer
from ...services.query import GeneralSettingsQuery


class GeneralSettingMobileViewSet(TainoMobileListModelMixin, TainoMobileGenericViewSet):
    serializer_class = GeneralSettingMobileSerializer
    queryset = GeneralSettingsQuery().get_visible_mobile_settings()
