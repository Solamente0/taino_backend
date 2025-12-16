import json

from django.urls import reverse
from faker import Faker
from model_bakery import baker

from apps.feedback.models import FeedBack
from base_utils.base_tests import TainoBaseAPITestCase


class AdminFeedBackTestCase(TainoBaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.list_url = reverse("feedback:feedback_admin:admin-feedback-api-list")
        self.post_url = reverse("feedback:feedback_admin:admin-feedback-api-list")
        self.user.is_admin = True
        self.user.save()
        self.fake = Faker()

        self.feedback_obj = baker.make(FeedBack, _quantity=10)
        self.all_feedback_objs = FeedBack.objects.all()

    def test_feed_back_success(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.list_url, content_type="application/json")
        self.assertTrue(response.status_code == 200)
        self.assertEqual(len(response.data), self.all_feedback_objs.count())

    def test_feed_back_retrieve_success(self):
        # dummy_data = {"pid": self.feedback_obj[0].pid}
        self.retrieve_url = reverse(
            "feedback:feedback_admin:admin-feedback-api-detail", kwargs={"pid": self.feedback_obj[0].pid}
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.retrieve_url, content_type="application/json")

        self.assertTrue(response.status_code == 200)
        self.assertEqual(response.data["pid"], self.feedback_obj[0].pid)

    def test_feed_back_post_success(self):
        dummy_obj = baker.prepare(FeedBack)
        dummy_data = {
            "message": "dummy  message",
        }
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.post_url, data=json.dumps(dummy_data), content_type="application/json")

        self.assertTrue(response.status_code == 201)
        self.assertEqual(response.data["message"], dummy_data["message"])

    def test_feed_back_put_success(self):

        data = self.all_feedback_objs.last()
        self.put_url = reverse("feedback:feedback_admin:admin-feedback-api-detail", kwargs={"pid": data.pid})
        dummy_obj = baker.prepare(FeedBack)
        dummy_data = {
            "message": "dummy  message",
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.put_url, data=json.dumps(dummy_data), content_type="application/json")

        self.assertTrue(response.status_code == 200)
        self.assertEqual(response.data["message"], dummy_data["message"])

    def test_feed_back_patch_success(self):
        data = self.all_feedback_objs.last()
        self.patch_url = reverse("feedback:feedback_admin:admin-feedback-api-detail", kwargs={"pid": data.pid})
        dummy_obj = baker.prepare(FeedBack)
        dummy_data = {
            "message": "dummy  message",
        }
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(self.patch_url, data=json.dumps(dummy_data), content_type="application/json")

        self.assertTrue(response.status_code == 200)
        self.assertEqual(response.data["message"], dummy_data["message"])

    # def test_feed_back_delete_success(self):
    #     data = self.all_feedback_objs.last()
    #     self.delete_url = reverse("feedback:feedback_admin:admin-feedback-api-detail", kwargs={"pid": data.pid})
    #
    #     dummy_data = {"pid": data.pid}
    #     self.client.force_authenticate(user=self.user)
    #
    #     response = self.client.delete(self.post_url, data=dummy_data, content_type="application/json")
    #
    #     self.assertTrue(response.status_code == 204)
