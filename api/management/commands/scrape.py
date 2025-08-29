from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from api.utils.management_utils.run_coles_scraper import run_coles_scraper
from companies.models.company import Company
from companies.models.store import Store
from api.scrapers.scrape_and_save_aldi import AldiScraper
from api.scrapers.scrape_and_save_iga import IgaScraper
from api.scrapers.scrape_and_save_woolworths import WoolworthsScraper
from api.utils.scraper_utils.get_woolworths_categories import get_woolworths_categories

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
            try:
                woolworths_company = Company.objects.get(name="Woolworths")
                stores = Store.objects.filter(company=woolworths_company, is_active=True)
                stores_to_scrape = stores.order_by('last_scraped_products')[:batch_size]
                categories = get_woolworths_categories(self)
                if not categories:
                    self.stdout.write(self.style.ERROR('Could not fetch Woolworths categories. Aborting Woolworths scrape.'))
                else:
                    for store in stores_to_scrape:
                        scraper = WoolworthsScraper(
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
            run_coles_scraper(self, batch_size)

        if options['aldi'] or run_all:
            try:
                aldi_company = Company.objects.get(name="Aldi")
                stores = Store.objects.filter(company=aldi_company, is_active=True)
                stores_to_scrape = stores.order_by('last_scraped_products')[:batch_size]
                for store in stores_to_scrape:
                    scraper = AldiScraper(
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
                stores_to_scrape = stores.order_by('last_scraped_products')[:batch_size]
                for store in stores_to_scrape:
                    scraper = IgaScraper(
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
