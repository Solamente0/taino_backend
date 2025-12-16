from apps.document.api.admin.serializers import (
    AdminImageUploadSerializer,
    AdminVideoUploadSerializer,
    AdminDocumentUploadSerializer,
)
from base_utils.views.admin import TainoAdminGenericViewSet

# apps/document/api/v1/views.py
from django.http import FileResponse
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.utils import inline_serializer
from rest_framework import status, serializers
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.document.api.v1.serializers import ImageUploadSerializer, VideoUploadSerializer, DocumentUploadSerializer
from apps.document.services.download_file import get_document_download_file
from base_utils.views.mobile import TainoMobileGenericViewSet


class DocumentAdminViewSet(TainoAdminGenericViewSet):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser]

    @extend_schema(
        request=AdminImageUploadSerializer,
        responses={
            201: inline_serializer(
                name="DocumentUploadResponseSerializer",
                fields={
                    "pid": serializers.ListField(child=serializers.CharField()),
                },
            )
        },
    )
    @action(methods=["POST"], detail=False, url_path="upload-image", permission_classes=[IsAuthenticated])
    def upload_image(self, request, **kwargs):
        ser = AdminImageUploadSerializer(data=request.data, context=self.get_serializer_context())
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(data=ser.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=AdminVideoUploadSerializer,
        responses={
            201: inline_serializer(
                name="DocumentUploadResponseSerializer",
                fields={
                    "pid": serializers.CharField(),
                },
            )
        },
    )
    @action(methods=["POST"], detail=False, url_path="upload-video", permission_classes=[IsAuthenticated])
    def upload_video(self, request, **kwargs):
        ser = AdminVideoUploadSerializer(data=request.data, context=self.get_serializer_context())
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(data=ser.data, status=status.HTTP_201_CREATED)

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

    # Other existing actions...

    @extend_schema(
        request=AdminDocumentUploadSerializer,
        responses={
            201: inline_serializer(
                name="DocumentUploadResponseSerializer",
                fields={
                    "pid": serializers.ListField(child=serializers.CharField()),
                },
            )
        },
    )
    @action(methods=["POST"], detail=False, url_path="upload-document", permission_classes=[IsAuthenticated])
    def upload_document(self, request, **kwargs):
        ser = AdminDocumentUploadSerializer(data=request.data, context=self.get_serializer_context())
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(data=ser.data, status=status.HTTP_201_CREATED)
