from django.http import FileResponse
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.document.services.download_file import get_document_download_file
from base_utils.views.public import TainoPublicGenericViewSet


class DocumentPublicViewSet(TainoPublicGenericViewSet):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser]

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Binary Response"),
        },
        parameters=[
            OpenApiParameter(
                name="download",
                type=int,
                description="Set to 1 for force download, 0 for inline viewing",
                required=False,
                default=1,
            )
        ],
    )
    @action(methods=["GET"], detail=True, url_path="download")
    def download(self, request, pid, **kwargs):
        try:
            # Get the download parameter (default to 1 if not provided)
            force_download = request.query_params.get("download", "1") == "1"

            file, mime_type = get_document_download_file(pid)

            # Set content type based on force_download parameter
            content_type = "force-download" if force_download else ""

            response = FileResponse(file, content_type=content_type, as_attachment=force_download)
            file_name = file.name.split("/")[-1]

            if force_download:
                response["Content-Disposition"] = f'attachment; filename="{file_name}"'
            else:
                response["Content-Disposition"] = f'inline; filename="{file_name}"'
                response["Content-Type"] = mime_type
            return response
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)
