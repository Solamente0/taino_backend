from rest_framework.routers import DefaultRouter

from .views import BannerAdminViewSet

app_name = "banner"

router = DefaultRouter()
router.register("", BannerAdminViewSet, basename="banner")

urlpatterns = []

urlpatterns += router.urls
