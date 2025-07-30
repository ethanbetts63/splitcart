import os
from django.core.management.base import BaseCommand
from django.conf import settings

# Import our new, testable utility functions
from api.utils.file_finder import file_finder
from api.utils.data_combiner import data_combiner
from api.utils.archive_manager import archive_manager
# We are deliberately NOT importing the cleanup utility for now.

class Command(BaseCommand):
    help = 'Processes raw JSON files, combines them by category, and saves them to a structured processed_data directory.'

    def add_arguments(self, parser):
        parser.add_argument(
            'store_name',
            nargs='?',
            type=str,
            help='Optional: The name of the store to process (e.g., "coles"). Processes all if omitted.',
            default=None
        )

    def handle(self, *args, **options):
        store_to_process = options['store_name']
        
        api_app_path = os.path.join(settings.BASE_DIR, 'api')
        raw_data_path = os.path.join(api_app_path, 'data', 'raw_data')
        processed_data_path = os.path.join(api_app_path, 'data', 'processed_data')

        # --- Station 1: The Organizer ---
        # Get a structured work plan of all the raw files.
        self.stdout.write(self.style.SUCCESS("--- Finding and grouping raw data files... ---"))
        scrape_plan = file_finder(raw_data_path)

        if not scrape_plan:
            self.stdout.write(self.style.WARNING("No raw data files found to process."))
            return

        # --- Determine which stores to process based on the argument ---
        stores_to_process = []
        if store_to_process:
            if store_to_process.lower() in scrape_plan:
                stores_to_process.append(store_to_process.lower())
            else:
                self.stdout.write(self.style.ERROR(f"No data found for store: {store_to_process}"))
                return
        else:
            self.stdout.write("No store specified. Processing all available stores...")
            stores_to_process = list(scrape_plan.keys())

        # --- Loop through the work plan (Store -> Scrape Run -> Category) ---
        for store in stores_to_process:
            if store not in scrape_plan:
                continue
            
            self.stdout.write(self.style.SUCCESS(f"\n--- Processing Store: {store} ---"))
            for scrape_run_id, categories in scrape_plan[store].items():
                self.stdout.write(f"  Processing scrape run: {scrape_run_id}")
                
                # We will process the date from the scrape_run_id
                scrape_date = scrape_run_id.split('T')[0]

                for category, page_files in categories.items():
                    self.stdout.write(f"    - Category: {category}")

                    # --- Station 2: The Assembler ---
                    # Combine all products from the page files into one list.
                    combined_products = data_combiner(page_files)

                    if not combined_products:
                        self.stdout.write(self.style.WARNING("      - No products found after combining. Skipping."))
                        continue
                    
                    self.stdout.write(f"      - Combined {len(combined_products)} products from {len(page_files)} page files.")

                    # --- Station 3: The Archivist ---
                    # Save the combined list to the processed_data directory.
                    archive_manager(processed_data_path, store, scrape_date, category, combined_products)

        # NOTE: We are intentionally not calling the cleanup utility yet.
        # The raw files will be left in place for now.
        self.stdout.write(self.style.WARNING("\nCleanup step skipped. Raw data files have not been deleted."))
        self.stdout.write(self.style.SUCCESS("\n--- All data processing complete ---"))
