# apps/wallet/api/v1/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.subscription.api.v1.views import UserSubscriptionViewSet, PackageViewSet

app_name = "subscription"

router = DefaultRouter()
router.register("packages", PackageViewSet, basename="package")
router.register("subscriptions", UserSubscriptionViewSet, basename="subscription")

urlpatterns = []

urlpatterns += router.urls
