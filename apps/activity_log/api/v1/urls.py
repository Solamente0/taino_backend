from rest_framework.routers import DefaultRouter
from .views import ActivityLogViewSet

app_name = "activity_log"

router = DefaultRouter()
router.register("", ActivityLogViewSet, basename="activity-log")

urlpatterns = []
urlpatterns += router.urls
