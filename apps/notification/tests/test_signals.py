from django.contrib.contenttypes.models import ContentType
from model_bakery import baker

from apps.expert_profile.models import ExpertProfileCoworker, ExpertProfileAgency
from apps.notification.models import UserSentRequests
from base_utils.base_tests import TainoBaseAPITestCase


class CoworkerRequestsDeleteTest(TainoBaseAPITestCase):

    def setUp(self) -> None:

        self.coworker = baker.make(ExpertProfileCoworker)
        self.notification_request = baker.make(
            UserSentRequests,
            from_object_id=self.coworker.id,
            from_content_type=ContentType.objects.get_for_model(ExpertProfileCoworker),
            request_type=UserSentRequests.RequestTypeChoice.COWORKER.value,
        )

    def test_delete_coworker_request_deletes_coworker_notification_request(self):
        self.assertEqual(UserSentRequests.objects.count(), 1)

        ExpertProfileCoworker.objects.all().delete()

        self.assertEqual(UserSentRequests.objects.all().count(), 0)


class AgencyRequestsDeleteTest(TainoBaseAPITestCase):

    def setUp(self) -> None:

        self.agency = baker.make(ExpertProfileAgency)
        self.notification_request = baker.make(
            UserSentRequests,
            from_object_id=self.agency.id,
            from_content_type=ContentType.objects.get_for_model(ExpertProfileAgency),
            request_type=UserSentRequests.RequestTypeChoice.AGENCY.value,
        )

    def test_delete_agency_request_deletes_coworker_notification_request(self):
        self.assertEqual(UserSentRequests.objects.count(), 1)

        ExpertProfileAgency.objects.all().delete()

        self.assertEqual(UserSentRequests.objects.all().count(), 0)
