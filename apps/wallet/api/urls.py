from django.urls import include, path

app_name = "wallet"

urlpatterns = [
    path("v1/", include("apps.wallet.api.v1.urls", namespace="wallet_v1"), name="wallet_v1"),
    path(
        "admin/",
        include("apps.wallet.api.admin.urls", namespace="wallet_admin"),
        name="wallet_admin",
    ),
]
