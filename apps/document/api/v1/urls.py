from rest_framework.routers import DefaultRouter

from .views import DocumentViewSet

app_name = "document"

router = DefaultRouter()
router.register("", DocumentViewSet, basename="documents")

urlpatterns = []

urlpatterns += router.urls
