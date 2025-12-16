# apps/wallet/api/v1/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import WalletViewSet, CoinSettingsViewSet, CoinPackageViewSet

app_name = "wallet"

router = DefaultRouter()
router.register("", WalletViewSet, basename="wallet")
router.register("coin-settings", CoinSettingsViewSet, basename="coin-settings")
router.register("coin-packages", CoinPackageViewSet, basename="coin-packages")
urlpatterns = [
    # Add a direct path for the verification endpoint
    # This is necessary because the router pattern might not match what we need
    # for the callback from Zarinpal
    path("verify-deposit/", WalletViewSet.as_view({"get": "verify_deposit"}), name="verify_deposit"),
]

urlpatterns += router.urls
