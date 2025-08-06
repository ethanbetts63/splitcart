from django.core.management.base import BaseCommand
from api.scrapers.find_iga_stores import fetch_all_stores_thorough

class Command(BaseCommand):
    help = 'Launches the thorough scraper to find all IGA store locations.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting IGA store location scraping process ---"))

        fetch_all_stores_thorough()

        self.stdout.write(self.style.SUCCESS("\n--- IGA store location scraping complete ---"))
