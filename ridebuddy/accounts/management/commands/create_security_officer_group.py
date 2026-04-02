from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help = 'Creates the Security Officer group and binds all "view-only" table permissions to it'

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name='Security Officer')
        
        system_apps = ['accounts', 'bookings', 'reviews', 'rides', 'analytics']
        
        # Fetching all 'view' permissions only for the custom models in this system, excluding OTPs
        view_permissions = Permission.objects.filter(
            codename__startswith='view_',
            content_type__app_label__in=system_apps
        ).exclude(content_type__model='otp')
        
        # Attach permissions to the group
        group.permissions.set(view_permissions)
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created "Security Officer" group with {view_permissions.count()} view permissions.')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'"Security Officer" group already exists. Refreshed with {view_permissions.count()} view permissions.')
            )
