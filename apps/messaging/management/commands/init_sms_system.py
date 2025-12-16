from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _

from apps.messaging.models import SystemSMSTemplate


class Command(BaseCommand):
    help = 'Initialize SMS system with default templates'

    def handle(self, *args, **options):
        # Initialize system templates
        SystemSMSTemplate.initialize_default_templates()

        # Count initialized templates
        template_count = SystemSMSTemplate.objects.count()

        self.stdout.write(
            self.style.SUCCESS(f"SMS system initialized successfully. {template_count} system templates are available.")
        )