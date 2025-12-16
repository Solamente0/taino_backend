from rest_framework import routers

from apps.user.api.admin.views import AdminUserViewSet

app_name = "user"

router = routers.DefaultRouter()


router.register(
    "",
    AdminUserViewSet,
    basename="admin_users",
)


urlpatterns = []
urlpatterns += router.urls
