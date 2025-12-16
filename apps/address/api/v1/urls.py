from rest_framework.routers import DefaultRouter

from .views import AddressListModelViewSet

app_name = "address"

router = DefaultRouter()
router.register("", AddressListModelViewSet, basename="user-address-api")

urlpatterns = []

urlpatterns += router.urls
