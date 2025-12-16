from rest_framework import serializers

from apps.referral.models import ReferralLink
from base_utils.serializers.base import TainoBaseModelSerializer, TainoBaseSerializer


class ReferralLinkSerializer(TainoBaseModelSerializer):
    referral_code = serializers.SerializerMethodField()
    referral_link = serializers.SerializerMethodField()
    # referral_deep_link = serializers.SerializerMethodField()

    def get_referral_code(self, obj):
        return obj.token

    def get_referral_link(self, obj):
        return obj.link

    # def get_referral_deep_link(self, obj):
    #     return None

    class Meta:
        model = ReferralLink
        fields = [
            "referral_code",
            "referral_link",
            # "referral_deep_link",
        ]


class ReferralShareSerializer(TainoBaseSerializer):
    @property
    def data(self):
        # todo this login should not be here
        user = self.context["request"].user
        try:
            referral_link = ReferralLink.objects.get(user=user)
        except Exception as e:
            referral_link = ReferralLink.objects.create(user=user)

        return ReferralLinkSerializer(instance=referral_link).data
