from rest_framework.routers import DefaultRouter

from apps.setting.api.admin.views import GeneralSettingAdminViewSet

app_name = "settings"

router = DefaultRouter()
router.register("general", GeneralSettingAdminViewSet, basename="general")

urlpatterns = []

urlpatterns += router.urls
