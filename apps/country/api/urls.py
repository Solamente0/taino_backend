from django.urls import include, path

app_name = "country"

urlpatterns = [
    path("v1/", include("apps.country.api.v1.urls", namespace="country_v1"), name="country_v1"),
    path(
        "admin/",
        include("apps.country.api.admin.urls", namespace="country_admin"),
        name="country_admin",
    ),
]
