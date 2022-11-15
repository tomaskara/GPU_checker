from django.core.management.base import BaseCommand
from ...scrapers import alza, czc, softcomp

class Command(BaseCommand):
    help = 'Pridani Alza,CZC,Softcomp zaznamu'

    def handle(self, *args, **options):
        alza()
        czc()
        softcomp()
        print("Alza,CZC,Softcomp zaznamy pridany")
        return
