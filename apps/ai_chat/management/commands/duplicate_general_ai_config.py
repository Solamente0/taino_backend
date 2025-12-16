# apps/ai_chat/management/commands/duplicate_general_ai_config.py
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.ai_chat.models import GeneralChatAIConfig, ChatAIConfig


class Command(BaseCommand):
    help = 'Duplicate a GeneralChatAIConfig and all its related ChatAIConfig instances'

    def add_arguments(self, parser):
        parser.add_argument(
            '--old-static-name',
            type=str,
            required=True,
            help='Static name of the source GeneralChatAIConfig to duplicate'
        )
        parser.add_argument(
            '--new-name',
            type=str,
            required=True,
            help='Name for the new GeneralChatAIConfig'
        )
        parser.add_argument(
            '--new-static-name',
            type=str,
            required=True,
            help='Static name for the new GeneralChatAIConfig'
        )
        parser.add_argument(
            '--new-description',
            type=str,
            required=True,
            help='Description for the new config'
        )
        parser.add_argument(
            '--creator-id',
            type=int,
            default=None,
            help='User ID for the creator field (uses source creator if not provided)'
        )

    def handle(self, *args, **options):
        source_static_name = options['old_static_name']
        new_name = options['new_name']
        new_static_name = options['new_static_name']
        new_description = options['new_description']
        creator_id = options.get('creator_id')

        try:
            # Get source GeneralChatAIConfig
            source_general_config = GeneralChatAIConfig.objects.get(
                static_name=source_static_name
            )
        except GeneralChatAIConfig.DoesNotExist:
            raise CommandError(
                f'GeneralChatAIConfig with static_name "{source_static_name}" does not exist'
            )

        # Check if new static_name already exists
        if GeneralChatAIConfig.objects.filter(static_name=new_static_name).exists():
            raise CommandError(
                f'GeneralChatAIConfig with static_name "{new_static_name}" already exists'
            )

        # Get creator
        if creator_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                creator = User.objects.get(id=creator_id)
            except User.DoesNotExist:
                raise CommandError(f'User with ID {creator_id} does not exist')
        else:
            creator = source_general_config.creator

        self.stdout.write(
            self.style.WARNING(
                f'Duplicating GeneralChatAIConfig: "{source_general_config.name}" '
                f'({source_general_config.static_name})'
            )
        )

        try:
            with transaction.atomic():
                # Get all related ChatAIConfigs before duplication
                source_ai_configs = ChatAIConfig.objects.filter(
                    general_config=source_general_config
                ).order_by('order', 'strength')

                self.stdout.write(
                    f'Found {source_ai_configs.count()} related ChatAIConfig(s) to duplicate'
                )

                # Duplicate GeneralChatAIConfig
                new_general_config = GeneralChatAIConfig()
                
                # Copy fields from source
                new_general_config.name = new_name
                new_general_config.static_name = new_static_name
                new_general_config.description = new_description
                new_general_config.system_instruction = source_general_config.system_instruction
                new_general_config.max_messages_per_chat = source_general_config.max_messages_per_chat
                new_general_config.max_tokens_per_chat = source_general_config.max_tokens_per_chat
                new_general_config.form_schema = source_general_config.form_schema
                new_general_config.order = source_general_config.order
                new_general_config.is_active = source_general_config.is_active
                new_general_config.admin_status = source_general_config.admin_status
                new_general_config.creator = creator
                
                # Copy icon if exists
                if source_general_config.icon:
                    new_general_config.icon = source_general_config.icon
                
                new_general_config.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created new GeneralChatAIConfig: "{new_general_config.name}" '
                        f'(PID: {new_general_config.pid})'
                    )
                )

                # Duplicate all related ChatAIConfigs
                duplicated_count = 0
                for source_ai_config in source_ai_configs:
                    new_ai_config = ChatAIConfig()
                    
                    # Set the new general_config reference
                    new_ai_config.general_config = new_general_config
                    
                    # Copy all non-unique fields
                    new_ai_config.name = source_ai_config.name
                    new_ai_config.strength = source_ai_config.strength
                    new_ai_config.description = source_ai_config.description
                    new_ai_config.model_name = source_ai_config.model_name
                    new_ai_config.base_url = source_ai_config.base_url
                    new_ai_config.api_key = source_ai_config.api_key
                    new_ai_config.system_prompt = source_ai_config.system_prompt
                    new_ai_config.default_temperature = source_ai_config.default_temperature
                    new_ai_config.default_max_tokens = source_ai_config.default_max_tokens
                    new_ai_config.rate_limit_per_minute = source_ai_config.rate_limit_per_minute
                    
                    # Pricing type
                    new_ai_config.pricing_type = source_ai_config.pricing_type
                    
                    # Message-based pricing
                    new_ai_config.cost_per_message = source_ai_config.cost_per_message
                    
                    # Hybrid pricing
                    new_ai_config.hybrid_base_cost = source_ai_config.hybrid_base_cost
                    new_ai_config.hybrid_char_per_coin = source_ai_config.hybrid_char_per_coin
                    new_ai_config.hybrid_free_chars = source_ai_config.hybrid_free_chars
                    new_ai_config.hybrid_tokens_min = source_ai_config.hybrid_tokens_min
                    new_ai_config.hybrid_tokens_max = source_ai_config.hybrid_tokens_max
                    new_ai_config.hybrid_tokens_step = source_ai_config.hybrid_tokens_step
                    new_ai_config.hybrid_cost_per_step = source_ai_config.hybrid_cost_per_step
                    
                    # Page/image pricing
                    new_ai_config.free_pages = source_ai_config.free_pages
                    new_ai_config.cost_per_page = source_ai_config.cost_per_page
                    new_ai_config.max_pages_per_request = source_ai_config.max_pages_per_request
                    
                    # Audio pricing
                    new_ai_config.free_minutes = source_ai_config.free_minutes
                    new_ai_config.cost_per_minute = source_ai_config.cost_per_minute
                    new_ai_config.max_minutes_per_request = source_ai_config.max_minutes_per_request
                    
                    # Display settings
                    new_ai_config.is_default = source_ai_config.is_default
                    new_ai_config.order = source_ai_config.order
                    new_ai_config.related_service = source_ai_config.related_service
                    
                    # Base model fields
                    new_ai_config.is_active = source_ai_config.is_active
                    new_ai_config.admin_status = source_ai_config.admin_status
                    new_ai_config.creator = creator
                    
                    # Generate new static_name based on new_static_name and strength
                    # Format: {new_static_name}_{strength}
                    new_ai_config.static_name = f"{new_static_name}_{source_ai_config.strength}"
                    
                    new_ai_config.save()
                    duplicated_count += 1
                    
                    self.stdout.write(
                        f'  ✓ Duplicated ChatAIConfig: "{new_ai_config.name}" '
                        f'({new_ai_config.get_strength_display()}) - '
                        f'static_name: {new_ai_config.static_name} - PID: {new_ai_config.pid}'
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✓ Successfully duplicated GeneralChatAIConfig and '
                        f'{duplicated_count} ChatAIConfig(s)'
                    )
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'New GeneralChatAIConfig PID: {new_general_config.pid}'
                    )
                )

        except Exception as e:
            raise CommandError(f'Error during duplication: {str(e)}')
