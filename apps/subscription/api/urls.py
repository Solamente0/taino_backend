from django.urls import include, path

app_name = "subscription"

urlpatterns = [
    path("v1/", include("apps.subscription.api.v1.urls", namespace="subscription_v1"), name="subscription_v1"),
    path(
        "admin/",
        include("apps.subscription.api.admin.urls", namespace="subscription_admin"),
        name="subscription_admin",
    ),
]
