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

        # Validar por username O por email (cualquiera)
        if User.objects.filter(username=admin_username).exists():
            self.stdout.write(self.style.WARNING(
                f"Ya existe un usuario con username '{admin_username}', no se creará otro."
            ))
            return
        
        if User.objects.filter(email=admin_email).exists():
            self.stdout.write(self.style.WARNING(
                f"Ya existe un usuario con email '{admin_email}', no se creará otro."
            ))
            return

        # Crear el superusuario correcto
        User.objects.create_superuser(
            username=admin_username,
            email=admin_email,
            password=admin_password,
            is_staff=True,
            is_superuser=True,
            rol="admin"
        )

        self.stdout.write(self.style.SUCCESS(
            f"✅ Superusuario creado correctamente: {admin_email}"
        ))
