# apps/file_to_text/api/urls.py
from django.urls import include, path

app_name = "file_to_text"

urlpatterns = [
    path("v1/", include("apps.file_to_text.api.v1.urls", namespace="file_to_text_v1")),
]
