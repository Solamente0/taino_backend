# apps/chat/management/commands/init_ai_config.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.ai_chat.models import ChatAIConfig

User = get_user_model()


class Command(BaseCommand):
    help = "Initialize AI configurations for different chat types"

    def handle(self, *args, **options):
        # Get or create admin user for creator
        admin_user = User.objects.filter(is_admin=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR("No admin user found. Please create an admin user first."))
            return

        # Define the AI configs
        ai_configs = [
            {
                "name": "V AI Assistant",
                "description": "Standard AI assistant with basic capabilities",
                "static_name": "v",
                "model_name": "deepseek-chat",
                "system_prompt": "You are a helpful legal assistant that provides concise answers.",
                "temperature": 0.7,
                "max_tokens": 2000,
                "is_default": True,
            },
            {
                "name": "V+ AI Assistant",
                "description": "Enhanced AI assistant with more capabilities",
                "static_name": "v_plus",
                "model_name": "deepseek-chat-v2",
                "system_prompt": "You are a sophisticated legal assistant with extensive knowledge. Provide detailed answers with legal references when applicable.",
                "temperature": 0.6,
                "max_tokens": 3000,
                "is_default": False,
            },
            {
                "name": "V++ AI Assistant",
                "description": "Premium AI assistant with advanced capabilities",
                "static_name": "v_x",
                "model_name": "deepseek-chat-v3",
                "system_prompt": "You are an expert legal assistant with deep knowledge of Iranian law. Provide comprehensive answers with specific legal codes, precedents, and detailed explanations.",
                "temperature": 0.5,
                "max_tokens": 4000,
                "is_default": False,
            },
        ]

        # Create or update AI configs
        for config_data in ai_configs:
            config, created = ChatAIConfig.objects.update_or_create(
                static_name=config_data["static_name"],
                defaults={
                    **config_data,
                    "creator": admin_user,
                    "is_active": True,
                    "api_key": "YOUR_API_KEY_HERE",  # This should be set from env variables in production
                },
            )

            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} AI config: {config.name}"))
