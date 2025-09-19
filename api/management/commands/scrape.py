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
        parser.add_argument('--store-pk', type=int, help='Scrape a specific store by its database primary key, ignoring batching.')

    def handle(self, *args, **options):
        # Clean up a previous stop file at the beginning of a new run.
        stop_file = 'stop.txt'
        if os.path.exists(stop_file):
            os.remove(stop_file)
            self.stdout.write(self.style.SUCCESS(f"Removed previous stop file: {stop_file}"))

        run_all = not any(options[company] for company in ['woolworths', 'coles', 'aldi', 'iga', 'gs1'])
        batch_size = options['batch_size']
        store_pk = options['store_pk']

        if options['woolworths'] or run_all:
            try:
                woolworths_company = Company.objects.get(name="Woolworths")
                stores = Store.objects.filter(company=woolworths_company, is_active=True, division__name__iexact='supermarkets')
                
                if store_pk:
                    stores_to_scrape = stores.filter(pk=store_pk)
                    self.stdout.write(self.style.SUCCESS(f"Scraping specific store with PK: {store_pk}"))
                else:
                    stores_to_scrape = stores.order_by('last_scraped_products')[:batch_size]

                categories = get_woolworths_categories(self)
                if not categories:
                    self.stdout.write(self.style.ERROR('Could not fetch Woolworths categories. Aborting Woolworths scrape.'))
                else:
                    for store in stores_to_scrape:
                        if os.path.exists('stop.txt'):
                            self.stdout.write(self.style.WARNING("Stop signal detected. Halting before next store."))
                            break
                        scraper = ProductScraperWoolworths(
                            command=self,
                            company=woolworths_company.name,
                            store_id=store.store_id,
                            store_name=store.store_name,
                            state=store.state,
                            categories_to_fetch=categories
                        )
                        scraper.run()
                        store.last_scraped_products = timezone.now()
                        store.save()
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR('Company "Woolworths" not found.'))

        if options['coles'] or run_all:
            try:
                coles_company = Company.objects.get(name="Coles")
                stores = Store.objects.filter(company=coles_company, is_active=True)
                
                if store_pk:
                    stores_to_scrape = stores.filter(pk=store_pk)
                    self.stdout.write(self.style.SUCCESS(f"Scraping specific store with PK: {store_pk}"))
                else:
                    stores_to_scrape = stores.order_by('last_scraped_products')[:batch_size]

                categories = get_coles_categories()
                if not categories:
                    self.stdout.write(self.style.ERROR('Could not fetch Coles categories. Aborting Coles scrape.'))
                else:
                    for store in stores_to_scrape:
                        if os.path.exists('stop.txt'):
                            self.stdout.write(self.style.WARNING("Stop signal detected. Halting before next store."))
                            break
                        scraper = ProductScraperColes(
                            command=self,
                            company=coles_company.name,
                            store_id=store.store_id,
                            store_name=store.store_name,
                            state=store.state,
                            categories_to_fetch=categories
                        )
                        scraper.run()
                        store.last_scraped_products = timezone.now()
                        store.save()
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR('Company "Coles" not found.'))

        if options['aldi'] or run_all:
            try:
                aldi_company = Company.objects.get(name="Aldi")
                stores = Store.objects.filter(company=aldi_company, is_active=True)

                if store_pk:
                    stores_to_scrape = stores.filter(pk=store_pk)
                    self.stdout.write(self.style.SUCCESS(f"Scraping specific store with PK: {store_pk}"))
                else:
                    stores_to_scrape = stores.order_by('last_scraped_products')[:batch_size]
                for store in stores_to_scrape:
                    if os.path.exists('stop.txt'):
                        self.stdout.write(self.style.WARNING("Stop signal detected. Halting before next store."))
                        break
                    scraper = ProductScraperAldi(
                        command=self,
                        company=aldi_company.name,
                        store_id=store.store_id,
                        store_name=store.store_name,
                        state=store.state
                    )
                    scraper.run()
                    store.last_scraped_products = timezone.now()
                    store.save()
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR('Company "Aldi" not found.'))

        if options['iga'] or run_all:
            try:
                iga_company = Company.objects.get(name="Iga")
                stores = Store.objects.filter(company=iga_company, is_active=True)

                if store_pk:
                    stores_to_scrape = stores.filter(pk=store_pk)
                    self.stdout.write(self.style.SUCCESS(f"Scraping specific store with PK: {store_pk}"))
                else:
                    stores_to_scrape = stores.order_by('last_scraped_products')[:batch_size]
                for store in stores_to_scrape:
                    if os.path.exists('stop.txt'):
                        self.stdout.write(self.style.WARNING("Stop signal detected. Halting before next store."))
                        break
                    scraper = ProductScraperIga(
                        command=self,
                        company=iga_company.name,
                        store_id=store.store_id,
                        retailer_store_id=store.retailer_store_id,
                        store_name=store.store_name,
                        state=store.state
                    )
                    scraper.run()
                    store.last_scraped_products = timezone.now()
                    store.save()
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR('Company "Iga" not found.'))

        self.stdout.write(self.style.SUCCESS('Scraping complete.'))

        if options['gs1']:
            scraper = Gs1CompanyScraper(self)
            scraper.run()
