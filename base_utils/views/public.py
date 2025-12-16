from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import GenericViewSet


class PublicBaseViewMixin:
    lookup_url_kwarg = "pid"
    lookup_field = "pid"
    permission_classes = [IsAuthenticatedOrReadOnly]


class TainoPubicListOnlyViewSet(PublicBaseViewMixin, ListModelMixin, GenericViewSet):
    pass


class TainoPubicRetrieveOnlyViewSet(PublicBaseViewMixin, RetrieveModelMixin, GenericViewSet):
    pass


class TainoPublicGenericViewSet(PublicBaseViewMixin, GenericViewSet):
    pass
