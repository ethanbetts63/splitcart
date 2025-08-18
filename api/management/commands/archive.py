from django.core.management.base import BaseCommand
from api.utils.archiving_utils.build_store_archive import build_store_archive
from api.utils.archiving_utils.build_product_archive import build_product_archive

class Command(BaseCommand):
    help = 'Builds store and product archive files.'

    def add_arguments(self, parser):
        parser.add_argument('--stores', action='store_true', help='Build the store archives (from company data).')
        parser.add_argument('--products', action='store_true', help='Build the product archives (for each store).')

    def handle(self, *args, **options):
        run_stores = options['stores']
        run_products = options['products']

        # If no arguments are given, run both
        if not run_stores and not run_products:
            run_stores = True
            run_products = True

        if run_stores:
            build_store_archive(self)
        
        if run_products:
            build_product_archive(self)

        self.stdout.write(self.style.SUCCESS('Archiving process complete.'))
