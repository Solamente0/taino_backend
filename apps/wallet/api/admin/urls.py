from rest_framework.routers import DefaultRouter
from apps.wallet.api.admin.views import (
    AdminWalletViewSet,
    AdminTransactionViewSet,
    AdminCoinSettingsViewSet,
    AdminCoinPackageViewSet,
)

app_name = "wallet"

router = DefaultRouter()
router.register("wallets", AdminWalletViewSet, basename="admin-wallets")
router.register("transactions", AdminTransactionViewSet, basename="admin-transactions")
router.register("coin-settings", AdminCoinSettingsViewSet, basename="admin-coin-settings")
router.register("coin-packages", AdminCoinPackageViewSet, basename="admin-coin-packages")
urlpatterns = []

urlpatterns += router.urls
