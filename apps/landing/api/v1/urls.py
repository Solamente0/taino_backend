from rest_framework.routers import DefaultRouter

from .views import LandingPageViewSet, BlogViewSet

app_name = "landing"

router = DefaultRouter()
router.register("", LandingPageViewSet, basename="landing")
router.register("blog", BlogViewSet, basename="blog")

urlpatterns = []

urlpatterns += router.urls
