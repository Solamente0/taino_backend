# import json

#
# from django.contrib.auth import get_user_model
# from django.urls import reverse
#
# from apps.common.models import ReferralLink
# from base_utils.base_tests import TainoBaseAPITestCase
#
# User = get_user_model()
#
#
# class ReferralTestCase(TainoBaseAPITestCase):
#     def setUp(self):
#         super().setUp()
#         self.base_url = reverse("authentication:authentication_v1:authentication-referral-code-api")

#         self.otp = self.fake.unique.random_int(00000, 99999)
#         self.new_pass = self.fake.password()
#         self.referral, _ = ReferralLink.objects.get_or_create(user=self.user)
#         self.foo_access_token = self.get_tokens_for_user(self.user1)

#         self.foo_user_headers = {
#             "Authorization": f"Bearer {self.foo_access_token}",  # Replace with your actual authorization token
#             "Content-Type": "application/json",
#         }
#
#     def test_referral_success(self):
#         dummy_data = {"code": str(self.referral.token)}
#         self.client.force_authenticate(user=self.user1)
#

#         response = self.client.post(self.base_url, data=dummy_data, format="json", headers=self.foo_user_headers)

#         self.assertTrue(
#             response.status_code == 200,
#             f"operation failed: \nstatus code is: {response.status_code}\n respnse_data: {response}",
#         )
#         response = response.json()
#         self.assertEquals(response["meta"]["message"], "Submitted.")
#
#     def test_referral_failure(self):
#         dummy_data = {
#             "code": self.fake.unique.random_int(00000, 99999),
#         }
#         self.client.force_authenticate(user=self.user1)
#
#         response = self.client.post(self.base_url, data=dummy_data, headers=self.foo_user_headers)
#         self.assertTrue(
#             response.status_code == 400,
#             f"failed!\nstatus code is: {response.status_code}\n response_data: {response}",
#         )
