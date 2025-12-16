from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.messaging.api.v1.serializers import SMSPackageSerializer
from apps.messaging.models import SMSPackage
from base_utils.views.mobile import TainoMobileGenericViewSet


class SMSPackageViewSet(TainoMobileGenericViewSet):
    """
    ViewSet for SMS packages
    """

    serializer_class = SMSPackageSerializer
    permission_classes = [AllowAny]  # Anyone can view packages

    def get_queryset(self):
        return SMSPackage.objects.filter(is_active=True).order_by("order", "value")

    @extend_schema(responses={200: SMSPackageSerializer(many=True)})
    def list(self, request):
        """
        List all active SMS packages
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
