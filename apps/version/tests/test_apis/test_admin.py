import json

from django.forms import model_to_dict
from django.urls import reverse
from faker import Faker

from apps.version.models import AppVersion
from base_utils.base_tests import TainoBaseAPITestCase


class AdminAppVersionTestCase(TainoBaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user.is_admin = True
        self.user.save()
        self.list_url = reverse("version:version_admin:admin-version-api-list")
        self.post_url = reverse("version:version_admin:admin-version-api-list")

        self.fake = Faker()
        valid_version = self.fake.pylist(nb_elements=5, value_types=int, allowed_types=int)
        self.version_detail = dict(
            os="android",
            build_number=valid_version[2],
            version_name=valid_version[-1],
            changelog=self.fake.sentence(nb_words=20),
            update_status="not_updated",
            creator_id=self.user.id,
        )
        self.version_obj, _ = AppVersion.objects.get_or_create(**self.version_detail)
        self.all_version_objs = AppVersion.objects.all()

    def test_app_version_success(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.list_url, content_type="application/json")

        self.assertTrue(
            response.status_code == 200,
            f"operation failed: \nstatus code is: {response.status_code}\n respnse_data: {response}",
        )
        self.assertEqual(len(response.json().get("result")), self.all_version_objs.count())

    def test_app_version_retrieve_success(self):
        # dummy_data = {"pid": self.version_obj.pid}
        self.retrieve_url = reverse("version:version_admin:admin-version-api-detail", kwargs={"pid": self.version_obj.pid})
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.retrieve_url, content_type="application/json")

        self.assertTrue(
            response.status_code == 200,
            f"operation failed: \nstatus code is: {response.status_code}\n respnse_data: {response}",
        )
        self.assertEqual(response.json().get("result")["pid"], self.version_obj.pid)

    def test_app_version_post_success(self):

        dummy_data = self.version_detail
        dummy_data["pid"] = "tetaeteatea"
        dummy_data["os"] = "mac"

        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.post_url, data=json.dumps(dummy_data), content_type="application/json")

        self.assertTrue(
            response.status_code == 201,
            f"operation failed: \nstatus code is: {response.status_code}\n respnse_data: {response}",
        )
        self.assertEqual(response.json().get("result")["os"], dummy_data["os"])

    def test_app_version_put_success(self):

        data = self.all_version_objs.last()
        self.put_url = reverse("version:version_admin:admin-version-api-detail", kwargs={"pid": data.pid})

        dummy_data = model_to_dict(data)
        dummy_data["pid"] = "1231241413413"
        dummy_data["os"] = "mac"

        response = self.client.put(self.put_url, data=json.dumps(dummy_data), content_type="application/json")

        self.assertTrue(
            response.status_code == 200,
            f"operation failed: \nstatus code is: {response.status_code}\n respnse_data: {response}",
        )
        self.assertEqual(response.json().get("result")["os"], dummy_data["os"])

    def test_app_version_patch_success(self):
        data = self.all_version_objs.last()
        self.patch_url = reverse("version:version_admin:admin-version-api-detail", kwargs={"pid": data.pid})
        dummy_data = model_to_dict(data)
        dummy_data["pid"] = "000000000"
        dummy_data["os"] = "windows"
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(self.patch_url, data=json.dumps(dummy_data), content_type="application/json")

        self.assertTrue(
            response.status_code == 200,
            f"operation failed: \nstatus code is: {response.status_code}\n respnse_data: {response}",
        )
        self.assertEqual(response.json().get("result")["os"], dummy_data["os"])

    # def test_app_version_delete_success(self):
    #     data = self.all_version_objs.last()
    #     self.delete_url = reverse("version:version_admin:admin-version-api-detail", kwargs={"pid": data.pid})
    #
    #     dummy_data = model_to_dict(data)
    #     self.client.force_authenticate(user=self.user)
    #
    #     response = self.client.delete(self.post_url, data=dummy_data, content_type="application/json")
    #
    #     self.assertTrue(
    #         response.status_code == 204,
    #         f"operation failed: \nstatus code is: {response.status_code}\n respnse_data: {response}",
    #     )
