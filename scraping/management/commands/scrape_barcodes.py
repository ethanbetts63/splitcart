import os
from django.conf import settings
from django.core.management.base import BaseCommand
from scraping.scrapers.barcode_scraper_coles import ColesBarcodeScraper

class Command(BaseCommand):
    help = 'Scans the barcode scraper inbox and processes files.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Starting Barcode Scraper Worker ---'))
        
        barcode_inbox_path = os.path.join(settings.BASE_DIR, 'scraping', 'data', 'inboxes', 'barcode_scraper_inbox')
        product_outbox_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'outboxes', 'product_outbox')

        if not os.path.exists(barcode_inbox_path):
            self.stdout.write(self.style.WARNING('Barcode scraper inbox does not exist. Nothing to do.'))
            return

        files_to_process = [f for f in os.listdir(barcode_inbox_path) if f.endswith('.jsonl')]

        if not files_to_process:
            self.stdout.write(self.style.SUCCESS('No files found in barcode scraper inbox.'))
            return

        self.stdout.write(f"Found {len(files_to_process)} files to process.")

        for file_name in files_to_process:
            source_file_path = os.path.join(barcode_inbox_path, file_name)
            self.stdout.write(self.style.HTTP_INFO(f"--- Processing file: {file_name} ---"))

            try:
                # Currently, we only have a barcode scraper for Coles.
                # This logic can be expanded if other scrapers need a barcode enrichment step.
                if 'coles' in file_name.lower():
                    scraper = ColesBarcodeScraper(command=self, source_file_path=source_file_path)
                    scraper.run()

                    # After the scraper.run() is successful, the original source file is deleted by the scraper.
                    # The enriched file is now in the temp_outbox. We need to move it to the final product_outbox.
                    # This part of the logic needs to be coordinated with the scraper's output.
                    
                    # For now, let's assume the scraper's `commit` places it in a known location.
                    # The current `ColesBarcodeScraper` deletes the source and commits its new file.
                    # We need to ensure that commit goes to the right place.
                    
                    # Let's re-read barcode_scraper_coles.py to check its output logic.
                    # It seems the barcode scraper will create a new file and commit it.
                    # We need to adjust that in Part 3. For now, this structure is a good start.
                    self.stdout.write(self.style.SUCCESS(f"Successfully processed {file_name}."))

                else:
                    self.stdout.write(self.style.WARNING(f"No barcode scraper available for {file_name}. Moving to final outbox as-is."))
                    # If no barcode scraper, move the file directly to the final outbox
                    final_destination = os.path.join(product_outbox_path, file_name)
                    os.rename(source_file_path, final_destination)


            except Exception as e:
                self.stderr.write(self.style.ERROR(f"An error occurred while processing {file_name}: {e}"))
                # Decide on an error strategy: move to a 'failed' folder, or leave it?
                # For now, we'll leave it in the inbox to be retried.
                continue
        
        self.stdout.write(self.style.SUCCESS('--- Barcode Scraper Worker Finished ---'))
