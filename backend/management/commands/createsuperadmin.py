from django.core.management.base import BaseCommand
from backend.models import Account
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = 'Creates a superadmin account'

    def handle(self, *args, **options):
        email = input("Enter superadmin email: ")
        password = input("Enter superadmin password: ")
        if not Account.objects.filter(email=email).exists():
            Account.objects.create(
                email=email,
                password=make_password(password),
                role='superadmin',
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('Superadmin created successfully'))
        else:
            self.stdout.write(self.style.ERROR('Email already exists'))