from django.core.management.base import BaseCommand
from django.conf import settings
import os
from scraping.scrapers.barcode_scraper_coles import ColesBarcodeScraper

class Command(BaseCommand):
    help = 'Runs the Coles barcode enrichment process on all files in the barcode_enrichment_inbox.'

    def handle(self, *args, **options):
        inbox_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', 'barcode_enrichment_inbox')

        if not os.path.exists(inbox_path):
            os.makedirs(inbox_path)
            self.stdout.write(self.style.WARNING(f"Created barcode inbox at: {inbox_path}"))
        
        def get_next_file():
            for file_name in os.listdir(inbox_path):
                if file_name.endswith('.jsonl'):
                    return os.path.join(inbox_path, file_name)
            return None

        while file_path := get_next_file():
            self.stdout.write(f"--- Starting enrichment for: {os.path.basename(file_path)} ---")
            try:
                scraper = ColesBarcodeScraper(self, file_path)
                scraper.run()
                self.stdout.write(self.style.SUCCESS(f"Enrichment process completed for {os.path.basename(file_path)}."))
            except InterruptedError as e:
                self.stderr.write(self.style.ERROR(f"A critical error occurred while processing {os.path.basename(file_path)}: {e}"))
                self.stderr.write(self.style.ERROR("Halting barcode scraping command to prevent further errors."))
                break
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"An unexpected error occurred for {os.path.basename(file_path)}: {e}"))
                self.stderr.write(self.style.ERROR("Halting barcode scraping command."))
                break
        
        self.stdout.write(self.style.SUCCESS('--- All barcode enrichment complete ---'))

