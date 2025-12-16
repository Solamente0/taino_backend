# apps/wallet/apps.py
from django.apps import AppConfig


class WalletConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.wallet"
    verbose_name = "کیف پول"

    def ready(self):
        try:
            import apps.wallet.signals
        except ImportError:
            pass
