import logging

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from apps.feedback.api.v1.serializers import (
    OutputFeedbackModelSerializer,
    InputFeedbackModelSerializer,
)
from apps.feedback.models import FeedBack
from base_utils.filters import CreatorFilterBackend
from base_utils.views.mobile import TainoMobileModelViewSet

log = logging.getLogger(__name__)


class FeedBackGenericViewSetAPI(TainoMobileModelViewSet):
    queryset = FeedBack.objects.all()

    serializer_class = OutputFeedbackModelSerializer
    writable_serializer_class = InputFeedbackModelSerializer

    http_method_names = ["get", "options", "head", "post"]

    filter_backends = (SearchFilter, CreatorFilterBackend, DjangoFilterBackend, OrderingFilter)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return self.serializer_class
        return self.writable_serializer_class

    @extend_schema(parameters=[InputFeedbackModelSerializer], responses={201: OutputFeedbackModelSerializer})
    def create(self, request, *args, **kwargs):
        input_serializer = InputFeedbackModelSerializer(data=request.data, context={"request": request})
        input_serializer.is_valid(raise_exception=True)
        validated_data = input_serializer.validated_data
        instance = input_serializer.create(validated_data)
        output = OutputFeedbackModelSerializer(instance=instance)

        return Response(data=output.data, status=status.HTTP_201_CREATED)
