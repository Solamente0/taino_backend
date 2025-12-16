from django.urls import include, path

app_name = "case"

urlpatterns = [
    path("v1/", include("apps.case.api.v1.urls", namespace="case_v1"), name="case_v1"),
    path("admin/", include("apps.case.api.admin.urls", namespace="case_admin"), name="case_admin"),
]
