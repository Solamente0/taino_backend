from django.urls import include, path

app_name = "document"

urlpatterns = [
    path("v1/", include("apps.document.api.v1.urls", namespace="document_v1"), name="document_v1"),
    path("admin/", include("apps.document.api.admin.urls", namespace="document_admin"), name="document_admin"),
    path("public/", include("apps.document.api.public.urls", namespace="document_public"), name="document_public"),
]
