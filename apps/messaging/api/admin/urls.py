from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AdminSMSBalanceViewSet,
    AdminSMSTemplateViewSet,
    AdminSMSPurchaseViewSet,
    AdminSMSMessageViewSet,
    AdminSystemSMSTemplateViewSet,
    AdminSMSDashboardViewSet,
)

app_name = "messaging"

router = DefaultRouter()
router.register("balances", AdminSMSBalanceViewSet, basename="admin-sms-balances")
router.register("templates", AdminSMSTemplateViewSet, basename="admin-sms-templates")
router.register("purchases", AdminSMSPurchaseViewSet, basename="admin-sms-purchases")
router.register("messages", AdminSMSMessageViewSet, basename="admin-sms-messages")
router.register("system-templates", AdminSystemSMSTemplateViewSet, basename="admin-system-templates")
router.register("dashboard", AdminSMSDashboardViewSet, basename="admin-sms-dashboard")

urlpatterns = []

urlpatterns += router.urls
