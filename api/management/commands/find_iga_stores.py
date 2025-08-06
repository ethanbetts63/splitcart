from django.core.management.base import BaseCommand
from api.scrapers.find_iga_stores import find_iga_stores

class Command(BaseCommand):
    help = 'Launches the thorough scraper to find all IGA store locations.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting IGA store location scraping process ---"))

        find_iga_stores()

        self.stdout.write(self.style.SUCCESS("\n--- IGA store location scraping complete ---"))
