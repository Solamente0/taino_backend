from rest_framework.routers import DefaultRouter

from apps.setting.api.v1.views import GeneralSettingMobileViewSet

app_name = "settings"

router = DefaultRouter()
router.register("general", GeneralSettingMobileViewSet, basename="general")

urlpatterns = []

urlpatterns += router.urls
