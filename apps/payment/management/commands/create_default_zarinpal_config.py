import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.payment.models import ZarinpalPaymentConfig

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create default Zarinpal payment configuration based on settings"

    def handle(self, *args, **options):
        # Check if a default config already exists
        if ZarinpalPaymentConfig.objects.filter(is_default=True).exists():
            default_config = ZarinpalPaymentConfig.objects.filter(is_default=True).first()
            self.stdout.write(
                self.style.WARNING(
                    f"Default Zarinpal configuration already exists: "
                    f"Merchant ID: {default_config.merchant_id} (Sandbox: {default_config.is_sandbox})"
                )
            )
            return

        # Get settings from Django settings.py
        merchant_id = getattr(settings, "ZARINPAL_MERCHANT_ID", "YOUR-ZARINPAL-MERCHANT-ID")
        is_sandbox = getattr(settings, "ZARINPAL_SANDBOX", True)

        # Create default config
        config = ZarinpalPaymentConfig.objects.create(
            merchant_id=merchant_id,
            is_sandbox=is_sandbox,
            is_active=True,
            is_default=True,
            description="Default configuration created from settings.py",
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created default Zarinpal configuration: "
                f"Merchant ID: {config.merchant_id} (Sandbox: {config.is_sandbox})"
            )
        )
