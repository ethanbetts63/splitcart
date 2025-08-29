from django.core.management.base import BaseCommand
from api.scrapers.enrich_coles_barcodes import fetch_and_update_coles_barcodes

class Command(BaseCommand):
    """
    A Django management command to find and update barcodes for Coles products.
    """
    help = 'Scrapes individual Coles product pages to find and save the barcode (GTIN) for products that are missing it.'

    def handle(self, *args, **options):
        """
        The main entry point for the command.
        """
        fetch_and_update_coles_barcodes(self)
