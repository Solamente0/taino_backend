from django.urls import reverse

from base_utils.base_tests import TainoBaseAPITestCase


class ChangePasswordTestCase(TainoBaseAPITestCase):
    def setUp(self):
        super(ChangePasswordTestCase, self).setUp()
        self.base_url = reverse("authentication:authentication_v1:authentication-change-password-api")
        self.new_pass = "Q!W@E#R$T%Y^U&I*O(P){_}+|<>??////,.1;>><<"

    def test_change_password_success(self):
        data = {
            "new_password": self.new_pass,
            "new_password_confirm": self.new_pass,
            "old_password": self.user_password,
        }

        response = self.client.post(self.base_url, data=data)
        self.assertTrue(
            response.status_code == 200,
            f"operation failed: \nstatus code is: {response.status_code}\n respnse_data: {response}",
        )

    def test_change_password_failure(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.base_url)

        self.assertTrue(
            response.status_code == 400,
            f"failed!\nstatus code is: {response.status_code}\n response_data: {response.json()}",
        )

    def test_change_password_new_and_confirm_password_not_equal_error(self):
        data = {
            "new_password": self.new_pass + "5",
            "new_password_confirm": self.new_pass + "6",
            "old_password": self.user_password,
        }
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.base_url, data)
        self.assertTrue(
            response.status_code == 400,
            f"failed!\nstatus code is: {response.status_code}\n response_data: {response.json()}",
        )

    def test_change_password_required_old_password_error(self):
        data = {"new_password": self.new_pass, "new_password_confirm": self.new_pass}
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.base_url, data=data)
        self.assertTrue(
            response.status_code == 400,
            f"failed!\nstatus code is: {response.status_code}\n response_data: {response.json()}",
        )

    def test_change_password_old_password_incorrect_error(self):
        data = {
            "new_password": self.new_pass + "2",
            "new_password_confirm": self.new_pass + "2",
            "old_password": self.user_password + "1",
        }
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.base_url, data=data)
        self.assertTrue(
            response.status_code == 400,
            f"failed!\nstatus code is: {response.status_code}\n response_data: {response.json()}",
        )
