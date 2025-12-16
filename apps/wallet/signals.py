# In apps/wallet/signals.py
import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.setting.services.query import GeneralSettingsQuery
from apps.wallet.models import Wallet

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=User)
def create_wallet_for_new_user(sender, instance, created, **kwargs):
    """
    Create a new wallet for each newly registered user
    """
    from apps.wallet.services.wallet import WalletService

    if created:
        # Use get_or_create to avoid potential race conditions
        wallet, wallet_created = Wallet.objects.get_or_create(
            user=instance,
            defaults={
                "balance": 0,
                "currency": instance.currency if hasattr(instance, "currency") and instance.currency else "IRR",
            },
        )

        # If this is a new wallet, give free coins based on user role
        if wallet_created:
            try:
                # Check if the user has the 'lawyer' role
                is_lawyer = False
                if hasattr(instance, "role") and instance.role:
                    is_lawyer = instance.role.static_name == "lawyer"
                print(f"log for is lawyer {is_lawyer=}", flush=True)
                # Award coins based on role
                if is_lawyer:
                    # Give 50 coins for lawyers
                    coin_amount = GeneralSettingsQuery.get_lawyer_register_prize_coin()
                    description = "50 سکه رایگان به مناسبت عضویت در سامانه (وکیل)"
                else:
                    # Give 10 coins for other users
                    coin_amount = GeneralSettingsQuery.get_user_register_prize_coin()
                    description = "10 سکه رایگان به مناسبت عضویت در سامانه"

                # Add coins to the user's wallet
                WalletService.reward_coins(
                    user=instance, coin_amount=coin_amount, description=description, reference_id="welcome_bonus"
                )

                logger.info(
                    f"Awarded {coin_amount} welcome coins to user {instance.id} ({instance.email or instance.phone_number})"
                )

            except Exception as e:
                logger.error(f"Error while giving welcome coins to user {instance.id}: {str(e)}")
