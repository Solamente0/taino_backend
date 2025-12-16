from rest_framework import serializers

from apps.version.models import AppVersion
from apps.version.services.check_version import check_version
from base_utils.serializers.base import TainoBaseSerializer, TainoBaseModelSerializer


class InputAppVersionSerializer(TainoBaseSerializer):
    os = serializers.CharField(
        required=True,
    )
    build_number = serializers.IntegerField(required=True)

    # def validate_os(self, value):
    #     if app_version := get_object_or_404(klass=AppVersion, os=value):
    #         return app_version.os
    #     else:
    #         raise ValidationError(_("os not found"))


class OutputAppVersionModelSerializer(TainoBaseModelSerializer):
    icon_url = serializers.SerializerMethodField(method_name="get_icon_url")

    def get_icon_url(self, obj):
        return getattr(obj, "icon_url", None)

    class Meta:
        model = AppVersion
        fields = (
            "os",
            "version_name",
            "build_number",
            "changelog",
            "admin_status",
            "update_status",
            "icon_url",
        )
        read_only_fields = fields


class OutputAppVersionStatusModelSerializer(TainoBaseModelSerializer):

    class Meta:
        model = AppVersion
        fields = ("update_status", "build_number", "changelog")
        read_only_fields = fields


class VersionStatusCheckSerializer(TainoBaseSerializer):
    @property
    def data(self):
        # todo this login should not be here
        request = self.context["request"]
        app_version, update_status = check_version(**request.query_params.dict())

        if app_version:
            app_version.update_status = update_status
            return OutputAppVersionStatusModelSerializer(app_version).data

        return {"update_status": update_status}
