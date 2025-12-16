from django.urls import path, include

app_name = "address"

urlpatterns = [
    path("v1/", include("apps.address.api.v1.urls", namespace="address_v1"), name="address_v1"),
]
