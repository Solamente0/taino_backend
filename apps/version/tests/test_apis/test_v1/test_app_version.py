# import json
# from time import sleep
#
# from django.urls import reverse
# from faker import Faker
# from model_bakery import baker
# from rest_framework import status
#
# from apps.version.models import AppVersion
# from base_utils.base_tests import TainoBaseAPITestCase
#
#
# class AppVersionTestCase(TainoBaseAPITestCase):
#     def setUp(self):
#         super().setUp()
#         self.base_url = reverse("version:version_v1:version-info-api-list")
#         self.status_base_url = reverse("version:version_v1:version-info-api-get-status")
#         self.fake = Faker()
#         valid_version = self.fake.pylist(nb_elements=5, value_types=int, allowed_types=int)
#         self.version_detail = dict(
#             os="android",
#             build_number=valid_version[2],
#             version_name=valid_version[-1],
#             changelog=self.fake.sentence(nb_words=20),
#         )
#         self.version_obj = baker.make(AppVersion, **self.version_detail)
#
#     def test_app_version_success(self):
#         dummy_data = {
#             "os": self.version_detail.get("os"),
#             "build_number": self.version_detail.get("build_number"),
#         }
#         self.client.force_authenticate(user=self.user)
#
#         response = self.client.get(self.base_url, data=dummy_data, content_type="application/json")
#         self.assertTrue(response.status_code == 200)
#
#     def test_app_version_status_success(self):
#         dummy_data = {
#             "os": self.version_detail.get("os"),
#             "build_number": self.version_detail.get("build_number"),
#         }
#         self.client.force_authenticate(user=self.user)
#
#         response = self.client.get(self.status_base_url, data=dummy_data, content_type="application/json")
#         self.assertTrue(response.status_code == 200)
#
#     def test_app_version_unauthorized_success(self):
#         dummy_data = {
#             "os": self.version_detail.get("os"),
#             "build_number": self.version_detail.get("build_number"),
#         }
#         self.client.logout()
#
#         response = self.client.get(self.base_url, data=dummy_data, content_type="application/json")
#         self.assertTrue(response.status_code == 200)
#
#     def test_app_version_not_found_success(self):
#         dummy_data = {"os": "linux", "build_number": 57576}
#         self.client.force_authenticate(user=self.user)
#
#         response = self.client.get(self.base_url, data=dummy_data, content_type="application/json")
#         self.assertTrue(response.status_code == status.HTTP_200_OK)
#
#     def test_app_version_info_invalid_input_data_error(self):
#         self.client.force_authenticate(user=self.user)
#         response = self.client.get(self.base_url, content_type="application/json")
#         self.assertTrue(response.status_code == 400)
