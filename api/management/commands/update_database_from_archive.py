import os
from django.core.management.base import BaseCommand
from django.conf import settings

from api.utils.database_updating_utils import update_stores_from_archive_file

class Command(BaseCommand):
    help = 'Updates the database from archived JSON files.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stores',
            action='store_true',
            help='Update store information from the company_data archive.'
        )
        parser.add_argument(
            '--products',
            action='store_true',
            help='Update products and prices from the store_data archive.'
        )

    def handle(self, *args, **options):
        run_stores = options['stores']
        run_products = options['products']

        if not run_stores and not run_products:
            run_stores = True
            run_products = True

        if run_stores:
            self.update_stores()
        
        if run_products:
            self.stdout.write(self.style.WARNING("Product update from archive is not yet implemented."))

    def update_stores(self):
        self.stdout.write(self.style.SUCCESS("--- Starting Store Update from Archive ---"))
        archive_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'archive', 'company_data')

        if not os.path.exists(archive_path):
            self.stdout.write(self.style.WARNING('Company data archive directory not found.'))
            return

        for filename in os.listdir(archive_path):
            if not filename.endswith('.json'):
                continue

            file_path = os.path.join(archive_path, filename)
            self.stdout.write(f"Processing file: {filename}...")
            
            company_name, stores_processed = update_stores_from_archive_file(file_path)
            
            if company_name:
                self.stdout.write(self.style.SUCCESS(f"  Successfully processed {stores_processed} stores for {company_name}."))
            else:
                self.stderr.write(self.style.ERROR(f"  Failed to process {filename}."))

        self.stdout.write(self.style.SUCCESS("--- Store Update from Archive Complete ---"))