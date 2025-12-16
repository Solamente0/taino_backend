from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet, ModelViewSet

from base_utils.permissions import HasTainoAdminUserPermission


class TainoAdminBaseMixin:
    lookup_url_kwarg = "pid"
    lookup_field = "pid"
    permission_classes = [IsAuthenticated, HasTainoAdminUserPermission]


class TainoAdminModelViewSet(TainoAdminBaseMixin, ModelViewSet):
    pass


class TainoAdminReadOnlyModelViewSet(TainoAdminBaseMixin, ReadOnlyModelViewSet):
    pass


class TainoAdminListBaseModelViewSet(TainoAdminBaseMixin, ListModelMixin, GenericViewSet):
    pass


class TainoAdminCreateModelMixin(TainoAdminBaseMixin, CreateModelMixin):
    pass


class TainoAdminRetrieveModelMixin(TainoAdminBaseMixin, RetrieveModelMixin):
    pass


class TainoAdminUpdateModelMixin(TainoAdminBaseMixin, UpdateModelMixin):
    pass


class TainoAdminDestroyModelMixin(TainoAdminBaseMixin, DestroyModelMixin):
    pass


class TainoAdminListModelMixin(TainoAdminBaseMixin, ListModelMixin):
    pass


class TainoAdminGenericViewSet(TainoAdminBaseMixin, GenericViewSet):
    pass


class TainoAdminRetrieveUpdateAPIView(TainoAdminBaseMixin, RetrieveUpdateAPIView):
    pass
