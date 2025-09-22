from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from companies.models.company import Company
from companies.models.store import Store
from api.scrapers.product_scraper_woolworths import ProductScraperWoolworths
from api.scrapers.product_scraper_coles import ColesScraper as ProductScraperColes
from api.scrapers.product_scraper_aldi import ProductScraperAldi
from api.scrapers.product_scraper_iga import IgaScraper as ProductScraperIga
from api.utils.scraper_utils.get_woolworths_categories import get_woolworths_categories
from api.utils.scraper_utils.get_coles_categories import get_coles_categories
from api.scrapers.gs1_company_scraper import Gs1CompanyScraper
import os

class Command(BaseCommand):
    help = 'Runs the scrapers for the specified companies.'

    def add_arguments(self, parser):
        parser.add_argument('--woolworths', action='store_true', help='Run the Woolworths scraper.')
        parser.add_argument('--coles', action='store_true', help='Run the Coles scraper.')
        parser.add_argument('--aldi', action='store_true', help='Run the Aldi scraper.')
        parser.add_argument('--iga', action='store_true', help='Run the IGA scraper.')
        parser.add_argument('--gs1', action='store_true', help='Run the GS1 company prefix scraper test.')
        parser.add_argument('--batch-size', type=int, default=100, help='The number of stores to scrape per run.')
        parser.add_argument('--store-pk', type=int, help='Scrape a specific store by its database primary key.')

    def handle(self, *args, **options):
        # Clean up a previous stop file at the beginning of a new run.
        stop_file = 'stop.txt'
        if os.path.exists(stop_file):
            os.remove(stop_file)
            self.stdout.write(self.style.SUCCESS(f"Removed previous stop file: {stop_file}"))

        store_pk = options.get('store_pk')

        if store_pk:
            self._scrape_single_store(store_pk)
        else:
            self._scrape_batch(options)

        if options['gs1']:
            self.stdout.write(self.style.SUCCESS('Running GS1 scraper...'))
            scraper = Gs1CompanyScraper(self)
            scraper.run()

        self.stdout.write(self.style.SUCCESS('Scraping complete.'))

    def _scrape_single_store(self, store_pk):
        try:
            store = Store.objects.select_related('company').get(pk=store_pk)
            company_name = store.company.name
            self.stdout.write(self.style.SUCCESS(f"Scraping specific store: {store.store_name} ({company_name}) [PK: {store_pk}]"))

            scraper = None
            if company_name == "Woolworths":
                categories = get_woolworths_categories(self)
                if not categories:
                    self.stdout.write(self.style.ERROR('Could not fetch Woolworths categories. Aborting scrape.'))
                    return
                scraper = ProductScraperWoolworths(
                    command=self, company=store.company.name, store_id=store.store_id,
                    store_name=store.store_name, state=store.state, categories_to_fetch=categories
                )
            elif company_name == "Coles":
                categories = get_coles_categories()
                if not categories:
                    self.stdout.write(self.style.ERROR('Could not fetch Coles categories. Aborting scrape.'))
                    return
                scraper = ProductScraperColes(
                    command=self, company=store.company.name, store_id=store.store_id,
                    store_name=store.store_name, state=store.state, categories_to_fetch=categories
                )
            elif company_name == "Aldi":
                scraper = ProductScraperAldi(
                    command=self, company=store.company.name, store_id=store.store_id,
                    store_name=store.store_name, state=store.state
                )
            elif company_name == "Iga":
                scraper = ProductScraperIga(
                    command=self, company=store.company.name, store_id=store.store_id,
                    retailer_store_id=store.retailer_store_id, store_name=store.store_name, state=store.state
                )
            else:
                self.stdout.write(self.style.ERROR(f"No scraper implemented for company '{company_name}'."))
                return

            if scraper:
                scraper.run()
                store.last_scraped = timezone.now()
                store.save()

        except Store.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Store with PK {store_pk} not found."))

    def _scrape_batch(self, options):
        run_all = not any(options[company] for company in ['woolworths', 'coles', 'aldi', 'iga', 'gs1'])
        batch_size = options['batch_size']

        if options['woolworths'] or run_all:
            self.stdout.write(self.style.SUCCESS('Running Woolworths scraper...'))
            try:
                woolworths_company = Company.objects.get(name="Woolworths")
                stores = Store.objects.filter(company=woolworths_company, is_active=True, division__name__iexact='supermarkets')
                stores_to_scrape = stores.order_by('last_scraped')[:batch_size]
                if not stores_to_scrape:
                    self.stdout.write(self.style.WARNING('No active Woolworths stores found to scrape.'))
                else:
                    categories = get_woolworths_categories(self)
                    if not categories:
                        self.stdout.write(self.style.ERROR('Could not fetch Woolworths categories. Aborting Woolworths scrape.'))
                    else:
                        for store in stores_to_scrape:
                            if os.path.exists('stop.txt'):
                                self.stdout.write(self.style.WARNING("Stop signal detected. Halting before next store."))
                                break
                            scraper = ProductScraperWoolworths(
                                command=self, company=woolworths_company.name, store_id=store.store_id,
                                store_name=store.store_name, state=store.state, categories_to_fetch=categories
                            )
                            scraper.run()
                            store.last_scraped = timezone.now()
                            store.save()
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR('Company "Woolworths" not found.'))

        if options['coles'] or run_all:
            self.stdout.write(self.style.SUCCESS('Running Coles scraper...'))
            try:
                coles_company = Company.objects.get(name="Coles")
                stores = Store.objects.filter(company=coles_company, is_active=True)
                stores_to_scrape = stores.order_by('last_scraped')[:batch_size]
                if not stores_to_scrape:
                    self.stdout.write(self.style.WARNING('No active Coles stores found to scrape.'))
                else:
                    categories = get_coles_categories()
                    if not categories:
                        self.stdout.write(self.style.ERROR('Could not fetch Coles categories. Aborting Coles scrape.'))
                    else:
                        for store in stores_to_scrape:
                            if os.path.exists('stop.txt'):
                                self.stdout.write(self.style.WARNING("Stop signal detected. Halting before next store."))
                                break
                            scraper = ProductScraperColes(
                                command=self, company=coles_company.name, store_id=store.store_id,
                                store_name=store.store_name, state=store.state, categories_to_fetch=categories
                            )
                            scraper.run()
                            store.last_scraped = timezone.now()
                            store.save()
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR('Company "Coles" not found.'))

        if options['aldi'] or run_all:
            self.stdout.write(self.style.SUCCESS('Running Aldi scraper...'))
            try:
                aldi_company = Company.objects.get(name="Aldi")
                stores = Store.objects.filter(company=aldi_company, is_active=True)
                stores_to_scrape = stores.order_by('last_scraped')[:batch_size]
                if not stores_to_scrape:
                    self.stdout.write(self.style.WARNING('No active Aldi stores found to scrape.'))
                else:
                    for store in stores_to_scrape:
                        if os.path.exists('stop.txt'):
                            self.stdout.write(self.style.WARNING("Stop signal detected. Halting before next store."))
                            break
                        scraper = ProductScraperAldi(
                            command=self, company=aldi_company.name, store_id=store.store_id,
                            store_name=store.store_name, state=store.state
                        )
                        scraper.run()
                        store.last_scraped = timezone.now()
                        store.save()
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR('Company "Aldi" not found.'))

        if options['iga'] or run_all:
            self.stdout.write(self.style.SUCCESS('Running IGA scraper...'))
            try:
                iga_company = Company.objects.get(name="Iga")
                stores = Store.objects.filter(company=iga_company, is_active=True)
                stores_to_scrape = stores.order_by('last_scraped')[:batch_size]
                if not stores_to_scrape:
                    self.stdout.write(self.style.WARNING('No active IGA stores found to scrape.'))
                else:
                    for store in stores_to_scrape:
                        if os.path.exists('stop.txt'):
                            self.stdout.write(self.style.WARNING("Stop signal detected. Halting before next store."))
                            break
                        scraper = ProductScraperIga(
                            command=self, company=iga_company.name, store_id=store.store_id,
                            retailer_store_id=store.retailer_store_id, store_name=store.store_name, state=store.state
                        )
                        scraper.run()
                        store.last_scraped = timezone.now()
                        store.save()
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR('Company "Iga" not found.'))
