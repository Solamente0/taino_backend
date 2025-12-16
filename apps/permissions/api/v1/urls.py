from rest_framework.routers import DefaultRouter

from apps.permissions.api.v1.views import PermissionCategoryViewSet, PermissionViewSet

app_name = "permissions"

router = DefaultRouter()
router.register("categories", PermissionCategoryViewSet, basename="permission_categories")
router.register("", PermissionViewSet, basename="permissions")

urlpatterns = []

urlpatterns += router.urls
