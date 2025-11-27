import os
from django.conf import settings
from django.core.management.base import BaseCommand
from scraping.scrapers.barcode_scraper_coles import ColesBarcodeScraper

class Command(BaseCommand):
    help = 'Scans the barcode scraper inbox and processes files.'

    def add_arguments(self, parser):
        parser.add_argument('--dev', action='store_true', help='Use dev server for API calls.')
        parser.add_argument('--coles-v2', action='store_true', help='Use the refactored Coles barcode scraper workflow.')

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

        if options['coles_v2']:
            # --- V2 Workflow ---
            from scraping.scrapers.barcode_scraper_coles_v2 import ColesBarcodeScraperV2
            from scraping.utils.coles_session_manager import ColesSessionManager
            
            self.stdout.write(self.style.SUCCESS("--- Running in V2 (session-persistent) mode ---"))
            session_manager = ColesSessionManager(self)

            for file_name in files_to_process:
                source_file_path = os.path.join(barcode_inbox_path, file_name)
                
                if 'coles' not in file_name.lower():
                    self.stdout.write(self.style.WARNING(f"No barcode scraper available for {file_name}. Moving to final outbox as-is."))
                    final_destination = os.path.join(product_outbox_path, file_name)
                    try:
                        os.rename(source_file_path, final_destination)
                    except FileNotFoundError:
                        self.stdout.write(self.style.WARNING(f"File {file_name} was not found, it may have been moved by another process."))
                    continue

                self.stdout.write(self.style.HTTP_INFO(f"--- Processing file: {file_name} ---"))
                try:
                    scraper = ColesBarcodeScraperV2(
                        command=self, 
                        source_file_path=source_file_path, 
                        session_manager=session_manager, 
                        dev=options['dev']
                    )
                    scraper.run()
                    self.stdout.write(self.style.SUCCESS(f"Successfully processed {file_name}."))

                except InterruptedError:
                    self.stdout.write(self.style.ERROR(f"Session blocked by CAPTCHA while processing {file_name}."))
                    self.stdout.write(self.style.WARNING(f"File {file_name} will be left in the inbox to be retried. A new session will be created."))
                    session_manager.close()
                    session_manager = ColesSessionManager(self)
                    continue
                
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"An unexpected error occurred while processing {file_name}: {e}"))
                    self.stdout.write(self.style.WARNING(f"File {file_name} will be left in the inbox to be retried."))
                    continue
            
            session_manager.close()

        else:
            # --- Original Workflow ---
            for file_name in files_to_process:
                source_file_path = os.path.join(barcode_inbox_path, file_name)
                self.stdout.write(self.style.HTTP_INFO(f"--- Processing file: {file_name} ---"))

                try:
                    if 'coles' in file_name.lower():
                        scraper = ColesBarcodeScraper(command=self, source_file_path=source_file_path, dev=options['dev'])
                        scraper.run()
                        self.stdout.write(self.style.SUCCESS(f"Successfully processed {file_name}."))
                    else:
                        self.stdout.write(self.style.WARNING(f"No barcode scraper available for {file_name}. Moving to final outbox as-is."))
                        final_destination = os.path.join(product_outbox_path, file_name)
                        os.rename(source_file_path, final_destination)

                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"An error occurred while processing {file_name}: {e}"))
                    continue
        
        self.stdout.write(self.style.SUCCESS('--- Barcode Scraper Worker Finished ---'))
