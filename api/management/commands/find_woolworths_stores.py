
from django.core.management.base import BaseCommand
from api.scrapers.find_woolworths_stores import find_woolworths_stores

class Command(BaseCommand):
    help = 'Launches the scraper to find all Woolworths stores in Australia by iterating through postcodes.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Woolworths store discovery process ---"))
        find_woolworths_stores()
        self.stdout.write(self.style.SUCCESS("--- Woolworths store discovery process complete ---"))
