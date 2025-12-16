from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a superuser with a phone number"

    def handle(self, *args, **options):
        User = get_user_model()
        vekalat_id = input("Enter Tainoekalat id: ")
        phone_number = input("Enter phone number: ")
        password = input("Enter password: ")

        User.objects.create_superuser(
            vekalat_id=vekalat_id, password=password, phone_number=phone_number, is_staff=True, is_superuser=True
        )
        self.stdout.write(self.style.SUCCESS("Superuser created successfully"))
