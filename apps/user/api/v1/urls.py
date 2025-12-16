from django.urls import path
from rest_framework import routers

from .views import UserProfileModelViewSetAPI, DeleteAccountAPIView, UserRolesViewSet, UserProfileViewSet, UserDeviceViewSet

app_name = "user"

router = routers.DefaultRouter()
router.register("", UserProfileModelViewSetAPI, basename="user_profile")
router.register("roles", UserRolesViewSet, basename="user_roles")
router.register("profile", UserProfileViewSet, basename="user_detailed_profile")
router.register("devices", UserDeviceViewSet, basename="user-devices")
urlpatterns = [
    path("delete-account/", DeleteAccountAPIView.as_view(), name="user_delete_account"),
    # Addresses are now handled through user_profile viewset actions
]

urlpatterns += router.urls
