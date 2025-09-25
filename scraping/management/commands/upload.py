from django.core.management.base import BaseCommand
from scraping.utils.command_utils.product_uploader import ProductUploader
from scraping.utils.command_utils.gs1_uploader import Gs1Uploader

from scraping.utils.command_utils.gs1_uploader import Gs1Uploader

class Command(BaseCommand):
    help = 'Uploads scraped data to the server.'

    def add_arguments(self, parser):
        parser.add_argument('--products', action='store_true', help='Upload product data.')
        parser.add_argument('--gs1', action='store_true', help='Upload GS1 data.')
        # Add arguments for other data types here in the future

    def handle(self, *args, **options):
        product = options['products']
        gs1 = options['gs1']

        # If no specific upload is requested, run all
        if not product and not gs1:
            product = True
            gs1 = True

        if product:
            self.stdout.write(self.style.SUCCESS("Uploading product data..."))
            uploader = ProductUploader(self)
            uploader.run()
        
        if gs1:
            self.stdout.write(self.style.SUCCESS("Uploading GS1 data..."))
            uploader = Gs1Uploader(self)
            uploader.run()