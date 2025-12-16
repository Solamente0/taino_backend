# apps/chat/management/commands/init_ai_pricing.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.setting.models import GeneralSetting, GeneralSettingChoices

User = get_user_model()


class Command(BaseCommand):
    help = "Initialize AI chat pricing settings"

    def handle(self, *args, **options):
        # Get or create admin user for creator
        admin_user = User.objects.filter(is_admin=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR("No admin user found. Please create an admin user first."))
            return

        # Define the AI pricing settings
        ai_pricing_settings = [
            {"key": GeneralSettingChoices.AI_CHAT_PRICE_V.value, "value": "1000", "is_active": True},  # Base price for V
            {
                "key": GeneralSettingChoices.AI_CHAT_PRICE_V_PLUS.value,
                "value": "2000",  # Base price for V+
                "is_active": True,
            },
            {
                "key": GeneralSettingChoices.AI_CHAT_PRICE_V_X.value,
                "value": "3000",  # Base price for V++
                "is_active": True,
            },
        ]

        # Create or update AI pricing settings
        for setting_data in ai_pricing_settings:
            setting, created = GeneralSetting.objects.update_or_create(
                key=setting_data["key"],
                defaults={
                    "value": setting_data["value"],
                    "is_active": setting_data["is_active"],
                    "creator": admin_user,
                },
            )

            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} AI pricing setting: {setting.key} = {setting.value}"))
