# apps/analyzer/api/v1/views/document_analyzer.py
import logging
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.utils.translation import gettext_lazy as _

from apps.analyzer.models import AnalyzerLog
from apps.analyzer.api.v1.serializers.analyzer import (
    DocumentAnalysisRequestSerializer,
    AnalyzerLogSerializer,
)
from apps.wallet.services.wallet import WalletService
from base_utils.permissions import HasTainoMobileUserPermission
from base_utils.views.mobile import TainoMobileGenericViewSet
from rest_framework.exceptions import ValidationError

from base_utils.voice_processor import VoiceProcessor

logger = logging.getLogger(__name__)


class DocumentAnalyzerViewSet(TainoMobileGenericViewSet):
    """ViewSet for document analysis using AI"""

    parser_classes = [*TainoMobileGenericViewSet.parser_classes, MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, HasTainoMobileUserPermission]

    @extend_schema(
        request=DocumentAnalysisRequestSerializer,
        responses={202: {"type": "object", "properties": {"status": {"type": "string"}, "task_id": {"type": "string"}}}},
    )
    @action(detail=False, methods=["POST"], url_path="analyze")
    def analyze(self, request):
        """Analyze documents using AI"""
        try:
            user = request.user
            serializer = DocumentAnalysisRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data

            prompt = validated_data.get("prompt", "")
            ai_type = validated_data.get("ai_type", "v_x")
            max_token_requested = validated_data.get("max_token_requested")
            files = request.FILES.getlist("files", [])

            # ✅ GET VOICE FILE AND CALCULATE DURATION ON BACKEND
            voice_file = request.FILES.get("voice_file")
            voice_duration_backend = 0  # Will be calculated
            voice_duration = None
            voice_duration_frontend = validated_data.get("voice_duration", 0)  # For comparison/fallback

            if voice_file:
                print(f"🎙️ Voice file received: {voice_file.name}, size: {voice_file.size}", flush=True)

                # ✅ CALCULATE DURATION ON BACKEND
                voice_duration_backend = VoiceProcessor.get_audio_duration(voice_file, voice_file.content_type)

                print(f"🎙️ Duration calculated:", flush=True)
                print(f"   Backend: {voice_duration_backend}s", flush=True)
                print(f"   Frontend: {voice_duration_frontend}s", flush=True)

                # ✅ USE BACKEND CALCULATION, FALLBACK TO FRONTEND IF BACKEND FAILS
                if voice_duration_backend > 0:
                    voice_duration = voice_duration_backend
                    print(f"   ✅ Using backend duration: {voice_duration}s", flush=True)
                else:
                    voice_duration = voice_duration_frontend
                    print(f"   ⚠️ Backend calculation failed, using frontend: {voice_duration}s", flush=True)

                # ✅ VALIDATE AGAINST CONFIG MAX
                from apps.ai_chat.services.ai_pricing_calculator import AIPricingCalculator

                ai_config = AIPricingCalculator.get_ai_config(ai_type)

                if ai_config and ai_config.max_minutes_per_request:
                    max_seconds = ai_config.max_minutes_per_request * 60
                    if voice_duration > max_seconds:
                        raise ValidationError(f"مدت زمان صدا ({voice_duration}s) بیش از حد مجاز ({max_seconds}s) است")

            # محاسبه هزینه کامل (متن + فایل + صدا)
            from apps.ai_chat.services.ai_pricing_calculator import AIPricingCalculator

            character_count = len(prompt)

            pricing_result = AIPricingCalculator.calculate_complete_cost(
                user=user,
                ai_config_static_name=ai_type,
                character_count=character_count,
                files=files,
                max_tokens_requested=max_token_requested,
                voice_duration_seconds=voice_duration if voice_file else None,  # ✅ USE VALIDATED DURATION
            )

            if not pricing_result.get("success"):
                raise ValidationError(pricing_result.get("error", "خطا در محاسبه قیمت"))

            # Check if it's free (bypass)
            if pricing_result.get("is_free"):
                print(f"Free document analysis for user {user.pid}: {pricing_result.get('bypass_reason')}", flush=True)
            else:
                # Check balance and charge
                total_cost = pricing_result.get("total_cost", 0)
                coin_balance = WalletService.get_wallet_coin_balance(user)

                description_parts = [f"تحلیل اسناد با {ai_type}"]
                if pricing_result["total_pages"] > 0:
                    description_parts.append(f"({pricing_result['total_pages']} صفحه)")
                if voice_duration:
                    description_parts.append(f"(صدا: {voice_duration}s)")
                description = " ".join(description_parts)

                if coin_balance < total_cost:
                    raise ValidationError(f"موجودی ناکافی: {total_cost} سکه نیاز است، {coin_balance} سکه موجود است")

                WalletService.use_coins(
                    user=user,
                    coin_amount=total_cost,
                    description=description,
                    reference_id=f"doc_analyzer_{ai_type}_{validated_data.get('ai_session_id', 'none')}",
                )

            # آماده‌سازی فایل‌ها و صدا برای task
            files_data = []
            if files:
                import base64

                for file in files:
                    file.seek(0)
                    files_data.append(
                        {
                            "name": file.name,
                            "content_type": file.content_type,
                            "content_b64": base64.b64encode(file.read()).decode("utf-8"),
                        }
                    )

            # ✅ Prepare voice data
            voice_data = None
            if voice_file:
                import base64

                voice_file.seek(0)
                voice_data = {
                    "filename": voice_file.name,
                    "content_type": voice_file.content_type,
                    "content_b64": base64.b64encode(voice_file.read()).decode("utf-8"),
                    "duration": voice_duration,  # ✅ BACKEND-VALIDATED DURATION
                }
                print(f"✅ Voice data prepared with backend duration: {voice_data['duration']}s", flush=True)

            # ارسال به task
            from apps.analyzer.tasks import document_analyzer_task

            task = document_analyzer_task.delay(
                user_pid=str(user.pid),
                prompt=prompt,
                files_data=files_data if files_data else None,
                voice_data=voice_data,  # ✅ ADD VOICE
                ai_session_id=validated_data.get("ai_session_id"),
                ai_type=ai_type,
            )

            return Response(
                {
                    "status": "processing",
                    "task_id": task.id,
                    "charged_amount": pricing_result.get("total_cost", 0),
                    "text_cost": pricing_result.get("text_cost", 0),
                    "file_cost": pricing_result.get("file_cost", 0),
                    "voice_cost": pricing_result.get("voice_cost", 0),
                    "total_pages": pricing_result.get("total_pages", 0),
                    "voice_duration": voice_duration if voice_file else 0,  # ✅ RETURN VALIDATED DURATION
                    "cost_per_page": pricing_result.get("cost_per_page", 0),
                    "is_free": pricing_result.get("is_free", False),
                    "message": _("درخواست تحلیل ارسال شد"),
                },
                status=status.HTTP_202_ACCEPTED,
            )

        except ValidationError as e:
            raise e
        except Exception as e:
            logger.error(f"Error in analyze: {e}", exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        parameters=[OpenApiParameter(name="task_id", type=str, required=True)],
        responses={200: {"type": "object", "properties": {"status": {"type": "string"}, "analysis": {"type": "string"}}}},
    )
    @action(detail=False, methods=["GET"], url_path="status")
    def check_status(self, request):
        """Check the status of a document analysis task"""
        task_id = request.query_params.get("task_id")

        if not task_id:
            return Response({"error": _("Task ID is required")}, status=status.HTTP_400_BAD_REQUEST)

        from celery.result import AsyncResult

        result = AsyncResult(task_id)

        if result.state == "SUCCESS":
            result_data = result.get()

            if result_data.get("status") == "success":
                return Response(
                    {
                        "status": "completed",
                        "analysis": result_data.get("analysis", ""),
                        "log_pid": result_data.get("log_pid", ""),
                    }
                )
            else:
                return Response(
                    {
                        "status": "error",
                        "message": result_data.get("message", "An unknown error occurred"),
                    }
                )

        elif result.state == "FAILURE":
            return Response({"status": "failed", "error": str(result.result)})

        else:
            return Response({"status": "processing"})

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "analysis": {"type": "string"},
                    "prompt": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                },
            }
        }
    )
    @action(detail=False, methods=["GET"], url_path="latest")
    def latest_analysis(self, request):
        """Get the latest analysis for the user"""
        try:
            user = request.user
            ai_type = request.query_params.get("ai_type")
            all_ = request.query_params.get("all", "0")

            if all_ == "1":
                query = AnalyzerLog.objects.filter(user=user)
                if ai_type:
                    query = query.filter(ai_type=ai_type)

                all_logs = query.order_by("-created_at")

                if not all_logs.exists():
                    return Response(
                        {"status": "not_found", "message": _("No analysis found for this user")},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                analyses_list = []
                for log in all_logs:
                    analyses_list.append(
                        {
                            "analysis": log.analysis_text,
                            "prompt": log.prompt,
                            "created_at": log.created_at,
                            "ai_session_id": log.ai_session.pid if log.ai_session else None,
                        }
                    )

                return Response(
                    {
                        "status": "success",
                        "analyses": analyses_list,
                    }
                )

            else:
                query = AnalyzerLog.objects.filter(user=user)
                if ai_type:
                    query = query.filter(ai_type=ai_type)

                latest_log = query.order_by("-created_at").first()

                if latest_log:
                    return Response(
                        {
                            "status": "success",
                            "analysis": {
                                "analysis": latest_log.analysis_text,
                                "prompt": latest_log.prompt,
                            },
                            "created_at": latest_log.created_at,
                            "ai_session_id": latest_log.ai_session.pid if latest_log.ai_session else None,
                        }
                    )

                return Response(
                    {"status": "not_found", "message": _("No analysis found for this user")},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except Exception as e:
            logger.error(f"Error fetching latest analysis: {e}")
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
