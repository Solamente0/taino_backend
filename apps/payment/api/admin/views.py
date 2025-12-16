import logging

from django.db import models
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from apps.payment.models import CouponUsage, Coupon, ZarinpalPaymentConfig
from base_utils.views.admin import TainoAdminModelViewSet
from ..v1.serializers import CouponCreateUpdateSerializer, CouponSerializer, CouponUsageSerializer
from .serializers import AdminZarinpalConfigSerializer, AdminZarinpalConfigCreateUpdateSerializer

logger = logging.getLogger(__name__)


class AdminCouponViewSet(TainoAdminModelViewSet):
    """
    API endpoint for admin coupon management
    """

    queryset = Coupon.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["code", "description"]
    filterset_fields = ["is_active", "discount_type", "country", "state", "city", "specific_user", "package"]
    ordering_fields = ["created_at", "valid_from", "valid_to", "current_uses"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CouponCreateUpdateSerializer
        return CouponSerializer

    @action(detail=True, methods=["get"])
    def usages(self, request, pid=None):
        """Get all usages for a specific coupon"""
        coupon = self.get_object()
        queryset = CouponUsage.objects.filter(coupon=coupon).order_by("-created_at")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CouponUsageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CouponUsageSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pid=None):
        """Deactivate a coupon"""
        coupon = self.get_object()
        coupon.is_active = False
        coupon.save()
        return Response({"message": "کد تخفیف با موفقیت غیرفعال شد", "coupon": CouponSerializer(coupon).data})

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get coupon statistics"""
        total_coupons = Coupon.objects.count()
        active_coupons = Coupon.objects.filter(is_active=True).count()

        now = timezone.now()
        expired_coupons = Coupon.objects.filter(valid_to__lt=now).count()

        total_usages = CouponUsage.objects.count()
        total_discount_amount = CouponUsage.objects.all().aggregate(total=models.Sum("discount_amount"))["total"] or 0

        return Response(
            {
                "total_coupons": total_coupons,
                "active_coupons": active_coupons,
                "expired_coupons": expired_coupons,
                "total_usages": total_usages,
                "total_discount_amount": total_discount_amount,
            }
        )


class AdminZarinpalConfigViewSet(TainoAdminModelViewSet):
    """
    API endpoint for admin Zarinpal payment gateway configuration
    """

    queryset = ZarinpalPaymentConfig.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["merchant_id", "description"]
    filterset_fields = ["is_active", "is_sandbox", "is_default"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return AdminZarinpalConfigCreateUpdateSerializer
        return AdminZarinpalConfigSerializer

    @action(detail=True, methods=["post"])
    def set_default(self, request, pid=None):
        """Set this configuration as the default"""
        config = self.get_object()
        config.is_default = True
        config.is_active = True  # Ensure it's active when set as default
        config.save()
        return Response(
            {"message": "تنظیمات زرین‌پال به عنوان پیش‌فرض تنظیم شد", "config": AdminZarinpalConfigSerializer(config).data}
        )

    @action(detail=True, methods=["post"])
    def activate(self, request, pid=None):
        """Activate this configuration"""
        config = self.get_object()
        config.is_active = True
        config.save()
        return Response(
            {"message": "تنظیمات زرین‌پال با موفقیت فعال شد", "config": AdminZarinpalConfigSerializer(config).data}
        )

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pid=None):
        """Deactivate this configuration"""
        config = self.get_object()
        if config.is_default:
            return Response({"error": "نمی‌توان تنظیمات پیش‌فرض را غیرفعال کرد"}, status=400)
        config.is_active = False
        config.save()
        return Response(
            {"message": "تنظیمات زرین‌پال با موفقیت غیرفعال شد", "config": AdminZarinpalConfigSerializer(config).data}
        )

    @action(detail=False, methods=["get"])
    def current(self, request):
        """Get current default Zarinpal configuration"""
        config = ZarinpalPaymentConfig.get_default()
        if config:
            return Response(AdminZarinpalConfigSerializer(config).data)
        # Return settings-based configuration if no database config exists
        from django.conf import settings

        return Response(
            {
                "merchant_id": settings.ZARINPAL_MERCHANT_ID,
                "is_sandbox": settings.ZARINPAL_SANDBOX,
                "api_key": None,
                "is_default": True,
                "is_active": True,
                "description": "Default configuration from settings",
            }
        )
