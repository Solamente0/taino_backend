import logging

from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.feedback.models import FeedBack
from base_utils.views.admin import TainoAdminModelViewSet
from .filters import FeedbackFilter
from .serializers import OutputFeedbackModelSerializer, InputFeedbackModelSerializer

log = logging.getLogger(__name__)
User = get_user_model()


class FeedbackModelViewSetAPI(TainoAdminModelViewSet):
    queryset = FeedBack.objects.all()

    serializer_class = OutputFeedbackModelSerializer
    writable_serializer_class = InputFeedbackModelSerializer

    filter_backends = (SearchFilter, DjangoFilterBackend, OrderingFilter)
    ordering = ["-created_at"]
    filterset_class = FeedbackFilter

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return self.serializer_class
        return self.writable_serializer_class

    search_fields = ["message"]
