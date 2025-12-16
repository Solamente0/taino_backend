from rest_framework import serializers
from apps.common.models import Newsletter
from base_utils.serializers.base import TainoBaseModelSerializer


class NewsletterSubscribeSerializer(TainoBaseModelSerializer):
    class Meta:
        model = Newsletter
        fields = ["email"]


class NewsletterUnsubscribeSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
