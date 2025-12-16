from rest_framework.generics import GenericAPIView
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet, ModelViewSet

from base_utils.permissions import HasTainoMobileUserPermission


class MobileBaseViewMixin:
    lookup_url_kwarg = "pid"
    lookup_field = "pid"
    permission_classes = [IsAuthenticated, HasTainoMobileUserPermission]


class TainoMobileAPIView(MobileBaseViewMixin, APIView):
    pass


class TainoMobileReadOnlyModelViewSet(MobileBaseViewMixin, ReadOnlyModelViewSet):
    pass


class TainoMobileGenericViewSet(MobileBaseViewMixin, GenericViewSet):
    pass


class TainoMobileGenericAPIView(MobileBaseViewMixin, GenericAPIView):
    pass


class TainoMobileCreateModelMixin(MobileBaseViewMixin, CreateModelMixin):
    pass


class TainoMobileRetrieveModelMixin(MobileBaseViewMixin, RetrieveModelMixin):
    pass


class TainoMobileUpdateModelMixin(MobileBaseViewMixin, UpdateModelMixin):
    pass


class TainoMobileDestroyModelMixin(MobileBaseViewMixin, DestroyModelMixin):
    pass


class TainoMobileListModelMixin(MobileBaseViewMixin, ListModelMixin):
    pass


class TainoMobileModelViewSet(MobileBaseViewMixin, ModelViewSet):
    pass
