from django.core.management.base import BaseCommand
from ...views import zaplnenost

class Command(BaseCommand):
    help = 'Pridani TSbohemia zaznamu'

    def handle(self, *args, **options):
        zaplnenost()
        return
