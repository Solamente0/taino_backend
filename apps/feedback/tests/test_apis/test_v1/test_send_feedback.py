import json

from django.urls import reverse
from faker import Faker
from model_bakery import baker

from apps.feedback.models import FeedBack
from base_utils.base_tests import TainoBaseAPITestCase


class SendFeedbackTestCase(TainoBaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.base_url = reverse("feedback:feedback_v1:send-feedback-api-list")
        self.fake = Faker()
        self.feed_objs = baker.make(FeedBack, _quantity=10, creator=self.user)
        self.feed_count = FeedBack.objects.count()

    def test_send_feedback_success(self):
        dummy_data = {
            "message": self.fake.sentence(5),
            "feedback_type": "ok",
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.base_url, data=json.dumps(dummy_data), content_type="application/json")
        self.assertTrue(response.status_code == 201)
        self.assertEqual(response.data["message"], dummy_data["message"])

    def test_get_feedbacks_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.base_url, content_type="application/json")
        self.assertTrue(response.status_code == 200)
        self.feed_count = FeedBack.objects.count()
        self.assertEqual(len(response.data), self.feed_count)

    def test_feedback_get_success(self):
        feed = FeedBack.objects.first()
        pid = feed.pid
        detail_url = reverse("feedback:feedback_v1:send-feedback-api-detail", kwargs={"pid": pid})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(detail_url, content_type="application/json")
        self.assertTrue(response.status_code == 200)
        self.assertEqual(response.data["message"], feed.message)
