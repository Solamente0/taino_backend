from rest_framework.routers import DefaultRouter

from . import views as version_apis

app_name = "version"

router = DefaultRouter()

router.register(
    "",
    version_apis.AppVersionsGenericViewSetAPI,
    basename="version-info-api",
)

urlpatterns = []

urlpatterns += router.urls
