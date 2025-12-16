from rest_framework.routers import DefaultRouter
from apps.analyzer.api.v1 import views

app_name = "analyzer"

router = DefaultRouter()
router.register("manual-request", views.ManualRequestFileUploadViewSet, basename="manual-request")
router.register("analyzer", views.DocumentAnalyzerViewSet, basename="document-analyzer")

urlpatterns = []
urlpatterns += router.urls
