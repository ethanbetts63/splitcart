from django.core.management.base import BaseCommand
from scraping.utils.command_utils.product_uploader import ProductUploader
from scraping.utils.command_utils.gs1_uploader import Gs1Uploader
from scraping.utils.command_utils.store_uploader import StoreUploader
from scraping.utils.command_utils.category_links_uploader import CategoryLinksUploader
from scraping.utils.command_utils.substitutions_uploader import SubstitutionsUploader

class Command(BaseCommand):
    help = 'Uploads scraped and generated data to the server.'

    def add_arguments(self, parser):
        parser.add_argument('--products', action='store_true', help='Upload product data.')
        parser.add_argument('--gs1', action='store_true', help='Upload GS1 data.')
        parser.add_argument('--stores', action='store_true', help='Upload store data.')
        parser.add_argument('--cat-links', action='store_true', help='Upload generated category links.')
        parser.add_argument('--subs', action='store_true', help='Upload generated substitutions.')
        parser.add_argument('--dev', action='store_true', help='Use development server URL.')

    def handle(self, *args, **options):
        run_all = not any(options.values()) # Check if any flag is set
        dev = options['dev']

        if options['products'] or run_all:
            self.stdout.write(self.style.SUCCESS("Uploading product data..."))
            uploader = ProductUploader(self, dev=dev)
            uploader.run()
        
        if options['gs1'] or run_all:
            self.stdout.write(self.style.SUCCESS("Uploading GS1 data..."))
            uploader = Gs1Uploader(self, dev=dev)
            uploader.run()

        if options['stores'] or run_all:
            self.stdout.write(self.style.SUCCESS("Uploading store data..."))
            uploader = StoreUploader(self, dev=dev)
            uploader.run()

        if options['category_links']:
            self.stdout.write(self.style.SUCCESS("Uploading category links..."))
            uploader = CategoryLinksUploader(self, dev=dev)
            uploader.run()

        if options['substitutions']:
            self.stdout.write(self.style.SUCCESS("Uploading substitutions..."))
            uploader = SubstitutionsUploader(self, dev=dev)
            uploader.run()