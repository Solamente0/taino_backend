from django.utils.translation import gettext_lazy as _

# from apps.expert_profile.models import ExpertProfileCoworker, ExpertProfileAgency
from apps.notification.models import UserSentRequests
from apps.notification.services.notifications import NotificationPublishManager


class RequestManager:

    def add_expert_follow_request(self, from_user, to_user, follow_object):

        request = UserSentRequests.objects.create(
            from_user=from_user,
            from_content_object=follow_object,
            to_user=to_user,
            request_type=UserSentRequests.RequestTypeChoice.FOLLOW.value,
        )

        return request

    def add_expert_coworker_request(self, coworker_object):
        to_user = coworker_object.to_expert_profile.owner
        if to_user is None:
            return

        request = UserSentRequests.objects.create(
            from_user=coworker_object.from_expert_profile.owner,
            from_content_object=coworker_object,
            to_user=to_user,
            request_type=UserSentRequests.RequestTypeChoice.COWORKER.value,
        )
        NotificationPublishManager(
            to_user, _("New Coworker Request"), _("Check Your New Coworker Request")
        ).send_mobile_notification()

        return request

    def add_expert_agency_request(self, agency_object):
        to_user = agency_object.to_expert_profile.owner
        if to_user is None:
            return
        request = UserSentRequests.objects.create(
            from_user=agency_object.from_expert_profile.owner,
            from_content_object=agency_object,
            to_user=to_user,
            request_type=UserSentRequests.RequestTypeChoice.AGENCY.value,
        )
        NotificationPublishManager(
            to_user, _("New Agency Request"), _("Check Your New Agency Request")
        ).send_mobile_notification()

        return request
