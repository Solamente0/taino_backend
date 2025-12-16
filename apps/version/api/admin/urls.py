from rest_framework import routers

from apps.version.api.admin import views as version_apis

app_name = "version"
router = routers.DefaultRouter()
router.register(r"", version_apis.VersionModelViewSetAPI, basename="admin-version-api")

urlpatterns = []
urlpatterns += router.urls
