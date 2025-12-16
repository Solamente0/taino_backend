from rest_framework.routers import DefaultRouter

from .views import DocumentAdminViewSet

app_name = "document"

router = DefaultRouter()
router.register("", DocumentAdminViewSet, basename="documents")

urlpatterns = []

urlpatterns += router.urls
