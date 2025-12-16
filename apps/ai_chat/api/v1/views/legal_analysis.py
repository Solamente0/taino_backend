# apps/ai_chat/api/v1/views.py
import base64
import logging

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.ai_chat.api.v1.serializers import LegalDocumentAnalysisRequestSerializer
from apps.ai_chat.models import LegalAnalysisLog
from apps.wallet.services.wallet import WalletService
from base_utils.enums import LegalDocumentAnalysisType
from base_utils.permissions import HasTainoMobileUserPermission
from base_utils.views.mobile import TainoMobileGenericViewSet
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class LegalAnalysisViewSet(TainoMobileGenericViewSet):
    """ViewSet for legal document analysis using AI"""

    permission_classes = [IsAuthenticated, HasTainoMobileUserPermission]

    @extend_schema(
        request=LegalDocumentAnalysisRequestSerializer,
        responses={202: {"type": "object", "properties": {"status": {"type": "string"}, "task_id": {"type": "string"}}}},
    )
    @action(detail=False, methods=["POST"], url_path="analyze")
    def analyze(self, request):
        """Analyze legal documents with pricing check"""
        try:
            data = request.data
            user = request.user

            serializer = LegalDocumentAnalysisRequestSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data

            ai_type = validated_data.get("ai_type", "v_x")

            # ✅ VOICE: Get voice file and duration
            voice_file = request.FILES.get("voice_file")
            voice_duration = None

            if voice_file:
                # Get duration from form data
                voice_duration = request.data.get("voice_duration")
                if voice_duration:
                    try:
                        voice_duration = int(float(voice_duration))
                    except (ValueError, TypeError):
                        voice_duration = None

                print(f"🎙️ Voice file received: {voice_file.name}, duration: {voice_duration}s", flush=True)

            # ✅ FIXED: Use dynamic pricing calculator
            from apps.ai_chat.services.ai_pricing_calculator import AIPricingCalculator

            # Calculate character count ONLY from prompt (not documents)
            prompt = validated_data.get("prompt", "")
            character_count = len(prompt)

            # ✅ Include voice duration in pricing
            pricing_result = AIPricingCalculator.calculate_complete_cost(
                user=user,
                ai_config_static_name=ai_type,
                character_count=character_count,
                max_tokens_requested=None,
                voice_duration_seconds=voice_duration,  # ✅ ADD THIS
            )

            if not pricing_result.get("success"):
                raise ValidationError(pricing_result.get("error", "خطا در محاسبه قیمت"))

            # Check if it's free (bypass)
            if pricing_result.get("is_free"):
                logger.info(f"Free analysis for user {user.pid}: {pricing_result.get('bypass_reason')}")
            else:
                # Check balance and charge
                price = pricing_result.get("total_cost", 0)
                coin_balance = WalletService.get_wallet_coin_balance(user)
                description = f"{ai_type} تحلیل اسناد حقوقی با استفاده از هوش مصنوعی"

                if voice_file:
                    description += f" (با فایل صوتی {voice_duration}s)"

                if coin_balance < price:
                    raise ValidationError(f"موجودی ناکافی: {price} سکه نیاز است، {coin_balance} سکه موجود است")

                WalletService.use_coins(
                    user=user,
                    coin_amount=price,
                    description=description,
                    reference_id=f"legal_analysis_{ai_type}_{validated_data.get('ai_session_id', 'none')}",
                )

            ai_session_id = validated_data.get("ai_session_id")
            basic_prompt = validated_data.get("prompt", "")
            legal_analyze_request_type = validated_data.get(
                "legal_analysis_user_request_choice", LegalDocumentAnalysisType.LEGAL_DOCUMENT_ANALYSIS
            )

            if legal_analyze_request_type == "other":
                user_req_prompt = ""
            else:
                user_req_prompt = LegalDocumentAnalysisType.get_sanitized_label_for_key(legal_analyze_request_type)

            custom_prompt = f"\n\nدرخواست کاربر: {user_req_prompt}\n\nتوضیحات کاربر: {basic_prompt} \n\n"

            # ✅ Add voice indicator to prompt if voice file exists
            if voice_file:
                custom_prompt += "\n\n[فایل صوتی ضمیمه شده است]\n\n"

            # ✅ Prepare voice data for task
            voice_data = None
            if voice_file:
                import base64

                voice_file.seek(0)
                voice_data = {
                    "filename": voice_file.name,
                    "content_type": voice_file.content_type,
                    "content_b64": base64.b64encode(voice_file.read()).decode("utf-8"),
                    "duration": voice_duration,
                }

            from apps.ai_chat.tasks import analyze_legal_documents_v2x

            task = analyze_legal_documents_v2x.delay(
                user_pid=str(user.pid),
                document_data=data,
                prompt=custom_prompt,
                user_request_choice=user_req_prompt,
                ai_session_id=ai_session_id,
                ai_type=ai_type,
                voice_data=voice_data,  # ✅ ADD THIS
            )

            return Response(
                {
                    "status": "processing",
                    "task_id": task.id,
                    "charged_amount": pricing_result.get("total_cost", 0),
                    "text_cost": pricing_result.get("text_cost", 0),
                    "voice_cost": pricing_result.get("voice_cost", 0),
                    "voice_duration": voice_duration,
                    "is_free": pricing_result.get("is_free", False),
                    "message": _("Documents submitted for analysis. Processing has started in the background."),
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except ValidationError as e:
            raise e
        except Exception as e:
            logger.error(f"Error submitting documents for analysis: {e}", exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        parameters=[OpenApiParameter(name="task_id", type=str, required=True)],
        responses={200: {"type": "object", "properties": {"status": {"type": "string"}, "analysis": {"type": "string"}}}},
    )
    @action(detail=False, methods=["GET"], url_path="status")
    def status(self, request):
        """Check the status of a legal analysis task"""
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
                        "analysis_result": result_data.get("analysis_result", ""),
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
                    "created_at": {"type": "string", "format": "date-time"},
                },
            }
        }
    )
    @action(detail=False, methods=["GET"], url_path="latest")
    def latest_analysis(self, request):
        """Get the latest legal analysis for the user"""
        try:
            user = request.user
            ai_type = request.query_params.get("ai_type")
            all_ = request.query_params.get("all", 0)

            if all_ == "1":
                all_logs = LegalAnalysisLog.objects.filter(user=user, ai_type=ai_type).order_by("-created_at")

                if not all_logs:
                    return Response(
                        {"status": "not_found", "message": _("No legal analysis found for this user")},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                analysis_list = []
                for log in all_logs:
                    analysis_list.append(
                        {
                            "analysis": log.analysis_text,
                            "user_request_analysis": log.user_request_analysis_text,
                            "user_request_choice": log.user_request_choice,
                            "created_at": log.created_at,
                            "ai_session_id": log.ai_session.pid if log.ai_session else None,
                        }
                    )

                return Response(
                    {
                        "status": "success",
                        "analyses": analysis_list,
                    }
                )

            else:
                latest_log = LegalAnalysisLog.objects.filter(user=user, ai_type=ai_type).order_by("-created_at").first()

            if latest_log:
                return Response(
                    {
                        "status": "success",
                        "analysis": {
                            "analysis": latest_log.analysis_text,
                            "user_request_analysis": latest_log.user_request_analysis_text,
                            "user_request_choice": latest_log.user_request_choice,
                        },
                        "created_at": latest_log.created_at,
                        "ai_session_id": latest_log.ai_session.pid if latest_log.ai_session else None,
                    }
                )

            return Response(
                {"status": "not_found", "message": _("No legal analysis found for this user")},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error fetching latest analysis: {e}")
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
