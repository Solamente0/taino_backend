import base64
import logging
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter

from base_utils.permissions import HasTainoMobileUserPermission
from base_utils.views.mobile import TainoMobileGenericViewSet

from apps.ai_chat.api.v1.serializers import OCRAnalysisRequestSerializer, OCRResultSerializer


logger = logging.getLogger(__name__)


class OCRAnalysisViewSet(TainoMobileGenericViewSet):
    """ViewSet for OCR document analysis"""

    permission_classes = [IsAuthenticated, HasTainoMobileUserPermission]

    section_mapping = {
        "initial_petition": "Initial_Petition",
        "pleadings": "Pleadings_of_the_Parties",
        "first_instance_judgment": "First_Instance_Judgment",
        "appeal": "Appeal",
    }

    @extend_schema(request=OCRAnalysisRequestSerializer, responses={202: OCRResultSerializer})
    @action(detail=False, methods=["POST"], url_path="analyze")
    def analyze(self, request):
        """Process legal documents with OCR and analyze with AI"""
        serializer = OCRAnalysisRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_pid = str(request.user.pid)

        from apps.ai_chat.services.ocr_service import OCRService

        OCRService.clear_cache(user_pid)

        processing_tasks = []

        for section_key, redis_key in self.section_mapping.items():
            section_data = serializer.validated_data.get(section_key)

            if not section_data:
                continue

            for file_data in section_data.get("files", []):
                file = file_data["file"]
                file_title = file_data["title"]

                file_content = base64.b64encode(file.read()).decode("utf-8")

                from apps.ai_chat.tasks import process_ocr_file

                task = process_ocr_file.delay(
                    user_pid=user_pid,
                    section_key=redis_key,
                    file_id=f"file_{len(processing_tasks) + 1}",
                    file_title=file_title,
                    file_type=getattr(file, "content_type", "application/octet-stream"),
                    file_content_b64=file_content,
                )

                processing_tasks.append(task.id)

        if not processing_tasks:
            return Response(
                {"error": _("No valid files provided for OCR analysis")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.ai_chat.tasks import analyze_ocr_data_with_ai

        analyze_task = analyze_ocr_data_with_ai.delay(user_pid=user_pid, ai_session_id=str(request.data.get("ai_session_id")))

        return Response(
            {
                "status": "processing",
                "task_id": analyze_task.id,
                "message": _("Documents uploaded for analysis. Processing will begin shortly."),
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        parameters=[OpenApiParameter(name="task_id", type=str, required=True)], responses={200: OCRResultSerializer}
    )
    @action(detail=False, methods=["GET"], url_path="status")
    def status(self, request):
        """Check the status of an OCR analysis task"""
        task_id = request.query_params.get("task_id")

        if not task_id:
            return Response({"error": _("Task ID is required")}, status=status.HTTP_400_BAD_REQUEST)

        from celery.result import AsyncResult

        result = AsyncResult(task_id)

        if result.state == "SUCCESS":
            result_data = result.get()

            return Response(
                {
                    "status": "completed",
                    "analysis": result_data.get("analysis", ""),
                    "error": result_data.get("message") if result_data.get("status") == "error" else None,
                }
            )
        elif result.state == "FAILURE":
            return Response({"status": "failed", "error": str(result.result)})
        else:
            return Response({"status": "processing"})
