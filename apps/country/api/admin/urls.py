from rest_framework.routers import DefaultRouter

from apps.country.api.admin.views import CountryAdminViewSet, CityAdminViewSet, StateAdminViewSet

app_name = "country"

router = DefaultRouter()
router.register("city", CityAdminViewSet, basename="city")
router.register("state", StateAdminViewSet, basename="state")
router.register("", CountryAdminViewSet, basename="country")

urlpatterns = []

urlpatterns += router.urls
