# apps/payment/tests/test_services.py
from unittest import mock
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.payment.models import Payment
from apps.payment.services import PaymentService
from apps.payment.services.zarinpal import ZarinpalService

User = get_user_model()


class ZarinpalServiceTestCase(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create(
            email="test@example.com",
            phone_number="09123456789",
        )
        self.user.set_password("testpassword")
        self.user.save()

    @mock.patch("apps.payment.services.zarinpal.requests.post")
    def test_request_payment_success(self, mock_post):
        # Mock successful response from Zarinpal
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Status": 100, "Authority": "A00000000000000000000000000217885159"}
        mock_post.return_value = mock_response

        zarinpal = ZarinpalService()
        success, payment_url, data = zarinpal.request_payment(
            amount=10000,
            description="Test payment",
            callback_url="http://example.com/callback",
            mobile="09123456789",
            email="test@example.com",
        )

        self.assertTrue(success)
        self.assertTrue(payment_url.endswith("A00000000000000000000000000217885159"))
        self.assertEqual(data["Status"], 100)

    @mock.patch("apps.payment.services.zarinpal.requests.post")
    def test_request_payment_error(self, mock_post):
        # Mock error response from Zarinpal
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Status": -1,
        }
        mock_post.return_value = mock_response

        zarinpal = ZarinpalService()
        success, error_message, data = zarinpal.request_payment(
            amount=10000, description="Test payment", callback_url="http://example.com/callback"
        )

        self.assertFalse(success)
        self.assertIn("اطلاعات ارسال شده ناقص", error_message)
        self.assertEqual(data["Status"], -1)

    @mock.patch("apps.payment.services.zarinpal.requests.post")
    def test_verify_payment_success(self, mock_post):
        # Mock successful verification response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Status": 100, "RefID": "12345678"}
        mock_post.return_value = mock_response

        zarinpal = ZarinpalService()
        success, ref_id, data = zarinpal.verify_payment(authority="A00000000000000000000000000217885159", amount=10000)

        self.assertTrue(success)
        self.assertEqual(ref_id, "12345678")
        self.assertEqual(data["Status"], 100)

    @mock.patch("apps.payment.services.zarinpal.requests.post")
    def test_verify_payment_error(self, mock_post):
        # Mock error verification response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Status": -22,
        }
        mock_post.return_value = mock_response

        zarinpal = ZarinpalService()
        success, ref_id, data = zarinpal.verify_payment(authority="A00000000000000000000000000217885159", amount=10000)

        self.assertFalse(success)
        self.assertIsNone(ref_id)
        self.assertEqual(data["Status"], -22)


class PaymentServiceTestCase(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create(
            email="test@example.com",
            phone_number="09123456789",
        )
        self.user.set_password("testpassword")
        self.user.save()

    @mock.patch("apps.payment.services.zarinpal.ZarinpalService.request_payment")
    def test_create_payment_success(self, mock_request_payment):
        # Mock successful payment request
        mock_request_payment.return_value = (
            True,
            "https://www.zarinpal.com/pg/StartPay/A00000000000000000000000000217885159",
            {"Authority": "A00000000000000000000000000217885159", "Status": 100},
        )

        payment_service = PaymentService()
        payment = payment_service.create_payment(user=self.user, amount=10000, description="Test payment")

        # Check if payment was created correctly
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.amount, 10000)
        self.assertEqual(payment.description, "Test payment")
        self.assertEqual(payment.status, "pending")
        self.assertEqual(payment.authority, "A00000000000000000000000000217885159")
        self.assertTrue(payment.payment_url.endswith("A00000000000000000000000000217885159"))

    @mock.patch("apps.payment.services.zarinpal.ZarinpalService.request_payment")
    def test_create_payment_error(self, mock_request_payment):
        # Mock failed payment request
        mock_request_payment.return_value = (False, "اطلاعات ارسال شده ناقص است", {"Status": -1})

        payment_service = PaymentService()
        payment = payment_service.create_payment(user=self.user, amount=10000, description="Test payment")

        # Check if payment was created with error status
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.amount, 10000)
        self.assertEqual(payment.description, "Test payment")
        self.assertEqual(payment.status, "failed")
        self.assertEqual(payment.error_code, "-1")
        self.assertEqual(payment.error_message, "اطلاعات ارسال شده ناقص است")

    @mock.patch("apps.payment.services.zarinpal.ZarinpalService.verify_payment")
    def test_verify_payment_success(self, mock_verify_payment):
        # Create a test payment
        payment = Payment.objects.create(
            user=self.user, amount=10000, description="Test payment", authority="A00000000000000000000000000217885159"
        )

        # Mock successful verification
        mock_verify_payment.return_value = (True, "12345678", {"Status": 100})

        payment_service = PaymentService()
        result = payment_service.verify_payment(payment)

        # Check if verification was successful
        self.assertTrue(result)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "successful")
        self.assertEqual(payment.ref_id, "12345678")
        self.assertTrue(payment.verified)

    @mock.patch("apps.payment.services.zarinpal.ZarinpalService.verify_payment")
    def test_verify_payment_error(self, mock_verify_payment):
        # Create a test payment
        payment = Payment.objects.create(
            user=self.user, amount=10000, description="Test payment", authority="A00000000000000000000000000217885159"
        )

        # Mock failed verification
        mock_verify_payment.return_value = (False, None, {"Status": -22})

        payment_service = PaymentService()
        result = payment_service.verify_payment(payment)

        # Check if verification failed
        self.assertFalse(result)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "failed")
        self.assertEqual(payment.error_code, "-22")
        self.assertFalse(payment.verified)
