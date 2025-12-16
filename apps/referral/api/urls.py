from django.urls import include, path

app_name = "referral"

urlpatterns = [
    path("v1/", include("apps.referral.api.v1.urls", namespace="referral_v1"), name="referral_v1"),
]
