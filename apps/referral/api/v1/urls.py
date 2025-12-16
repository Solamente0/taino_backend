from rest_framework.routers import DefaultRouter

from apps.referral.api.v1.views import ReferralLinkViewSet

app_name = "referral"

router = DefaultRouter()
router.register("link", ReferralLinkViewSet, basename="link")

urlpatterns = []

urlpatterns += router.urls
