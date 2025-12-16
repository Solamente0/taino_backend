from django.urls import include, path

app_name = "landing"

urlpatterns = [
    path("v1/", include("apps.landing.api.v1.urls", namespace="landing_v1"), name="landing_v1"),
    path("admin/", include("apps.landing.api.admin.urls", namespace="landing_admin"), name="landing_admin"),
]
