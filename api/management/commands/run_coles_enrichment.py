from django.core.management.base import BaseCommand
from django.conf import settings
import os
from api.scrapers.barcode_scraper_coles import ColesBarcodeScraper

class Command(BaseCommand):
    help = 'Manually runs the Coles barcode enrichment process on a specific file.'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='The absolute path to a specific .jsonl file to process.')

    def handle(self, *args, **options):
        file_path = options['file']

        if not os.path.isabs(file_path):
            self.stdout.write(self.style.ERROR("Please provide an absolute path for the file."))
            return

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(f"Starting enrichment for: {file_path}")
        try:
            scraper = ColesBarcodeScraper(self, file_path)
            scraper.run()
            self.stdout.write(self.style.SUCCESS("Enrichment process completed."))
        except InterruptedError as e:
            self.stdout.write(self.style.WARNING(f"Process stopped: {e}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An unexpected error occurred: {e}"))
