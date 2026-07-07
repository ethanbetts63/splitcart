from django.core.management.base import BaseCommand
from scraping.utils.command_utils.product_uploader import ProductUploader
from scraping.utils.command_utils.category_links_uploader import CategoryLinksUploader
from scraping.utils.command_utils.substitutions_uploader import SubstitutionsUploader

class Command(BaseCommand):
    help = 'Uploads scraped and generated data to the server.'

    def add_arguments(self, parser):
        parser.add_argument('--products', action='store_true', help='Upload product data.')
        parser.add_argument('--cat-links', action='store_true', help='Upload generated category links.')
        parser.add_argument('--subs', action='store_true', help='Upload generated substitutions.')
        parser.add_argument('--dev', action='store_true', help='Use development server URL.')

    def handle(self, *args, **options):
        dev = options['dev']

        if options['products']:
            self.stdout.write(self.style.SUCCESS("Uploading product data..."))
            uploader = ProductUploader(self, dev=dev)
            uploader.run()

        if options['cat_links']:
            self.stdout.write(self.style.SUCCESS("Uploading category links..."))
            uploader = CategoryLinksUploader(self, dev=dev)
            uploader.run()

        if options['subs']:
            self.stdout.write(self.style.SUCCESS("Uploading substitutions..."))
            uploader = SubstitutionsUploader(self, dev=dev)
            uploader.run()
