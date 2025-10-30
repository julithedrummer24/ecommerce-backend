from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = "Crea un superusuario por defecto si no existe"

    def handle(self, *args, **options):
        admin_email = getattr(settings, "ADMIN_EMAIL", "admin@ecommerce.com")
        admin_username = getattr(settings, "ADMIN_USERNAME", "admin")
        admin_password = getattr(settings, "ADMIN_PASSWORD", "admin123")

        if not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                is_staff=True,
                is_superuser=True,
                rol="admin"
            )
            self.stdout.write(self.style.SUCCESS(f"✅ Superusuario creado: {admin_email} / {admin_password}"))
        else:
            self.stdout.write(self.style.WARNING(f"ℹ️ El superusuario {admin_email} ya existe."))
