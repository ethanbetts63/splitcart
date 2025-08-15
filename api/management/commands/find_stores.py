from django.core.management.base import BaseCommand
from api.scrapers.find_aldi_stores import find_aldi_stores
from api.scrapers.find_coles_stores import find_coles_stores
from api.scrapers.find_iga_stores import find_iga_stores
from api.scrapers.find_woolworths_stores import find_woolworths_stores
from api.scrapers.find_woolworths_stores2 import find_woolworths_stores2

class Command(BaseCommand):
    help = 'Finds store locations for various supermarkets.'

    def add_arguments(self, parser):
        parser.add_argument('--aldi', action='store_true', help='Find ALDI stores.')
        parser.add_argument('--coles', action='store_true', help='Find Coles stores.')
        parser.add_argument('--iga', action='store_true', help='Find IGA stores.')
        parser.add_argument('--woolworths', action='store_true', help='Find Woolworths stores.')
        parser.add_argument('--woolworths2', action='store_true', help='Find Woolworths stores (alternative method).')

    def handle(self, *args, **options):
        any_specific_store = options['aldi'] or options['coles'] or options['iga'] or options['woolworths'] or options['woolworths2']

        if not any_specific_store:
            self.stdout.write(self.style.SUCCESS("--- Starting all store discovery processes ---"))
            find_aldi_stores()
            find_coles_stores()
            find_iga_stores()
            find_woolworths_stores()
            find_woolworths_stores2()
            self.stdout.write(self.style.SUCCESS("--- All store discovery processes complete ---"))
        else:
            if options['aldi']:
                self.stdout.write(self.style.SUCCESS("--- Starting ALDI store discovery process ---"))
                find_aldi_stores()
                self.stdout.write(self.style.SUCCESS("--- ALDI store discovery process complete ---"))
            if options['coles']:
                self.stdout.write(self.style.SUCCESS("--- Starting Coles store location scraping process ---"))
                find_coles_stores()
                self.stdout.write(self.style.SUCCESS("\n--- Coles store location scraping complete ---"))
            if options['iga']:
                self.stdout.write(self.style.SUCCESS("--- Starting IGA store location scraping process ---"))
                find_iga_stores()
                self.stdout.write(self.style.SUCCESS("\n--- IGA store location scraping complete ---"))
            if options['woolworths']:
                self.stdout.write(self.style.SUCCESS("--- Starting Woolworths store discovery process ---"))
                find_woolworths_stores()
                self.stdout.write(self.style.SUCCESS("--- Woolworths store discovery process complete ---"))
            if options['woolworths2']:
                self.stdout.write(self.style.SUCCESS("--- Starting Woolworths store discovery process (alternative method) ---"))
                find_woolworths_stores2()
                self.stdout.write(self.style.SUCCESS("--- Woolworths store discovery process (alternative method) complete ---"))
