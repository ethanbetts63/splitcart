from django.core.management.base import BaseCommand
from api.scrapers.enrich_coles_barcodes import enrich_coles_inbox_files

class Command(BaseCommand):
    """
    A Django management command to enrich Coles .jsonl files in the product inbox.
    """
    help = 'Enriches Coles .jsonl files with barcodes by checking the DB and scraping the web.'

    def handle(self, *args, **options):
        """
        The main entry point for the command.
        """
        enrich_coles_inbox_files(self)
