import os
from django.core.management.base import BaseCommand
from django.conf import settings

from api.utils.processing_utils.file_finder import file_finder
from api.utils.processing_utils.data_combiner import data_combiner
from api.utils.processing_utils.archive_manager import archive_manager

class Command(BaseCommand):
    help = 'Processes raw JSON files, combines them by category, and saves them to a structured processed_data directory.'

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
            found = False
            for company in scrape_plan.keys():
                if company.lower() == company_to_process.lower():
                    companies_to_process.append(company)
                    found = True
                    break
            if not found:
                self.stdout.write(self.style.ERROR(f"No data found for company: {company_to_process}"))
                return
        else:
            self.stdout.write("No company specified. Processing all available companies...")
            companies_to_process = list(scrape_plan.keys())

        for company in companies_to_process:
            if company not in scrape_plan:
                continue
            
            self.stdout.write(self.style.SUCCESS(f"\n--- Processing Company: {company} ---"))
            
            for state, stores in scrape_plan[company].items():
                self.stdout.write(self.style.SUCCESS(f"  --- Processing State: {state} ---"))

                for store, dates in stores.items():
                    self.stdout.write(self.style.SUCCESS(f"    --- Processing Store: {store} ---"))
                    
                    all_scrape_dates = sorted(dates.keys(), reverse=True)

                    for scrape_date in all_scrape_dates:
                        self.stdout.write(f"      Processing scrape date: {scrape_date}")
                        categories = dates[scrape_date]

                        for category, page_files in categories.items():
                            self.stdout.write(f"        - Category: {category}")

                            combined_products = data_combiner(page_files)

                            if not combined_products:
                                self.stdout.write(self.style.WARNING("          - No products found after combining. Skipping."))
                                continue
                            
                            self.stdout.write(f"          - Combined {len(combined_products)} products from {len(page_files)} page files.")

                            # Call the updated archive manager with the new arguments
                            archive_manager(
                                processed_data_path, 
                                company, 
                                state,
                                store, 
                                scrape_date, 
                                category, 
                                combined_products, 
                                page_files
                            )

        self.stdout.write(self.style.WARNING("\nCleanup step skipped. Raw data files have not been deleted."))
        self.stdout.write(self.style.SUCCESS("\n--- All data processing complete ---"))
