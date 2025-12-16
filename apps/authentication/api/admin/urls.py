from django.urls import path

from .views import (
    AdminTokenObtainPairView,
    AdminTokenRefreshView,
    # AdminLogoutView,
    logout,
)

app_name = "authentication"

urlpatterns = [
    path("login/", AdminTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", AdminTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", logout, name="logout"),
]
