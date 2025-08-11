import os
from django.core.management.base import BaseCommand
from django.conf import settings

from api.utils.processing_utils.file_finder import file_finder
from api.utils.processing_utils.data_combiner import data_combiner
from api.utils.processing_utils.save_processed_data import save_processed_data
from api.utils.processing_utils.cleanup import cleanup

class Command(BaseCommand):
    help = 'Processes raw JSON files, combines them by store and date, and saves them to a flat processed_data directory.'

    def add_arguments(self, parser):
        parser.add_argument(
            'company_name',
            nargs='?',
            type=str,
            help='Optional: The name of the company to process (e.g., "coles"). Processes all if omitted.',
            default=None
        )

    def handle(self, *args, **options):
        company_to_process = options['company_name']
        
        api_app_path = os.path.join(settings.BASE_DIR, 'api')
        raw_data_path = os.path.join(api_app_path, 'data', 'raw_data')
        processed_data_path = os.path.join(api_app_path, 'data', 'processed_data')

        self.stdout.write(self.style.SUCCESS("--- Finding and grouping raw data files... ---"))
        scrape_plan = file_finder(raw_data_path)

        if not scrape_plan:
            self.stdout.write(self.style.WARNING("No raw data files found to process."))
            return

        companies_to_process = []
        if company_to_process:
            # Find the matching company key case-insensitively
            for key in scrape_plan.keys():
                if key.lower() == company_to_process.lower():
                    companies_to_process.append(key)
                    break
            if not companies_to_process:
                self.stdout.write(self.style.ERROR(f"No data found for company: {company_to_process}"))
                return
        else:
            self.stdout.write("No company specified. Processing all available companies...")
            companies_to_process = list(scrape_plan.keys())

        for company in companies_to_process:
            self.stdout.write(self.style.SUCCESS(f"\n--- Processing Company: {company} ---"))
            
            for state, stores in scrape_plan[company].items():
                self.stdout.write(self.style.SUCCESS(f"  --- Processing State: {state} ---"))

                for store_id, dates in stores.items():
                    self.stdout.write(self.style.SUCCESS(f"    --- Processing Store ID: {store_id} ---"))
                    
                    for scrape_date, categories in dates.items():
                        self.stdout.write(f"      Processing scrape date: {scrape_date}")
                        
                        all_products_for_store = []
                        all_source_files = []
                        final_metadata = {}

                        for category, page_files in categories.items():
                            self.stdout.write(f"        - Combining category: {category}")
                            combined_products, metadata = data_combiner(page_files)

                            if not combined_products:
                                continue
                            
                            all_products_for_store.extend(combined_products)
                            all_source_files.extend([os.path.basename(f) for f in page_files])
                            
                            # Capture metadata from the first category processed
                            if not final_metadata:
                                final_metadata = metadata

                        if not all_products_for_store:
                            self.stdout.write(self.style.WARNING("          - No products found for this store. Skipping."))
                            continue

                        # --- Assemble the simplified, final data packet ---
                        
                        # 1. Create the simplified metadata
                        simplified_metadata = {
                            "company": company,
                            "store_name": final_metadata.get('store_name', 'N/A'), # Assumes store_name is in metadata
                            "store_id": store_id,
                            "state": state,
                            "scrape_date": scrape_date,
                            "product_count": len(all_products_for_store),
                            "source_files": all_source_files
                        }

                        # 2. Create the final packet
                        processed_data_packet = {
                            "metadata": simplified_metadata,
                            "products": all_products_for_store
                        }

                        # 3. Save the single file for the store for that date
                        processed_data_success = save_processed_data(
                            processed_data_path,
                            processed_data_packet
                        )

                        if processed_data_success:
                            self.stdout.write(f"          - Successfully created processed file for store {store_id} on {scrape_date}.")
                            # We need to collect all file paths to be cleaned up
                            files_to_clean = []
                            for cat_files in categories.values():
                                files_to_clean.extend(cat_files)
                            cleanup(files_to_clean)
                        else:
                            self.stdout.write(self.style.ERROR("          - Archiving failed. Raw files not deleted."))

        self.stdout.write(self.style.SUCCESS("\n--- All data processing complete ---"))