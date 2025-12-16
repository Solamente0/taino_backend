import json
from unittest import skip

from django.forms import model_to_dict
from django.urls import reverse

from apps.ratelimit.models import RateLimitConfig
from base_utils.base_tests import TainoBaseAPITestCase


@skip
class AdminRateLimitTestCase(TainoBaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.list_url = reverse("ratelimit:ratelimit_admin:admin-ratelimit-api-list")
        self.post_url = reverse("ratelimit:ratelimit_admin:admin-ratelimit-api-list")

        self.limit_detail = dict(
            name="ChangePassword",
            key="user_or_ip",
            rate="11/h",
            group=None,
            method="POST",
            method_name="post",
            block=True,
            creator_id=self.user.pk,
        )
        self.ratelimit_obj, _ = RateLimitConfig.objects.get_or_create(**self.limit_detail)
        self.all_ratelimit_objs = RateLimitConfig.objects.all()

    def test_ratelimit_success(self):
        self.client.force_authenticate(user=self.user)

        # print("self.headers", self.headers)
        response = self.client.get(self.list_url, content_type="application/json")

        self.assertTrue(
            response.status_code == 200,
            f"operation failed: \nstatus code is: {response.status_code}\n respnse_data: {response}",
        )
        self.assertEqual(len(response.data), self.all_ratelimit_objs.count())

    def test_ratelimit_retrieve_success(self):
        # dummy_data = {"pid": self.ratelimit_obj.pid}
        self.retrieve_url = reverse(
            "ratelimit:ratelimit_admin:admin-ratelimit-api-detail", kwargs={"pid": self.ratelimit_obj.pid}
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.retrieve_url, content_type="application/json")
        self.assertTrue(response.status_code == 200)
        self.assertEqual(response.data["name"], self.ratelimit_obj.name)

    def test_ratelimit_post_success(self):

        dummy_data = self.limit_detail
        dummy_data["name"] = "ForgotPassword"
        self.client.force_login(self.user)
        response = self.client.post(self.post_url, data=json.dumps(dummy_data), content_type="application/json")
        self.assertTrue(response.status_code == 201)
        self.assertEqual(response.data["name"], dummy_data["name"])

    def test_ratelimit_put_success(self):

        data = self.all_ratelimit_objs.last()
        self.put_url = reverse("ratelimit:ratelimit_admin:admin-ratelimit-api-detail", kwargs={"pid": data.pid})
        dummy_data = model_to_dict(data)
        dummy_data["name"] = "Login"
        dummy_data["creator"] = self.user.pk
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.put_url, data=json.dumps(dummy_data), content_type="application/json")
        self.assertTrue(response.status_code == 200)
        self.assertEqual(response.data["name"], dummy_data["name"])

    def test_ratelimit_patch_success(self):
        data = self.all_ratelimit_objs.last()
        self.patch_url = reverse("ratelimit:ratelimit_admin:admin-ratelimit-api-detail", kwargs={"pid": data.pid})
        dummy_data = model_to_dict(data)
        dummy_data["name"] = "Register"
        dummy_data["creator"] = self.user.pk
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(self.patch_url, data=json.dumps(dummy_data), content_type="application/json")

        self.assertTrue(response.status_code == 200)
        self.assertEqual(response.data["name"], dummy_data["name"])

    # def test_ratelimit_delete_success(self):
    #     data = self.all_ratelimit_objs.last()
    #     self.delete_url = reverse("ratelimit:ratelimit_admin:admin-ratelimit-api-detail", kwargs={"pid": data.pid})
    #
    #     dummy_data = model_to_dict(data)
    #     self.client.force_authenticate(user=self.user)
    #
    #     response = self.client.delete(self.post_url, data=dummy_data, content_type="application/json")
    #
    #     self.assertTrue(response.status_code == 204)
