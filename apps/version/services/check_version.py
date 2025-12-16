from apps.version.models import AppVersion
from base_utils.base_models import AdminStatusChoices


def check_version(os: str, build_number: int):

    try:
        # First filter os and active versions
        versions = AppVersion.objects.filter(os=os, admin_status=AdminStatusChoices.ACTIVE)
        if not versions.exists():
            return None, AppVersion.UpdateStatus.NOT_UPDATED.value

        # then filter greater than versions of input build number
        versions = versions.filter(build_number__gt=build_number)
        if not versions.exists():
            return None, AppVersion.UpdateStatus.NOT_UPDATED.value

        # check if exists any force-update version, so update_status must be FORCE_UPDATE
        update_status = None
        if versions.filter(update_status=AppVersion.UpdateStatus.FORCE_UPDATE).exists():
            update_status = AppVersion.UpdateStatus.FORCE_UPDATE.value

        # get last version and return its object with status
        last_version = versions.order_by("-build_number").first()
        if not update_status:
            update_status = last_version.update_status

        return last_version, update_status
    except Exception as e:
        return None, AppVersion.UpdateStatus.NOT_UPDATED.value
