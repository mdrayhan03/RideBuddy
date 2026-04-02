from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Creates the analytics core group required for accessing the dashboard'

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name='Analytics')
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created "Analytics" group'))
        else:
            self.stdout.write(self.style.WARNING('"Analytics" group already exists'))
