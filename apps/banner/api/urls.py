from django.urls import include, path

app_name = "banner"

urlpatterns = [
    path("v1/", include("apps.banner.api.v1.urls", namespace="banner_v1"), name="banner_v1"),
    path("admin/", include("apps.banner.api.admin.urls", namespace="banner_admin"), name="banner_admin"),
]
