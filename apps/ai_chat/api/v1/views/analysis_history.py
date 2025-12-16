# apps/ai_chat/api/v1/views.py
import logging

from django.utils.translation import gettext_lazy as _
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer

from apps.ai_chat.api.v1.serializers.analysis_history import AIHistoryItemSerializer
from apps.ai_chat.models import LegalAnalysisLog
from apps.contract.models import ContractLog
from apps.file_to_text.models import FileToTextLog
from base_utils.permissions import HasTainoMobileUserPermission
from base_utils.views.mobile import TainoMobileGenericViewSet, TainoMobileListModelMixin

from apps.ai_chat.api.v1.serializers import CombinedAnalysisHistorySerializer, AIUserSerializer, AIHistoryUpdateSerializer


from itertools import chain
from operator import attrgetter
from apps.analyzer.models import AnalyzerLog

logger = logging.getLogger(__name__)


class AnalysisHistoryViewSet(TainoMobileListModelMixin, TainoMobileGenericViewSet):
    """ViewSet for combined analysis history (Legal + Document Analysis)"""

    permission_classes = [IsAuthenticated, HasTainoMobileUserPermission]
    serializer_class = CombinedAnalysisHistorySerializer

    def get_queryset(self):
        """Combine both legal and document analysis logs"""
        user = self.request.user
        ai_type = self.request.query_params.get("ai_type")
        analysis_type = self.request.query_params.get("analysis_type")

        # Get legal analysis logs
        legal_logs = LegalAnalysisLog.objects.filter(user=user, is_deleted=False)

        # Get document analysis logs
        analyzer_logs = AnalyzerLog.objects.filter(user=user, is_deleted=False)
        file_to_text_logs = FileToTextLog.objects.filter(user=user, is_deleted=False)

        # Filter by ai_type if provided
        if ai_type:
            legal_logs = legal_logs.filter(ai_type=ai_type)
            analyzer_logs = analyzer_logs.filter(ai_type=ai_type)
            file_to_text_logs = file_to_text_logs.filter(ai_type=ai_type)

        # Filter by analysis_type if provided
        if analysis_type == "legal_analysis":
            return legal_logs.order_by("-created_at")
        elif analysis_type == "document_analysis":
            return analyzer_logs.order_by("-created_at")
        elif analysis_type == "file_to_text":
            return file_to_text_logs.order_by("-created_at")

        # Combine both querysets and sort by created_at
        combined = list(chain(legal_logs, analyzer_logs, file_to_text_logs))
        combined.sort(key=attrgetter("created_at"), reverse=True)

        return combined

    def list(self, request, *args, **kwargs):
        """Override list to handle combined queryset pagination"""
        queryset = self.get_queryset()

        # If queryset is a list (combined), handle pagination manually
        if isinstance(queryset, list):
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        # If queryset is a QuerySet (filtered), use default behavior
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="ai_type", type=str, required=False, description="Filter by AI type (v, v_plus, v_x)"),
            OpenApiParameter(
                name="analysis_type",
                type=str,
                required=False,
                description="Filter by analysis type (legal_analysis, document_analysis)",
            ),
        ],
        responses={
            200: inline_serializer(
                name="AnalysisHistoryResponse",
                fields={
                    "pid": serializers.CharField(),
                    "user": AIUserSerializer(),
                    "ai_session_id": serializers.CharField(),
                    "ai_type": serializers.CharField(),
                    "ai_type_details": serializers.DictField(),  # Add this
                    "analysis_type": serializers.CharField(),
                    "created_at": serializers.DateTimeField(),
                    "analysis_text": serializers.CharField(),
                    "user_request_analysis_text": serializers.CharField(),
                    "user_request_choice": serializers.CharField(),
                    "user_request_choice_display": serializers.CharField(),
                    "prompt": serializers.CharField(),
                },
            )
        },
    )
    @action(detail=False, methods=["GET"], url_path="all")
    def all_history(self, request):
        """Get all analysis history for the user"""
        return self.list(request)

    @extend_schema(responses={200: CombinedAnalysisHistorySerializer})
    @action(detail=False, methods=["GET"], url_path="latest")
    def latest_analysis(self, request):
        """Get the latest analysis (either legal or document)"""
        user = request.user
        ai_type = request.query_params.get("ai_type")
        analysis_type = request.query_params.get("analysis_type")

        try:
            # Get latest from both types
            legal_log_query = LegalAnalysisLog.objects.filter(user=user, is_deleted=False)
            analyzer_log_query = AnalyzerLog.objects.filter(user=user, is_deleted=False)
            file_to_text_query = FileToTextLog.objects.filter(user=user, is_deleted=False)

            if ai_type:
                legal_log_query = legal_log_query.filter(ai_type=ai_type)
                analyzer_log_query = analyzer_log_query.filter(ai_type=ai_type)
                file_to_text_query = file_to_text_query.filter(ai_type=ai_type)

            if analysis_type == "legal_analysis":
                latest = legal_log_query.order_by("-created_at").first()
            elif analysis_type == "document_analysis":
                latest = analyzer_log_query.order_by("-created_at").first()
            elif analysis_type == "file_to_text":
                latest = file_to_text_query.order_by("-created_at").first()
            else:
                # Get the most recent from both
                latest_legal = legal_log_query.order_by("-created_at").first()
                latest_analyzer = analyzer_log_query.order_by("-created_at").first()
                latest_file_to_text = file_to_text_query.order_by("-created_at").first()

                if not latest_legal and not latest_analyzer and not latest_file_to_text:
                    return Response(
                        {"status": "not_found", "message": _("No analysis history found")}, status=status.HTTP_404_NOT_FOUND
                    )
                elif not latest_legal:
                    latest = latest_analyzer
                elif not latest_analyzer:
                    latest = latest_legal
                elif not latest_legal and latest_analyzer:
                    latest = latest_file_to_text
                else:
                    latest = latest_legal if latest_legal.created_at > latest_analyzer.created_at else latest_analyzer

            if latest:
                serializer = self.get_serializer(latest)
                return Response({"status": "success", "data": serializer.data})

            return Response(
                {"status": "not_found", "message": _("No analysis history found")}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            logger.error(f"Error fetching latest analysis: {e}", exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        parameters=[OpenApiParameter(name="ai_type", type=str, required=False)],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "legal_analysis_count": {"type": "integer"},
                    "document_analysis_count": {"type": "integer"},
                    "total_count": {"type": "integer"},
                },
            }
        },
    )
    @action(detail=False, methods=["GET"], url_path="stats")
    def stats(self, request):
        """Get statistics about analysis history"""
        user = request.user
        ai_type = request.query_params.get("ai_type")

        legal_query = LegalAnalysisLog.objects.filter(user=user, is_deleted=False)
        analyzer_query = AnalyzerLog.objects.filter(user=user, is_deleted=False)
        file_to_text_query = FileToTextLog.objects.filter(user=user, is_deleted=False)

        if ai_type:
            legal_query = legal_query.filter(ai_type=ai_type)
            analyzer_query = analyzer_query.filter(ai_type=ai_type)
            file_to_text_query = file_to_text_query.filter(ai_type=ai_type)

        legal_count = legal_query.count()
        analyzer_count = analyzer_query.count()
        file_to_text_count = file_to_text_query.count()

        return Response(
            {
                "legal_analysis_count": legal_count,
                "document_analysis_count": analyzer_count,
                "file_to_text_count": file_to_text_count,
                "total_count": legal_count + analyzer_count + file_to_text_count,
            }
        )

    @extend_schema(request=AIHistoryUpdateSerializer, responses={200: AIHistoryItemSerializer})
    @action(detail=True, methods=["PATCH"], url_path="update")
    def update_history_item(self, request, pid=None):
        """Update an AI history item"""
        try:
            user = request.user

            # Try to find in different models based on analysis_type
            item = None
            model_type = None

            # Try AnalyzerLog
            try:
                item = AnalyzerLog.objects.get(pid=pid, user=user)
                model_type = "analyzer"
            except AnalyzerLog.DoesNotExist:
                pass

            # Try ContractLog
            if not item:
                try:
                    item = ContractLog.objects.get(pid=pid, user=user)
                    model_type = "contract"
                except ContractLog.DoesNotExist:
                    pass

            # Try FileToTextLog
            if not item:
                try:
                    item = FileToTextLog.objects.get(pid=pid, user=user)
                    model_type = "file_to_text"
                except FileToTextLog.DoesNotExist:
                    pass

            if not item:
                return Response({"detail": _("آیتم یافت نشد")}, status=status.HTTP_404_NOT_FOUND)

            serializer = AIHistoryUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Update based on model type
            if model_type == "analyzer":
                if "analysis_text" in serializer.validated_data:
                    item.analysis_text = serializer.validated_data["analysis_text"]
            elif model_type == "contract":
                if "contract_text" in serializer.validated_data:
                    item.contract_text = serializer.validated_data["contract_text"]
            elif model_type == "file_to_text":
                if "extracted_text" in serializer.validated_data:
                    item.extracted_text = serializer.validated_data["extracted_text"]

            item.save()

            # Return updated item
            return Response(
                AIHistoryItemSerializer(self._ctainoert_to_history_item(item, model_type)).data, status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error updating history item: {e}", exc_info=True)
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(responses={204: None})
    @action(detail=True, methods=["DELETE"], url_path="delete")
    def delete_history_item(self, request, pid=None):
        """Delete an AI history item"""
        try:
            user = request.user

            # Try to find and delete in different models
            deleted = False

            # Try AnalyzerLog
            try:
                item = AnalyzerLog.objects.get(pid=pid, user=user)
                item.delete()
                deleted = True
            except AnalyzerLog.DoesNotExist:
                pass

            # Try ContractLog
            if not deleted:
                try:
                    item = ContractLog.objects.get(pid=pid, user=user)
                    item.delete()
                    deleted = True
                except ContractLog.DoesNotExist:
                    pass

            # Try FileToTextLog
            if not deleted:
                try:
                    item = FileToTextLog.objects.get(pid=pid, user=user)
                    item.delete()
                    deleted = True
                except FileToTextLog.DoesNotExist:
                    pass

            if not deleted:
                return Response({"detail": _("آیتم یافت نشد")}, status=status.HTTP_404_NOT_FOUND)

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f"Error deleting history item: {e}", exc_info=True)
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _ctainoert_to_history_item(self, item, model_type):
        """Helper to ctainoert model instances to uniform format"""

        base_data = {
            "pid": str(item.pid),
            "user": item.user,
            "ai_session_id": str(item.ai_session.pid) if hasattr(item, "ai_session") and item.ai_session else None,
            "ai_type": getattr(item, "ai_type", "unknown"),
            "created_at": item.created_at,
        }

        if model_type == "analyzer":
            base_data.update(
                {
                    "analysis_type": "document_analysis",
                    "analysis_text": item.analysis_text,
                    "extracted_text": getattr(item, "extracted_text", ""),
                    "prompt": item.prompt,
                }
            )
        elif model_type == "contract":
            base_data.update(
                {
                    "analysis_type": "contract",
                    "analysis_text": item.contract_text,
                    "prompt": item.prompt,
                }
            )
        elif model_type == "file_to_text":
            base_data.update(
                {
                    "analysis_type": "file_to_text",
                    "analysis_text": item.extracted_text,
                    "extracted_text": item.extracted_text,
                    "prompt": item.original_filename,
                }
            )

        return type("HistoryItem", (), base_data)
