from django.conf import settings
from django.core.management.base import BaseCommand
from api.utils.management_utils.run_woolworths_scraper import run_woolworths_scraper
from api.utils.management_utils.run_coles_scraper import run_coles_scraper
from api.utils.management_utils.run_aldi_scraper import run_aldi_scraper
from api.utils.management_utils.run_iga_scraper import run_iga_scraper

class Command(BaseCommand):
    help = 'Runs the scrapers for the specified companies.'

    def add_arguments(self, parser):
        parser.add_argument('--woolworths', action='store_true', help='Run the Woolworths scraper.')
        parser.add_argument('--coles', action='store_true', help='Run the Coles scraper.')
        parser.add_argument('--aldi', action='store_true', help='Run the Aldi scraper.')
        parser.add_argument('--iga', action='store_true', help='Run the IGA scraper.')
        parser.add_argument('--batch-size', type=int, default=100, help='The number of stores to scrape per run.')

    def handle(self, *args, **options):
        run_all = not any(options[company] for company in ['woolworths', 'coles', 'aldi', 'iga'])
        batch_size = options['batch_size']
        if options['woolworths'] or run_all:
            run_woolworths_scraper(self, batch_size)

        if options['coles'] or run_all:
            run_coles_scraper(self, batch_size)

        if options['aldi'] or run_all:
            run_aldi_scraper(self, batch_size)

        if options['iga'] or run_all:
            run_iga_scraper(self, batch_size)

        self.stdout.write(self.style.SUCCESS('Scraping complete.'))
