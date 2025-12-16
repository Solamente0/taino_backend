import logging

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, NotFound

from apps.document.services.query import TainoDocumentQuery
from apps.version.models import AppVersion
from base_utils.serializers.base import TainoBaseModelSerializer, TainoBaseSerializer

log = logging.getLogger(__name__)


class InputAdminVersionModelSerializer(TainoBaseModelSerializer):
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())
    icon = serializers.SlugRelatedField(
        queryset=TainoDocumentQuery.get_visible_for_create_update(), slug_field="pid", required=False, allow_null=True
    )

    class Meta:
        model = AppVersion
        fields = [
            "creator",
            "version_name",
            "build_number",
            "changelog",
            "update_status",
            "icon",
            "admin_status",
            "os",
        ]


class InputAdminPIDListAppVersionModelSerializer(TainoBaseSerializer):
    pid = serializers.ListField(child=serializers.CharField())

    @staticmethod
    def validate_pid(value):
        try:
            objs = AppVersion.objects.filter(pid__in=value)
            if not objs.exists():
                raise NotFound()
            return objs
        except Exception as e:
            log.info(f"exception {e} occurred! in file {__file__}")
            raise ValidationError(_("please enter valid pid list"))


class OutputAdminVersionModelSerializer(TainoBaseModelSerializer):
    icon = serializers.FileField()

    class Meta:
        model = AppVersion
        fields = [
            "pid",
            "created_at",
            "updated_at",
            "version_name",
            "build_number",
            "changelog",
            "update_status",
            "icon",
            "admin_status",
            "os",
        ]
