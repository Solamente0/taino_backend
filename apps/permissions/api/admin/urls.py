from rest_framework.routers import DefaultRouter

from apps.permissions.api.admin.views import (
    PermissionCategoryAdminViewSet,
    PermissionAdminViewSet,
    UserTypePermissionAdminViewSet,
    UserPermissionAdminViewSet,
)

app_name = "permissions"

router = DefaultRouter()
router.register("categories", PermissionCategoryAdminViewSet, basename="permission_categories")
router.register("permissions", PermissionAdminViewSet, basename="permissions")
router.register("user-type-permissions", UserTypePermissionAdminViewSet, basename="user_type_permissions")
router.register("user-permissions", UserPermissionAdminViewSet, basename="user_permissions")

urlpatterns = []

urlpatterns += router.urls
