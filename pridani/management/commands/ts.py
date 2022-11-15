from django.core.management.base import BaseCommand
from ...scrapers import tsbohemia_api

class Command(BaseCommand):
    help = 'Pridani TSbohemia zaznamu'

    def handle(self, *args, **options):
        tsbohemia_api()
        print("TS zaznamy pridany")
        return
