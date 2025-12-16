from rest_framework.routers import DefaultRouter

from apps.referral.api.v1.views import ReferralLinkViewSet

app_name = "referral"

router = DefaultRouter()

urlpatterns = []

urlpatterns += router.urls
