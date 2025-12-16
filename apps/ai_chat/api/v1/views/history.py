# apps/ai_chat/api/v1/views/history.py

import logging
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.utils.translation import gettext_lazy as _

from apps.analyzer.models import AnalyzerLog
from apps.contract.models import ContractLog
from apps.file_to_text.models import FileToTextLog
from apps.ai_chat.models import ChatAIConfig
from apps.ai_chat.api.v1.serializers import AIHistoryItemSerializer, AIHistoryUpdateSerializer
from base_utils.permissions import HasTainoMobileUserPermission
from base_utils.views.mobile import TainoMobileGenericViewSet

logger = logging.getLogger(__name__)


class AIHistoryViewSet(TainoMobileGenericViewSet):
    """ViewSet for AI history from all sources"""

    permission_classes = [IsAuthenticated, HasTainoMobileUserPermission]
    serializer_class = AIHistoryItemSerializer

    def _get_ai_type_details(self, ai_type: str):
        """Get AI type details from ChatAIConfig"""
        try:
            config = ChatAIConfig.objects.filter(static_name=ai_type, is_active=True).first()
            if config:
                return {
                    "name": config.name,
                    "description": config.description,
                    "ai_type_name": config.name,
                    "ai_type": ai_type,
                }
        except Exception as e:
            logger.error(f"Error getting AI type details: {e}")

        return {
            "name": ai_type,
            "description": "",
            "ai_type_name": ai_type,
            "ai_type": ai_type,
        }

    def _ctainoert_to_history_item(self, item, model_type):
        """Ctainoert model instances to unified history item format"""

        ai_type = getattr(item, "ai_type", "unknown")
        ai_type_details = self._get_ai_type_details(ai_type)

        base_data = {
            "pid": str(item.pid),
            "user": item.user,
            "ai_session_id": str(item.ai_session.pid) if hasattr(item, "ai_session") and item.ai_session else None,
            "ai_type": ai_type,
            "created_at": item.created_at,
            "ai_type_details": ai_type_details,
        }

        if model_type == "analyzer":
            base_data.update(
                {
                    "analysis_type": "document_analysis",
                    "analysis_text": item.analysis_text or "",
                    "extracted_text": "",
                    "prompt": item.prompt or "",
                    "user_request_analysis_text": "",
                    "user_request_choice": "",
                    "user_request_choice_display": "",
                }
            )
        elif model_type == "contract":
            base_data.update(
                {
                    "analysis_type": "contract",
                    "analysis_text": item.contract_text or "",
                    "extracted_text": "",
                    "prompt": item.prompt or "",
                    "user_request_analysis_text": "",
                    "user_request_choice": "",
                    "user_request_choice_display": "",
                }
            )
        elif model_type == "file_to_text":
            base_data.update(
                {
                    "analysis_type": "file_to_text",
                    "analysis_text": item.extracted_text or "",
                    "extracted_text": item.extracted_text or "",
                    "prompt": item.original_filename or "",
                    "user_request_analysis_text": "",
                    "user_request_choice": "",
                    "user_request_choice_display": "",
                }
            )

        return base_data

    def _get_all_history_items(self, user, ai_type=None):
        """Get all history items from different sources"""
        items = []

        # Get from AnalyzerLog
        analyzer_query = AnalyzerLog.objects.filter(user=user)
        if ai_type:
            analyzer_query = analyzer_query.filter(ai_type=ai_type)

        for item in analyzer_query:
            items.append(
                {
                    "item": item,
                    "type": "analyzer",
                    "created_at": item.created_at,
                }
            )

        # Get from ContractLog
        contract_query = ContractLog.objects.filter(user=user)
        if ai_type:
            contract_query = contract_query.filter(ai_type=ai_type)

        for item in contract_query:
            items.append(
                {
                    "item": item,
                    "type": "contract",
                    "created_at": item.created_at,
                }
            )

        # Get from FileToTextLog
        file_to_text_query = FileToTextLog.objects.filter(user=user)
        if ai_type:
            file_to_text_query = file_to_text_query.filter(ai_type=ai_type)

        for item in file_to_text_query:
            items.append(
                {
                    "item": item,
                    "type": "file_to_text",
                    "created_at": item.created_at,
                }
            )

        # Sort by created_at descending
        items.sort(key=lambda x: x["created_at"], reverse=True)

        return items

    @extend_schema(
        parameters=[
            OpenApiParameter(name="ai_type", type=str, required=False),
            OpenApiParameter(name="analysis_type", type=str, required=False),
        ],
        responses={200: AIHistoryItemSerializer(many=True)},
    )
    def list(self, request):
        """Get all AI history items"""
        try:
            user = request.user
            ai_type = request.query_params.get("ai_type")
            analysis_type = request.query_params.get("analysis_type")

            items = self._get_all_history_items(user, ai_type)

            # Filter by analysis_type if provided
            if analysis_type:
                items = [item for item in items if item["type"] == analysis_type]

            # Ctainoert to serializable format
            serialized_items = []
            for item_data in items:
                ctainoerted = self._ctainoert_to_history_item(item_data["item"], item_data["type"])
                serialized_items.append(ctainoerted)

            serializer = AIHistoryItemSerializer(serialized_items, many=True)

            return Response(
                {
                    "count": len(serialized_items),
                    "results": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error fetching history: {e}", exc_info=True)
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(request=AIHistoryUpdateSerializer, responses={200: AIHistoryItemSerializer})
    @action(detail=True, methods=["PATCH"], url_path="update")
    def update_history_item(self, request, pid=None):
        """Update an AI history item"""
        try:
            user = request.user

            # Try to find in different models
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
                elif "analysis_text" in serializer.validated_data:
                    item.contract_text = serializer.validated_data["analysis_text"]
            elif model_type == "file_to_text":
                if "extracted_text" in serializer.validated_data:
                    item.extracted_text = serializer.validated_data["extracted_text"]
                elif "analysis_text" in serializer.validated_data:
                    item.extracted_text = serializer.validated_data["analysis_text"]

            item.save()

            # Return updated item
            ctainoerted = self._ctainoert_to_history_item(item, model_type)
            return Response(AIHistoryItemSerializer(ctainoerted).data, status=status.HTTP_200_OK)

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
