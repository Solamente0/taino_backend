from rest_framework.routers import DefaultRouter

from .views import CountryViewSet, CityViewSet, StateViewSet

app_name = "country"

router = DefaultRouter()
router.register("city", CityViewSet, basename="city")
router.register("state", StateViewSet, basename="state")
router.register("", CountryViewSet, basename="country")

urlpatterns = []

urlpatterns += router.urls
