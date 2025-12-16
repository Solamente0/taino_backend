# apps/chat/management/commands/init_openai_legal_config.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.ai_chat.models import ChatAIConfig

User = get_user_model()


class Command(BaseCommand):
    help = "Initialize OpenAI configuration for legal document analysis"

    def handle(self, *args, **options):
        # Get or create admin user for creator
        admin_user = User.objects.filter(is_admin=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR("No admin user found. Please create an admin user first."))
            return

        # Define the AI config for VX
        openai_config = {
            "name": "VX OpenAI Legal Analysis",
            "description": "Advanced legal document analysis using OpenAI Assistants API",
            "static_name": "v_x",
            "model_name": "gpt-4o",  # Using GPT-4o for best analysis capabilities
            "base_url": "https://api.openai.com/v1",
            "system_prompt": "شما یک متخصص حقوقی ایرانی هستید. اسناد پیوست شده را بررسی کنید و با استناد به شماره بند و صفحه، تحلیل حقوقی دقیقی ارائه دهید.",
            "temperature": 0.2,  # Lower temperature for more deterministic outputs
            "max_tokens": 4000,  # Large context for comprehensive analysis
            "is_default": False,  # Not setting as default to avoid affecting other services
        }

        # Create or update AI config
        config, created = ChatAIConfig.objects.update_or_create(
            static_name=openai_config["static_name"],
            defaults={
                **openai_config,
                "creator": admin_user,
                "is_active": True,
                "api_key": "YOUR_OPENAI_API_KEY_HERE",  # Should be set from env variables in production
            },
        )

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} OpenAI legal analysis config: {config.name}"))

        # Instructions for setting the API key
        self.stdout.write(
            self.style.WARNING(
                "\nIMPORTANT: You must set a valid OpenAI API key in the admin panel.\n"
                "1. Go to the admin panel\n"
                "2. Navigate to Chat AI Config\n"
                "3. Find the 'VX OpenAI Legal Analysis' config\n"
                "4. Update the API key field with your OpenAI API key\n"
                "5. Save the changes\n"
            )
        )
