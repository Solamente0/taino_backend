import logging

from django.db.models import QuerySet, Q
from apps.wallet.models import Wallet, Transaction, CoinSettings
from base_utils.services import AbstractBaseQuery

logger = logging.getLogger(__name__)


class WalletQuery(AbstractBaseQuery):
    """
    Query class for wallet operations
    """

    @staticmethod
    def get_active_wallets() -> QuerySet[Wallet]:
        """
        Get all active wallets
        """
        return Wallet.objects.filter(is_active=True)

    @staticmethod
    def get_user_wallet(user_id) -> Wallet:
        """
        Get a specific user's wallet
        """
        return Wallet.objects.filter(user__pid=user_id, is_active=True).first()

    @staticmethod
    def get_user_transactions(user_id, transaction_type=None) -> QuerySet[Transaction]:
        """
        Get transactions for a specific user
        """
        wallet = WalletQuery.get_user_wallet(user_id)
        if not wallet:
            return Transaction.objects.none()

        # Get all transactions for this wallet
        transactions = Transaction.objects.filter(wallet=wallet)

        # Filter by transaction type if specified
        if transaction_type:
            transactions = transactions.filter(type=transaction_type)

        # Ensure we're showing the most recent transactions first
        transactions = transactions.order_by("-created_at")

        # Log the query and result count for debugging
        logger.info(f"Getting transactions for user {user_id}, found {transactions.count()} transactions")

        return transactions

    @staticmethod
    def get_user_coin_transactions(user_id, transaction_type=None) -> QuerySet[Transaction]:
        """
        Get coin transactions for a specific user (transactions with coin_amount > 0)
        """
        wallet = WalletQuery.get_user_wallet(user_id)
        if not wallet:
            return Transaction.objects.none()

        # Get all transactions with coin_amount > 0
        transactions = Transaction.objects.filter(wallet=wallet, coin_amount__gt=0)

        # Filter by transaction type if specified
        if transaction_type:
            transactions = transactions.filter(type=transaction_type)

        # Ensure we're showing the most recent transactions first
        transactions = transactions.order_by("-created_at")

        # Log the query and result count for debugging
        logger.info(f"Getting coin transactions for user {user_id}, found {transactions.count()} transactions")

        return transactions

    @staticmethod
    def get_coin_settings(is_active=True) -> QuerySet[CoinSettings]:
        """
        Get coin settings
        """
        queryset = CoinSettings.objects.all()
        if is_active:
            queryset = queryset.filter(is_active=True)
        return queryset.order_by("-created_at")

    @staticmethod
    def get_default_coin_settings() -> CoinSettings:
        """
        Get default coin settings
        """
        return CoinSettings.get_default()
