from django.core.management.base import BaseCommand
from api.scrapers.find_coles_stores import fetch_coles_stores_graphql

class Command(BaseCommand):
    help = 'Launches the GraphQL scraper to find all Coles store locations.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Coles store location scraping process ---"))
        
        fetch_coles_stores_graphql()
        
        self.stdout.write(self.style.SUCCESS("\n--- Coles store location scraping complete ---"))
