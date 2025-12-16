from django.urls import include, path

app_name = "crm_hub"

urlpatterns = [
    path("v1/", include("apps.crm_hub.api.v1.urls", namespace="crm_hub_v1"), name="crm_hub_v1"),
    path("admin/", include("apps.crm_hub.api.admin.urls", namespace="crm_hub_admin"), name="crm_hub_admin"),
]
