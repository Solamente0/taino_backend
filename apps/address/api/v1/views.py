from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.address.models import Address
from base_utils.filters import CreatorFilterBackend
from base_utils.views.mobile import TainoMobileModelViewSet
from .serializers import OutputAddressListRetrieveSerializer, InputAddressListRetrieveSerializer


class AddressListModelViewSet(TainoMobileModelViewSet):
    queryset = Address.objects.all()

    filter_backends = [CreatorFilterBackend, SearchFilter, DjangoFilterBackend, OrderingFilter]

    search_fields = ["name"]
    ordering_fields = ["name"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return OutputAddressListRetrieveSerializer
        return InputAddressListRetrieveSerializer
