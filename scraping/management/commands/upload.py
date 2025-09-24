from django.core.management.base import BaseCommand
from scraping.utils.command_utils.product_uploader import ProductUploader

class Command(BaseCommand):
    help = 'Uploads scraped data to the server.'

    def add_arguments(self, parser):
        parser.add_argument('--products', action='store_true', help='Upload product data.')
        # Add arguments for other data types here in the future

    def handle(self, *args, **options):
        if options['products']:
            self.stdout.write(self.style.SUCCESS("Uploading product data..."))
            uploader = ProductUploader(self)
            uploader.run()
        else:
            self.stdout.write(self.style.WARNING("Please specify which data to upload, e.g., --products"))