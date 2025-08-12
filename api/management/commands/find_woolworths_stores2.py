from django.core.management.base import BaseCommand
from api.scrapers.find_woolworths_stores2 import find_woolworths_stores2

class Command(BaseCommand):
    help = 'Finds all Woolworths stores using the postcode-based API.'

    def handle(self, *args, **options):
        find_woolworths_stores2()
