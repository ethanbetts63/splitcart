
from django.core.management.base import BaseCommand
from api.scrapers.barcode_scraper_coles import ColesBarcodeScraper
import os

class Command(BaseCommand):
    help = 'Enriches a Coles product .jsonl file with barcode information.'

    def add_arguments(self, parser):
        parser.add_argument('source_file_path', type=str, help='The absolute path to the .jsonl file to enrich.')

    def handle(self, *args, **options):
        source_file_path = options['source_file_path']

        if not os.path.exists(source_file_path):
            self.stderr.write(self.style.ERROR(f"Source file not found: {source_file_path}"))
            return

        if not source_file_path.endswith('.jsonl'):
            self.stderr.write(self.style.ERROR("Source file must be a .jsonl file."))
            return

        self.stdout.write(self.style.SUCCESS(f'Starting barcode enrichment for: {os.path.basename(source_file_path)}'))

        try:
            scraper = ColesBarcodeScraper(command=self, source_file_path=source_file_path)
            scraper.run()
            self.stdout.write(self.style.SUCCESS('Enrichment process finished.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'An unexpected error occurred: {e}'))
