from django.urls import path, include

app_name = "social_media"

urlpatterns = [
    path("v1/", include("apps.social_media.api.v1.urls", namespace="social_media_v1"), name="social_media_v1"),
    path("admin/", include("apps.social_media.api.admin.urls", namespace="social_media_admin"), name="social_media_admin"),
]
