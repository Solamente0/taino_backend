# apps/file_to_text/api/v1/views.py
import logging
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from django.utils.translation import gettext_lazy as _

from apps.file_to_text.models import FileToTextLog
from apps.file_to_text.api.v1.serializers import (
    FileToTextSubmitSerializer,
    FileToTextLogSerializer,
)
from apps.wallet.services.wallet import WalletService
from apps.setting.services.query import GeneralSettingsQuery
from base_utils.permissions import HasTainoMobileUserPermission
from base_utils.views.mobile import TainoMobileGenericViewSet
from base_utils.subscription import check_bypass_user_payment
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)


class FileToTextViewSet(TainoMobileGenericViewSet):
    """ViewSet for file to text ctainoersion"""

    permission_classes = [IsAuthenticated, HasTainoMobileUserPermission]
    queryset = FileToTextLog.objects.all()
    serializer_class = FileToTextLogSerializer

    def get_queryset(self):
        """Filter logs by current user"""
        return FileToTextLog.objects.filter(user=self.request.user).order_by("-created_at")

    @extend_schema(request=FileToTextSubmitSerializer, responses={201: FileToTextLogSerializer})
    @action(detail=False, methods=["POST"], url_path="ctainoert")
    def ctainoert(self, request):
        """Submit file to text ctainoersion and deduct coins"""
        try:
            user = request.user
            serializer = FileToTextSubmitSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data

            filename = validated_data.get("filename")
            extracted_text = validated_data.get("extracted_text")
            file_type = validated_data.get("file_type")
            file_size = validated_data.get("file_size", 0)

            # Calculate text statistics
            character_count = len(extracted_text)
            word_count = len(extracted_text.split())

            # Get pricing - check for bypass
            # bypassed_roles = GeneralSettingsQuery.get_bypass_premium_feature_per_roles()
            # check_rules = check_bypass_user_payment(
            #     user,
            #     bypassed_roles,
            #     valid_static_name="file_to_text"
            # )
            #
            # if check_rules:
            #     coins_needed = 0
            #     logger.info(f"✅ User {user.pid} bypassed payment for file_to_text")
            # else:
            #     # Calculate coins based on character count
            #     # Base price + price per 1000 characters
            #     base_price = GeneralSettingsQuery.get_ai_chat_price_by_type("file_to_text_base") or 5
            #     price_per_1k_chars = GeneralSettingsQuery.get_ai_chat_price_by_type("file_to_text_per_1k") or 2
            #
            #     additional_chars = max(0, character_count - 1000)  # First 1000 chars included in base
            #     additional_cost = (additional_chars // 1000) * price_per_1k_chars
            #
            #     coins_needed = int(base_price + additional_cost)
            #
            # # Check balance and deduct coins
            # if coins_needed > 0:
            #     coin_balance = WalletService.get_wallet_coin_balance(user)
            #
            #     if coin_balance < coins_needed:
            #         raise ValidationError(
            #             f"موجودی ناکافی: {coins_needed} سکه نیاز است، {coin_balance} سکه موجود است"
            #         )
            #
            #     # Deduct coins
            #     WalletService.use_coins(
            #         user=user,
            #         coin_amount=coins_needed,
            #         description=f"تبدیل فایل به متن: {filename}",
            #         reference_id=f"file_to_text_{filename}_{user.pid}",
            #     )
            #
            #     logger.info(f"💰 Deducted {coins_needed} coins from user {user.pid}")

            # Save log
            file_to_text_log = FileToTextLog.objects.create(
                user=user,
                original_filename=filename,
                extracted_text=extracted_text,
                file_type=file_type,
                file_size=file_size,
                coins_used=0,
                character_count=character_count,
                word_count=word_count,
            )

            logger.info(f"✅ File to text ctainoersion saved: {file_to_text_log.pid}")

            return Response(
                {
                    "status": "success",
                    "message": _("فایل با موفقیت به متن تبدیل شد"),
                    "log": FileToTextLogSerializer(file_to_text_log).data,
                    "coins_used": 0,
                    "statistics": {
                        "character_count": character_count,
                        "word_count": word_count,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except ValidationError as e:
            raise e
        except Exception as e:
            logger.error(f"❌ Error in file to text ctainoersion: {e}", exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(responses={200: FileToTextLogSerializer(many=True)})
    @action(detail=False, methods=["GET"], url_path="history")
    def history(self, request):
        """Get user's file to text ctainoersion history"""
        try:
            logs = self.get_queryset()[:20]  # Last 20 ctainoersions
            serializer = FileToTextLogSerializer(logs, many=True)

            return Response(
                {"status": "success", "results": serializer.data, "count": logs.count()}, status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"❌ Error fetching history: {e}", exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
