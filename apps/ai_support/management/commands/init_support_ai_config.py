from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.ai_support.models import SupportAIConfig

User = get_user_model()


class Command(BaseCommand):
    help = "Initialize AI support configuration"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--api-key',
            type=str,
            help='OpenRouter API key',
            default=''
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Model name',
            default='meta-llama/llama-3.1-8b-instruct:free'
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing configurations'
        )
    
    def handle(self, *args, **options):
        api_key = options['api_key']
        model = options['model']
        reset = options['reset']
        
        if reset:
            deleted_count = SupportAIConfig.objects.all().delete()[0]
            self.stdout.write(
                self.style.WARNING(f"Deleted {deleted_count} existing configurations")
            )
        
        # Check if default config exists
        existing_config = SupportAIConfig.objects.filter(is_default=True).first()
        
        if existing_config and not reset:
            self.stdout.write(
                self.style.WARNING(
                    f"Default configuration already exists: {existing_config.name}"
                )
            )
            self.stdout.write("Use --reset to delete and recreate")
            return
        
        # Get or create admin user
        admin_user = User.objects.filter(is_admin=True).first()
        if not admin_user:
            self.stdout.write(
                self.style.ERROR("No admin user found. Creating configurations without creator.")
            )
        
        # Default system prompt in Persian
        default_system_prompt = """شما یک دستیار پشتیبانی حرفه‌ای هستید که به فارسی پاسخ می‌دهید.
وظیفه شما کمک به کاربران در حل مشکلات و پاسخ به سوالات آنهاست.

راهنماها:
- همیشه مودب، صبور و دقیق باشید
- اگر نمی‌دانید، صادقانه بگویید که این موضوع را به تیم فنی ارجاع می‌دهید
- پاسخ‌های خود را واضح و مختصر بیان کنید
- در صورت لزوم، مراحل حل مشکل را گام به گام توضیح دهید
- از استفاده از اصطلاحات فنی پیچیده خودداری کنید مگر اینکه ضروری باشد

اطلاعات مفید:
- سایت ما: taino.ir
- ساعات پشتیبانی: 9 صبح تا 6 بعدازظهر
- برای مسائل فوری، از تیکت پشتیبانی استفاده کنید"""

        # Create default configuration
        config = SupportAIConfig.objects.create(
            name="پیکربندی پیش‌فرض پشتیبانی",
            api_key=api_key or "YOUR_OPENROUTER_API_KEY_HERE",
            base_url="https://openrouter.ai/api/v1",
            model_name=model,
            system_prompt=default_system_prompt,
            temperature=0.7,
            max_tokens=500,
            ctainoersation_history_limit=10,
            response_delay_seconds=1,
            fallback_message="متاسفانه در حال حاضر قادر به پاسخگویی نیستم. لطفاً بعداً دوباره تلاش کنید یا با تیم پشتیبانی تماس بگیرید.",
            is_default=True,
            is_active=True,
            creator=admin_user
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Successfully created default AI configuration: {config.name}"
            )
        )
        
        if not api_key:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  IMPORTANT: You need to set a valid OpenRouter API key!"
                )
            )
            self.stdout.write("1. Go to: https://openrouter.ai/")
            self.stdout.write("2. Sign up and get your API key")
            self.stdout.write("3. Update the configuration in Django admin")
            self.stdout.write(f"   or run: python manage.py init_support_ai_config --api-key YOUR_KEY\n")
        
        self.stdout.write("\nConfiguration details:")
        self.stdout.write(f"  - Model: {config.model_name}")
        self.stdout.write(f"  - Temperature: {config.temperature}")
        self.stdout.write(f"  - Max tokens: {config.max_tokens}")
        self.stdout.write(f"  - History limit: {config.ctainoersation_history_limit}")
        self.stdout.write(f"  - Response delay: {config.response_delay_seconds}s")
        
        self.stdout.write(
            self.style.SUCCESS(
                "\n✓ Setup complete! You can now use the AI support chat system."
            )
        )
