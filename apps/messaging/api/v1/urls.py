from rest_framework.routers import DefaultRouter

from .views import (
    SMSBalanceViewSet,
    SMSTemplateViewSet,
    SMSPurchaseViewSet,
    SMSMessageViewSet,
    SystemSMSTemplateViewSet,
    SMSPackageViewSet,
)

app_name = "messaging"

router = DefaultRouter()
router.register("balance", SMSBalanceViewSet, basename="sms-balance")
router.register("templates", SMSTemplateViewSet, basename="sms-templates")
router.register("purchases", SMSPurchaseViewSet, basename="sms-purchases")
router.register("messages", SMSMessageViewSet, basename="sms-messages")
router.register("system-templates", SystemSMSTemplateViewSet, basename="system-templates")
router.register("packages", SMSPackageViewSet, basename="sms-packages")
urlpatterns = []

urlpatterns += router.urls
