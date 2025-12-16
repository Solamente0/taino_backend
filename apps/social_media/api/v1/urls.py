from rest_framework.routers import DefaultRouter

from .views import SocialMediaTypeViewSet

app_name = "social_media"

router = DefaultRouter()
router.register("", SocialMediaTypeViewSet, basename="social_media")

urlpatterns = []

urlpatterns += router.urls
