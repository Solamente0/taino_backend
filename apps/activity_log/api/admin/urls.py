from rest_framework.routers import DefaultRouter
from .views import AdminActivityLogViewSet

app_name = "activity_log"

router = DefaultRouter()
router.register("", AdminActivityLogViewSet, basename="activity-log")

urlpatterns = []
urlpatterns += router.urls
