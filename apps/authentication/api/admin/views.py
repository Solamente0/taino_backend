import logging

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from base_utils.permissions import RefreshHasAdminAccess, AccessTokenHasAdminAccess
from .serializers import AdminCustomTokenObtainPairSerializer, AdminCustomTokenRefreshSerializer, AdminLogoutSerializer

log = logging.getLogger(__name__)
User = get_user_model()


class AdminTokenObtainPairView(TokenObtainPairView):
    serializer_class = AdminCustomTokenObtainPairSerializer
    permission_classes = [AccessTokenHasAdminAccess]
    throttle_scope = "auth"


class AdminTokenRefreshView(TokenRefreshView):
    serializer_class = AdminCustomTokenRefreshSerializer
    permission_classes = [RefreshHasAdminAccess]
    throttle_scope = "auth"


# class AdminLogoutView(TokenRefreshView):
#     serializer_class = AdminLogoutSerializer
#     permission_classes = [AllowAny]


@extend_schema(request=AdminLogoutSerializer)
@api_view(["POST"])
@permission_classes([AllowAny])
def logout(request, **kwargs):
    # TODO: logic
    return Response({}, status=status.HTTP_200_OK)
