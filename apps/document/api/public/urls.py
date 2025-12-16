from rest_framework.routers import DefaultRouter

from .views import DocumentPublicViewSet

app_name = "document"

router = DefaultRouter()
router.register("", DocumentPublicViewSet, basename="documents")

urlpatterns = []

urlpatterns += router.urls
