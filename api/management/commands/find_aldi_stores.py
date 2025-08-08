
from django.core.management.base import BaseCommand
from api.scrapers.find_aldi_stores import find_aldi_stores

class Command(BaseCommand):
    help = 'Launches the scraper to find all ALDI stores in Australia.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting ALDI store discovery process ---"))
        find_aldi_stores()
        self.stdout.write(self.style.SUCCESS("--- ALDI store discovery process complete ---"))
