from django.core.management.base import BaseCommand
from users.models import User
from users.models import Role

class Command(BaseCommand):
    help = 'Creates a superuser with all required fields'

    def handle(self, *args, **options):
        try:
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin123',
                    first_name='Admin',
                    last_name='User',
                    role=Role.ADMIN,  # Use enum value from User model
                    is_mfa_enabled=False,
                    phone_number='+911234567890'
                )
                self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
            else:
                self.stdout.write(self.style.WARNING('Superuser already exists'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {str(e)}'))