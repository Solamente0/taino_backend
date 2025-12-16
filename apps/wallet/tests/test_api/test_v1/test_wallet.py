# apps/wallet/tests/test_api.py
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from decimal import Decimal

from apps.wallet.models import Wallet, Transaction
from base_utils.base_tests import TainoBaseAPITestCase


class WalletAPITests(TainoBaseAPITestCase):

    def setUp(self):
        super().setUp()
        self.wallet = Wallet.objects.get(user=self.user)  # Wallet should be auto-created
        self.wallet.balance = Decimal("1000.00")
        self.wallet.save()

        self.details_url = reverse("wallet:wallet_v1:wallet-details")
        self.balance_url = reverse("wallet:wallet_v1:wallet-balance")
        self.deposit_url = reverse("wallet:wallet_v1:wallet-deposit")
        self.withdraw_url = reverse("wallet:wallet_v1:wallet-withdraw")
        self.transactions_url = reverse("wallet:wallet_v1:wallet-transactions")

    def test_get_wallet_details(self):
        response = self.client.get(self.details_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["balance"], str(self.wallet.balance))
        self.assertEqual(response.data["currency"], "IRR")

    def test_get_wallet_balance(self):
        response = self.client.get(self.balance_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["balance"], str(self.wallet.balance))
        self.assertEqual(response.data["currency"], "IRR")

    def test_deposit_funds(self):
        data = {"amount": "500.00", "description": "Test deposit"}

        response = self.client.post(self.deposit_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["amount"], "500.00")
        self.assertEqual(response.data["type"], "deposit")
        self.assertEqual(response.data["status"], "completed")

        # Check that the balance was updated
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("1500.00"))

    def test_withdraw_funds(self):
        data = {"amount": "300.00", "description": "Test withdrawal"}

        response = self.client.post(self.withdraw_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["amount"], "300.00")
        self.assertEqual(response.data["type"], "withdrawal")
        self.assertEqual(response.data["status"], "completed")

        # Check that the balance was updated
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("700.00"))

    def test_withdrawal_insufficient_funds(self):
        data = {"amount": "2000.00", "description": "Test excessive withdrawal"}  # More than current balance

        response = self.client.post(self.withdraw_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

        # Check that the balance was not changed
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("1000.00"))

    def test_get_transactions(self):
        # Create some transactions
        baker.make(Transaction, wallet=self.wallet, amount=Decimal("100.00"), type="deposit", status="completed", _quantity=3)

        baker.make(
            Transaction, wallet=self.wallet, amount=Decimal("50.00"), type="withdrawal", status="completed", _quantity=2
        )

        # Test all transactions
        response = self.client.get(self.transactions_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

        # Test filtering by type
        response = self.client.get(f"{self.transactions_url}?type=deposit")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        # Test filtering by type
        response = self.client.get(f"{self.transactions_url}?type=withdrawal")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
