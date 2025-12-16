from django.urls import path
from rest_framework import routers

from . import views as auth_apis

app_name = "authentication"

router = routers.DefaultRouter()
router.register("", auth_apis.TainoAuthFlowViewSet, basename="authentication")

urlpatterns = [
    path("refresh/", auth_apis.TokenRefreshView.as_view(), name="token_refresh"),
    # path("login/google/", auth_apis.GoogleAuthView.as_view(), name="google_login"),
    path("logout/", auth_apis.logout, name="logout"),
]

urlpatterns += router.urls
