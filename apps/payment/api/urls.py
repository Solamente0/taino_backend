from django.urls import include, path

app_name = "payment"

urlpatterns = [
    path("v1/", include("apps.payment.api.v1.urls", namespace="payment_v1"), name="payment_v1"),
    path(
        "admin/",
        include("apps.payment.api.admin.urls", namespace="payment_admin"),
        name="payment_admin",
    ),
]
