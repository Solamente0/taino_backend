from rest_framework.routers import DefaultRouter

from . import views

app_name = "analyzer"

router = DefaultRouter()
# router.register("", AnalyzerAdminViewSet, basename="analyzer")

urlpatterns = []

urlpatterns += router.urls
