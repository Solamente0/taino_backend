# apps/wallet/api/admin/views.py
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.wallet.models import Wallet, Transaction, CoinSettings, CoinPackage
from base_utils.views.admin import TainoAdminModelViewSet
from .serializers import (
    AdminWalletSerializer,
    AdminTransactionSerializer,
    AdminCoinSettingsSerializer,
    AdminCoinSettingsCreateUpdateSerializer, AdminCoinPackageSerializer, AdminCoinPackageCreateUpdateSerializer
)


class AdminWalletViewSet(TainoAdminModelViewSet):
    """
    Admin ViewSet for wallet management
    """
    queryset = Wallet.objects.all().order_by('-created_at')
    serializer_class = AdminWalletSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'user__phone_number']
    filterset_fields = ['is_active']
    ordering_fields = ['created_at', 'balance', 'coin_balance']

    @action(detail=True, methods=["get"])
    def transactions(self, request, pid=None):
        """Get transactions for a specific wallet"""
        wallet = self.get_object()
        queryset = Transaction.objects.filter(wallet=wallet).order_by('-created_at')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AdminTransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AdminTransactionSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def coin_transactions(self, request, pid=None):
        """Get coin transactions for a specific wallet"""
        wallet = self.get_object()
        queryset = Transaction.objects.filter(wallet=wallet, coin_amount__gt=0).order_by('-created_at')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AdminTransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AdminTransactionSerializer(queryset, many=True)
        return Response(serializer.data)


class AdminTransactionViewSet(TainoAdminModelViewSet):
    """
    Admin ViewSet for transaction management
    """
    queryset = Transaction.objects.all().order_by('-created_at')
    serializer_class = AdminTransactionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['description', 'reference_id', 'wallet__user__first_name', 'wallet__user__last_name']
    filterset_fields = ['type', 'status']
    ordering_fields = ['created_at', 'amount', 'coin_amount']


class AdminCoinSettingsViewSet(TainoAdminModelViewSet):
    """
    Admin ViewSet for coin settings management
    """
    queryset = CoinSettings.objects.all().order_by('-created_at')
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['is_active', 'is_default']
    ordering_fields = ['created_at', 'exchange_rate']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AdminCoinSettingsCreateUpdateSerializer
        return AdminCoinSettingsSerializer

    @action(detail=True, methods=["post"])
    def set_default(self, request, pid=None):
        """Set a coin setting as default"""
        coin_setting = self.get_object()
        coin_setting.is_default = True
        coin_setting.is_active = True  # Ensure it's active
        coin_setting.save()
        return Response({"message": "تنظیمات به عنوان پیش فرض تنظیم شد"})

    @action(detail=True, methods=["post"])
    def activate(self, request, pid=None):
        """Activate a coin setting"""
        coin_setting = self.get_object()
        coin_setting.is_active = True
        coin_setting.save()
        return Response({"message": "تنظیمات فعال شد"})

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pid=None):
        """Deactivate a coin setting"""
        coin_setting = self.get_object()

        # Don't allow deactivating the default setting
        if coin_setting.is_default:
            return Response(
                {"error": "تنظیمات پیش فرض نمی‌تواند غیرفعال شود. ابتدا تنظیمات دیگری را پیش فرض کنید."},
                status=status.HTTP_400_BAD_REQUEST
            )

        coin_setting.is_active = False
        coin_setting.save()
        return Response({"message": "تنظیمات غیرفعال شد"})

    @action(detail=False, methods=["get"])
    def current(self, request):
        """Get current default coin settings"""
        coin_setting = CoinSettings.get_default()
        serializer = self.get_serializer(coin_setting)
        return Response(serializer.data)




class AdminCoinPackageViewSet(TainoAdminModelViewSet):
    """
    Admin ViewSet for coin package management
    """
    queryset = CoinPackage.objects.all().order_by('order', 'value')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['label', 'description']
    filterset_fields = ['is_active', 'role']
    ordering_fields = ['created_at', 'value', 'price', 'order']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AdminCoinPackageCreateUpdateSerializer
        return AdminCoinPackageSerializer

    @action(detail=True, methods=["post"])
    def activate(self, request, pid=None):
        """Activate a coin package"""
        package = self.get_object()
        package.is_active = True
        package.save()
        return Response({"message": "پکیج سکه فعال شد"})

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pid=None):
        """Deactivate a coin package"""
        package = self.get_object()
        package.is_active = False
        package.save()
        return Response({"message": "پکیج سکه غیرفعال شد"})

    @action(detail=False, methods=["get"])
    def by_role(self, request):
        """Get packages grouped by role"""
        from django.db.models import Q
        from apps.authentication.models import UserType

        # Get all active roles
        roles = UserType.objects.filter(is_active=True)

        result = {
            "generic": AdminCoinPackageSerializer(
                CoinPackage.objects.filter(role__isnull=True, is_active=True),
                many=True
            ).data
        }

        for role in roles:
            packages = CoinPackage.objects.filter(role=role, is_active=True)
            if packages.exists():
                result[role.static_name] = {
                    "role_name": role.name,
                    "packages": AdminCoinPackageSerializer(packages, many=True).data
                }

        return Response(result)
