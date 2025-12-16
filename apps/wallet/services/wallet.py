import logging
from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.wallet.models import Wallet, Transaction, CoinSettings

User = get_user_model()
logger = logging.getLogger(__name__)


class WalletService:
    """
    Service class for wallet operations
    """

    @staticmethod
    def get_or_create_wallet(user):
        """
        Get user's wallet or create a new one if it doesn't exist
        """
        wallet, created = Wallet.objects.get_or_create(user=user)
        return wallet

    @staticmethod
    def get_wallet_balance(user):
        """
        Get the current balance of a user's wallet
        """
        wallet = WalletService.get_or_create_wallet(user)
        return wallet.balance

    @staticmethod
    def get_wallet_coin_balance(user):
        """
        Get the current coin balance of a user's wallet
        """
        wallet = WalletService.get_or_create_wallet(user)
        return wallet.coin_balance

    @staticmethod
    @transaction.atomic
    def deposit(user, amount, reference_id=None, description=None):
        """
        Add funds to user's wallet
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")

        wallet = WalletService.get_or_create_wallet(user)

        trans = Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            type="deposit",
            status="completed",
            reference_id=reference_id,
            description=description,
        )

        wallet.balance += Decimal(amount)
        wallet.save()

        logger.info(f"Deposited {amount} to {user}'s wallet. New balance: {wallet.balance}")
        return trans

    @staticmethod
    @transaction.atomic
    def withdraw(user, amount, reference_id=None, description=None):
        """
        Withdraw funds from user's wallet
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")

        wallet = WalletService.get_or_create_wallet(user)

        if wallet.balance < amount:
            raise ValueError("Insufficient funds")

        trans = Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            type="withdrawal",
            status="completed",
            reference_id=reference_id,
            description=description,
        )

        wallet.balance -= Decimal(amount)
        wallet.save()

        logger.info(f"Withdrew {amount} from {user}'s wallet. New balance: {wallet.balance}")
        return trans

    @staticmethod
    @transaction.atomic
    def purchase_coins(user, rial_amount, reference_id=None, description=None):
        """
        Purchase coins with Rials
        """
        if rial_amount <= 0:
            raise ValueError("Purchase amount must be positive")

        wallet = WalletService.get_or_create_wallet(user)

        if wallet.balance < rial_amount:
            raise ValueError("Insufficient funds")

        # Calculate ctainoersion
        exchange_rate = CoinSettings.get_exchange_rate()
        coin_amount = CoinSettings.ctainoert_rial_to_coin(rial_amount)

        tr = Transaction.objects.create(
            wallet=wallet,
            amount=rial_amount,
            coin_amount=coin_amount,
            type="coin_purchase",
            status="completed",
            reference_id=reference_id,
            description=description or f"تبدیل {rial_amount} ریال به {coin_amount} سکه",
            exchange_rate=exchange_rate,
        )

        wallet.balance -= Decimal(rial_amount)
        wallet.coin_balance += Decimal(coin_amount)
        wallet.save()

        logger.info(
            f"Purchased {coin_amount} coins for {rial_amount} rials for {user}. New coin balance: {wallet.coin_balance}"
        )
        return tr

    @staticmethod
    @transaction.atomic
    def buy_coins_from_payment(user, rial_amount, reference_id=None, description=None):
        """
        Buy coins directly from payment (without deducting from wallet balance)
        """
        if rial_amount <= 0:
            raise ValueError("Purchase amount must be positive")

        wallet = WalletService.get_or_create_wallet(user)

        # Calculate ctainoersion
        exchange_rate = CoinSettings.get_exchange_rate()
        coin_amount = CoinSettings.ctainoert_rial_to_coin(rial_amount)

        trans = Transaction.objects.create(
            wallet=wallet,
            amount=rial_amount,
            coin_amount=coin_amount,
            type="coin_purchase",
            status="completed",
            reference_id=reference_id,
            description=description or f"خرید {coin_amount} سکه با {rial_amount} ریال",
            exchange_rate=exchange_rate,
        )

        wallet.coin_balance += Decimal(coin_amount)
        wallet.save()

        logger.info(
            f"Purchased {coin_amount} coins for {rial_amount} rials for {user} directly. New coin balance: {wallet.coin_balance}"
        )
        return trans

    @staticmethod
    @transaction.atomic
    def use_coins(user, coin_amount, reference_id=None, description=None):
        """
        Use coins from user's wallet
        """
        if coin_amount < 0:
            raise ValueError("Coin amount must be positive")

        wallet = WalletService.get_or_create_wallet(user)

        if wallet.coin_balance < coin_amount:
            raise ValueError("موجودی سکه کافی نیست")

        # Calculate rial value for record-keeping
        rial_value = CoinSettings.ctainoert_coin_to_rial(coin_amount)
        exchange_rate = CoinSettings.get_exchange_rate()

        tr = Transaction.objects.create(
            wallet=wallet,
            amount=rial_value,  # Rial equivalent for reference
            coin_amount=coin_amount,
            type="coin_usage",
            status="completed",
            reference_id=reference_id,
            description=description,
            exchange_rate=exchange_rate,
        )
        print(f"{tr=}", flush=True)
        wallet.coin_balance -= Decimal(coin_amount)
        wallet.save()

        logger.info(f"Used {coin_amount} coins from {user}'s wallet. New coin balance: {wallet.coin_balance}")
        return tr

    @staticmethod
    @transaction.atomic
    def refund_coins(user, coin_amount, reference_id=None, description=None):
        """
        Refund coins to user's wallet
        """
        if coin_amount <= 0:
            raise ValueError("Coin amount must be positive")

        wallet = WalletService.get_or_create_wallet(user)

        # Calculate rial value for record-keeping
        rial_value = CoinSettings.ctainoert_coin_to_rial(coin_amount)
        exchange_rate = CoinSettings.get_exchange_rate()

        trans = Transaction.objects.create(
            wallet=wallet,
            amount=rial_value,  # Rial equivalent for reference
            coin_amount=coin_amount,
            type="coin_refund",
            status="completed",
            reference_id=reference_id,
            description=description,
            exchange_rate=exchange_rate,
        )

        wallet.coin_balance += Decimal(coin_amount)
        wallet.save()

        logger.info(f"Refunded {coin_amount} coins to {user}'s wallet. New coin balance: {wallet.coin_balance}")
        return trans

    @staticmethod
    @transaction.atomic
    def reward_coins(user, coin_amount, reference_id=None, description=None):
        """
        Reward coins to user's wallet (e.g., for promotions, referrals)
        """
        if coin_amount <= 0:
            raise ValueError("Coin amount must be positive")

        wallet = WalletService.get_or_create_wallet(user)

        # Calculate rial value for record-keeping
        rial_value = CoinSettings.ctainoert_coin_to_rial(coin_amount)
        exchange_rate = CoinSettings.get_exchange_rate()

        tr = Transaction.objects.create(
            wallet=wallet,
            amount=rial_value,  # Rial equivalent for reference
            coin_amount=coin_amount,
            type="coin_reward",
            status="completed",
            reference_id=reference_id,
            description=description,
            exchange_rate=exchange_rate,
        )

        wallet.coin_balance += Decimal(coin_amount)
        wallet.save()

        logger.info(f"Rewarded {coin_amount} coins to {user}'s wallet. New coin balance: {wallet.coin_balance}")
        return tr

    @staticmethod
    @transaction.atomic
    def pay_for_consultation(user, amount, reference_id=None, description=None, use_coins=False):
        """
        Pay for a consultation service
        """
        if amount <= 0:
            raise ValueError("Payment amount must be positive")

        wallet = WalletService.get_or_create_wallet(user)

        if use_coins:
            # Ctainoert amount to coins
            exchange_rate = CoinSettings.get_exchange_rate()
            coin_amount = CoinSettings.ctainoert_rial_to_coin(amount)

            if wallet.coin_balance < coin_amount:
                raise ValueError("موجودی سکه کافی نیست")

            trans = Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                coin_amount=coin_amount,
                type="consultation_fee",
                status="completed",
                reference_id=reference_id,
                description=description or "پرداخت هزینه مشاوره با سکه",
                exchange_rate=exchange_rate,
            )

            wallet.coin_balance -= Decimal(coin_amount)
            wallet.save()

            logger.info(
                f"Paid {coin_amount} coins for consultation from {user}'s wallet. New coin balance: {wallet.coin_balance}"
            )
        else:
            if wallet.balance < amount:
                raise ValueError("Insufficient funds")

            trans = Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                type="consultation_fee",
                status="completed",
                reference_id=reference_id,
                description=description,
            )

            wallet.balance -= Decimal(amount)
            wallet.save()

            logger.info(f"Paid {amount} for consultation from {user}'s wallet. New balance: {wallet.balance}")

        return trans

    @staticmethod
    def get_transaction_history(user, transaction_type=None, limit=None):
        """
        Get transaction history for a user
        """
        wallet = WalletService.get_or_create_wallet(user)
        transactions = wallet.transactions.all()

        if transaction_type:
            transactions = transactions.filter(type=transaction_type)

        if limit:
            transactions = transactions[:limit]

        return transactions

    @staticmethod
    @transaction.atomic
    def deduct_balance(
        user, amount, transaction_type="payment", description=None, reference_id=None, metadata=None, use_coins=True
    ):
        """
        Deduct funds from user's wallet balance or coins

        Args:
            user: The user to charge
            amount: Amount to deduct
            transaction_type: Transaction type (default: "payment")
            description: Transaction description
            reference_id: External reference ID
            metadata: Additional metadata for the transaction (stored as JSON)
            use_coins: Whether to use coins instead of rial balance

        Returns:
            bool: True if successful, False otherwise

        Raises:
            ValueError: If amount is invalid or insufficient funds
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        wallet = WalletService.get_or_create_wallet(user)

        if use_coins:
            # Ctainoert amount to coins
            from apps.wallet.models import CoinSettings

            coin_amount = CoinSettings.ctainoert_rial_to_coin(amount)
            exchange_rate = CoinSettings.get_exchange_rate()

            # Check if user has enough coins
            if wallet.coin_balance < coin_amount:
                return False

            # Create transaction with metadata
            tr = Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                coin_amount=coin_amount,
                type=transaction_type,
                status="completed",
                reference_id=reference_id,
                description=description or f"پرداخت با {coin_amount} سکه",
                exchange_rate=exchange_rate,
                metadata=metadata,
            )

            # Update wallet coin balance
            wallet.coin_balance -= Decimal(coin_amount)
            wallet.save()

            logger.info(
                f"Deducted {coin_amount} coins from {user}'s wallet for {transaction_type}. New coin balance: {wallet.coin_balance}"
            )
            return True
        else:
            # Check if user has enough rial balance
            if wallet.balance < amount:
                return False

            # Create transaction with metadata
            tr = Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                type=transaction_type,
                status="completed",
                reference_id=reference_id,
                description=description,
                metadata=metadata,
            )

            # Update wallet balance
            wallet.balance -= Decimal(amount)
            wallet.save()

            logger.info(f"Deducted {amount} from {user}'s wallet for {transaction_type}. New balance: {wallet.balance}")
            return True
