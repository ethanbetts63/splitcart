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

    def handle(self, *args, **options):
        run_all = not any(options[company] for company in ['woolworths', 'coles', 'aldi', 'iga'])

        if options['woolworths'] or run_all:
            self.stdout.write(self.style.SUCCESS('Running Woolworths scraper...'))
            run_woolworths_scraper()

        if options['coles'] or run_all:
            self.stdout.write(self.style.SUCCESS('Running Coles scraper...'))
            run_coles_scraper()

        if options['aldi'] or run_all:
            self.stdout.write(self.style.SUCCESS('Running Aldi scraper...'))
            run_aldi_scraper()

        if options['iga'] or run_all:
            self.stdout.write(self.style.SUCCESS('Running IGA scraper...'))
            run_iga_scraper()

        self.stdout.write(self.style.SUCCESS('Scraping complete.'))
