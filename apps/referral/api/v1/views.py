from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from base_utils.views.mobile import TainoMobileGenericViewSet
from .serializers import ReferralShareSerializer, ReferralLinkSerializer


class ReferralLinkViewSet(TainoMobileGenericViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=[ReferralLinkSerializer])
    @action(
        methods=["GET"],
        detail=False,
        url_name="share",
    )
    def share(self, request, **kwargs):
        ser = ReferralShareSerializer(context={"request": request})
        return Response(data=ser.data, status=status.HTTP_200_OK)
