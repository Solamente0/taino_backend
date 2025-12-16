from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from apps.analyzer.api.v1.serializers.manual_request import (
    ManualRequestEmailDocumentUploadSerializer,
    ManualRequestDocumentUploadSerializer,
    ManualRequestEmailWithTemplateSerializer,
)
from apps.setting.services.query import GeneralSettingsQuery
from apps.wallet.services.wallet import WalletService
from base_utils.subscription import check_bypass_user_payment
from base_utils.views.mobile import TainoMobileGenericViewSet
import logging

logger = logging.getLogger(__name__)


class ManualRequestFileUploadViewSet(TainoMobileGenericViewSet):
    """
    ViewSet for handling court notification image uploads
    """

    parser_classes = [MultiPartParser]

    def get_serializer_class(self):
        if self.action == "upload_documents_email":
            return ManualRequestEmailDocumentUploadSerializer
        elif self.action == "upload_documents_email_template":
            return ManualRequestEmailWithTemplateSerializer
        return ManualRequestDocumentUploadSerializer

    def check_user_balance(self):
        user = self.request.user
        data = self.request.data
        bypassed_roles = GeneralSettingsQuery.get_bypass_premium_feature_per_roles()
        check_rules = check_bypass_user_payment(user, bypassed_roles, valid_static_name="v_manual_request")

        if check_rules:
            price = 0
        else:
            price = GeneralSettingsQuery.get_ai_chat_price_by_type("v_manual_request")
        coin_balance = WalletService.get_wallet_coin_balance(user)
        description = f"v_manual_request تحلیل اسناد با استفاده از هوش مصنوعی "

        if coin_balance < price:
            raise ValidationError("در کیف پول شارژ کافی برای ایجاد این درخواست را ندارید!")
        else:
            tr = WalletService.use_coins(
                user=user,
                coin_amount=price,
                description=description,
                reference_id=f"ai_chat_v_manual_request",
            )
        return True

    @extend_schema(
        request=ManualRequestDocumentUploadSerializer,
        responses={
            201: inline_serializer(
                name="ManualRequestDocumentUploadResponseSerializer",
                fields={
                    "document_pids": serializers.ListField(child=serializers.CharField()),
                    "description": serializers.CharField(),
                    "count": serializers.IntegerField(),
                },
            )
        },
    )
    @action(methods=["POST"], detail=False, url_path="upload-documents")
    def upload_documents(self, request, **kwargs):
        """Upload images for manual request"""
        self.check_user_balance()

        serializer = ManualRequestDocumentUploadSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(data=result, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=ManualRequestEmailDocumentUploadSerializer,
        responses={
            201: inline_serializer(
                name="ManualRequestEmailDocumentUploadResponseSerializer",
                fields={
                    "success": serializers.BooleanField(),
                    "message": serializers.CharField(),
                    "recipient": serializers.EmailField(),
                    "subject": serializers.CharField(),
                    "attachments_count": serializers.IntegerField(),
                },
            )
        },
    )
    @action(methods=["POST"], detail=False, url_path="send-documents")
    def upload_documents_email(self, request, **kwargs):
        """Upload documents and send directly via email without saving to database"""
        logger.info("=== STARTING upload_documents_email ===")

        self.check_user_balance()
        logger.info("=== Balance check passed ===")

        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context())
        logger.info("=== Serializer created ===")

        try:
            serializer.is_valid(raise_exception=True)
            logger.info("=== Serializer validation passed ===")
        except Exception as e:
            logger.error(f"=== Serializer validation failed: {e} ===")
            raise

        try:
            result = serializer.save()
            logger.info(f"=== Serializer save completed: {result} ===")
        except Exception as e:
            logger.error(f"=== Serializer save failed: {e} ===")
            raise

        return Response(data=result, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=ManualRequestEmailWithTemplateSerializer,
        responses={
            201: inline_serializer(
                name="ManualRequestEmailTemplateResponseSerializer",
                fields={
                    "success": serializers.BooleanField(),
                    "message": serializers.CharField(),
                    "recipient": serializers.EmailField(),
                    "subject": serializers.CharField(),
                    "template_used": serializers.CharField(),
                    "attachments_count": serializers.IntegerField(),
                },
            )
        },
    )
    @action(methods=["POST"], detail=False, url_path="send-documents-template")
    def upload_documents_email_template(self, request, **kwargs):
        """Upload documents and send via email with HTML template without saving to database"""
        self.check_user_balance()
        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(data=result, status=status.HTTP_201_CREATED)
