from rest_framework.routers import DefaultRouter

from apps.social_media.api.admin.views import SocialMediaTypeAdminViewSet

app_name = "social_media"

router = DefaultRouter()
router.register("", SocialMediaTypeAdminViewSet, basename="social_media_admin")

urlpatterns = []

urlpatterns += router.urls
