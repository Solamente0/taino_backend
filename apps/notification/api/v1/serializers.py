from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.notification.models import UserNotificationToken, UserSentNotification, UserSentRequests
from base_utils.serializers.base import TainoBaseModelSerializer, TainoBaseSerializer


class NotificationMinimalUserSerializer(TainoBaseModelSerializer):
    avatar = serializers.FileField()

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "avatar"]


class UserNotificationTokenSerializer(TainoBaseModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserNotificationToken
        fields = ["user", "token", "user_agent"]


class UserNotificationListRetrieveSerializer(TainoBaseModelSerializer):

    class Meta:
        model = UserSentNotification
        fields = [
            "pid",
            "name",
            "description",
            "link",
            "seen",
            "created_at",
            "updated_at",
        ]


class UserNotificationUpdateSerializer(TainoBaseModelSerializer):

    class Meta:
        model = UserSentNotification
        fields = []


class UserNotificationBulkUpdateSerializer(TainoBaseSerializer):
    pids = serializers.ListField(child=serializers.CharField())


class UserRequestsListRetrieveSerializer(TainoBaseModelSerializer):
    from_user = NotificationMinimalUserSerializer()
    to_user = NotificationMinimalUserSerializer()
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        if obj.from_content_object and hasattr(obj.from_content_object, "name"):
            return obj.from_content_object.name

        return None

    class Meta:
        model = UserSentRequests
        fields = ["pid", "request_type", "from_user", "to_user", "seen", "created_at", "updated_at", "name"]


#
# class UserRequestsUpdateSerializer(TainoBaseModelSerializer):
#
#     class Meta:
#         model = UserSentRequests
#         fields = ["seen"]
#
#     def update(self, instance: UserSentRequests, validated_data):
#         status = validated_data.pop("status")
#         super().update(instance, validated_data)
#
#         from_instance = None
#         if instance.from_content_type.model == "expertprofileagency":
#             from_instance = ExpertProfileAgency.objects.filter(id=instance.from_object_id).first()
#
#         if instance.from_content_type.model == "expertprofilecoworker":
#             from_instance = ExpertProfileCoworker.objects.filter(id=instance.from_object_id).first()
#
#         if from_instance:
#             from_instance.status = status
#             from_instance.save()
#             instance.is_done = True
#             instance.seen = True
#             instance.save()
#
#             if status == ExpertProfileRelationChoices.BANNED.value:
#                 expert = ExpertProfile.objects.get(owner=instance.from_user)
#                 ExpertProfileRelationsService(instance.to_user).block(expert)
#
#         return instance
