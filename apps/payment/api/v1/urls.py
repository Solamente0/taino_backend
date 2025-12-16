from rest_framework.routers import DefaultRouter
from django.urls import path

from .views import PaymentViewSet, VerifyPaymentAPIView, CouponViewSet

app_name = "payment"

router = DefaultRouter()
router.register("", PaymentViewSet, basename="payment")
router.register("coupons", CouponViewSet, basename="coupons")

urlpatterns = [
    path("verify/", VerifyPaymentAPIView.as_view(), name="verify"),
]

urlpatterns += router.urls
