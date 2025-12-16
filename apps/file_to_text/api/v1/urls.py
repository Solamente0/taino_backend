# apps/file_to_text/api/v1/urls.py
from rest_framework.routers import DefaultRouter
from apps.file_to_text.api.v1 import views

app_name = "file_to_text"

router = DefaultRouter()
router.register("", views.FileToTextViewSet, basename="file-to-text")

urlpatterns = []
urlpatterns += router.urls
