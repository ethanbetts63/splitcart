import os
import json
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
                        
                        # --- Load existing data if it exists ---
                        processed_filepath = os.path.join(processed_data_path, f"{company}_{store_id}_{scrape_date}.json")
                        existing_products = {}
                        if os.path.exists(processed_filepath):
                            self.stdout.write(f"        - Found existing processed file. Loading products...")
                            with open(processed_filepath, 'r', encoding='utf-8') as f:
                                try:
                                    existing_data = json.load(f)
                                    for p in existing_data.get('products', []):
                                        if p.get('product_id_store'):
                                            existing_products[p['product_id_store']] = p
                                except json.JSONDecodeError:
                                    self.stdout.write(self.style.WARNING(f"          - Could not decode existing file {processed_filepath}. It will be overwritten."))

                        # --- Process new raw files ---
                        newly_processed_products = []
                        all_source_files_this_run = []
                        final_metadata = {}

                        for category, page_files in categories.items():
                            combined_products, metadata = data_combiner(page_files)
                            if combined_products:
                                newly_processed_products.extend(combined_products)
                            all_source_files_this_run.extend([os.path.basename(f) for f in page_files])
                            if not final_metadata:
                                final_metadata = metadata

                        if not newly_processed_products:
                            self.stdout.write(self.style.WARNING("          - No new products found in raw files. Nothing to do."))
                            continue

                        # --- Merge, de-duplicate, and save ---
                        self.stdout.write(f"        - Found {len(newly_processed_products)} new products. Merging with {len(existing_products)} existing products.")
                        for new_product in newly_processed_products:
                            if new_product.get('product_id_store'):
                                existing_products[new_product['product_id_store']] = new_product
                        
                        final_product_list = list(existing_products.values())

                        simplified_metadata = {
                            "company": company,
                            "store_name": final_metadata.get('store_name', 'N/A'),
                            "store_id": store_id,
                            "state": state,
                            "scrape_date": scrape_date,
                            "product_count": len(final_product_list),
                            "source_files": all_source_files_this_run # Note: only lists sources from this run
                        }

                        processed_data_packet = {
                            "metadata": simplified_metadata,
                            "products": final_product_list
                        }

                        save_success = save_processed_data(processed_data_path, processed_data_packet)

                        if save_success:
                            self.stdout.write(f"          - Successfully saved updated processed file for store {store_id}.")
                            files_to_clean = []
                            for cat_files in categories.values():
                                files_to_clean.extend(cat_files)
                            cleanup(files_to_clean)
                        else:
                            self.stdout.write(self.style.ERROR("          - Saving processed file failed. Raw files not deleted."))

        self.stdout.write(self.style.SUCCESS("\n--- All data processing complete ---"))
