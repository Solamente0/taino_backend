from rest_framework.routers import DefaultRouter
from apps.payment.api.admin.views import AdminCouponViewSet, AdminZarinpalConfigViewSet

app_name = "payment"

router = DefaultRouter()
router.register("coupons", AdminCouponViewSet, basename="coupons")
router.register("zarinpal-config", AdminZarinpalConfigViewSet, basename="zarinpal-config")

urlpatterns = []

urlpatterns += router.urls
