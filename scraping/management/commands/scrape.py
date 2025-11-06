from django.core.management.base import BaseCommand
from companies.models.store import Store
from scraping.utils.product_scraping_utils.get_woolworths_categories import get_woolworths_categories
from scraping.utils.product_scraping_utils.get_coles_categories import get_coles_categories
from scraping.scrapers.gs1_company_scraper import Gs1CompanyScraper
import requests
import time
import os
from django.conf import settings
from scraping.utils.python_file_downloader import fetch_python_file

class Command(BaseCommand):
    help = 'Runs the scrapers as a persistent worker, continuously selecting one store at a time based on the ScrapeScheduler.'

    def add_arguments(self, parser):
        parser.add_argument('--store-pk', type=int, help='Scrape a specific store by its database primary key as a one-off task.')
        parser.add_argument('--gs1', action='store_true', help='Run the GS1 company prefix scraper test as a one-off task.')
        # Company flags to filter the scheduler's scope
        parser.add_argument('--woolworths', action='store_true', help='Limit the scraper to Woolworths stores.')
        parser.add_argument('--coles', action='store_true', help='Limit the scraper to Coles stores.')
        parser.add_argument('--aldi', action='store_true', help='Limit the scraper to Aldi stores.')
        parser.add_argument('--iga', action='store_true', help='Limit the scraper to IGA stores.')
        parser.add_argument('--dev', action='store_true', help='Use dev server.')

    def handle(self, *args, **options):
        base_url = "http://127.0.0.1:8000" if options['dev'] else settings.API_SERVER_URL
        
        self.stdout.write(self.style.SUCCESS('Updating translation tables...'))
        product_table_path = os.path.join(settings.BASE_DIR, 'scraping', 'data', 'product_translation_table.py')
        brand_table_path = os.path.join(settings.BASE_DIR, 'scraping', 'data', 'brand_translation_table.py')
        fetch_python_file('product_translations', product_table_path, self, base_url)
        fetch_python_file('brand_translations', brand_table_path, self, base_url)
        self.stdout.write(self.style.SUCCESS('Translation tables are up to date.'))

        stop_file = os.path.join('scraping', 'stop.txt')
        if os.path.exists(stop_file):
            os.remove(stop_file)
            self.stdout.write(self.style.SUCCESS(f"Removed previous stop file: {stop_file}"))

        # Handle one-off tasks first
        if options.get('store_pk'):
            self._scrape_single_store(options['store_pk'])
            self.stdout.write(self.style.SUCCESS('Scraping complete for single store.'))
            return

        if options['gs1']:
            self.stdout.write(self.style.SUCCESS('Running GS1 scraper...'))
            Gs1CompanyScraper(self).run()
            self.stdout.write(self.style.SUCCESS('GS1 scraping complete.'))
            return

        # If no one-off task is specified, start the persistent worker loop
        self._run_worker_loop(options, base_url)

    def _run_worker_loop(self, options, base_url):
        companies_to_scrape = []
        if options['woolworths']: companies_to_scrape.append('Woolworths')
        if options['coles']: companies_to_scrape.append('Coles')
        if options['aldi']: companies_to_scrape.append('Aldi')
        if options['iga']: companies_to_scrape.append('Iga')

        scope_message = f" for {', '.join(companies_to_scrape)}" if companies_to_scrape else " for all companies"
        self.stdout.write(self.style.SUCCESS(f"Starting scraper in persistent worker mode{scope_message}..."))
        self.stdout.write(self.style.SUCCESS("Create a 'stop.txt' file in the 'scraping' directory to gracefully stop the worker."))

        while True:
            if os.path.exists(os.path.join('scraping', 'stop.txt')):
                self.stdout.write(self.style.WARNING("Stop signal detected. Shutting down worker."))
                break

            self.stdout.write(self.style.HTTP_INFO("\nRequesting next candidate from scheduler API..."))
            try:
                # Construct the API URL with query parameters for company filtering
                api_url = f"{base_url}/api/scheduler/next-candidate/"
                params = {'company': companies_to_scrape}
                headers = {'X-Internal-API-Key': settings.INTERNAL_API_KEY}
                response = requests.get(api_url, params=params, headers=headers, timeout=30)
                response.raise_for_status() # Raise an exception for bad status codes

                if response.status_code == 204:
                    self.stdout.write(self.style.WARNING("Scheduler returned no store. Waiting 30 seconds..."))
                    time.sleep(30)
                    continue
                
                store_to_scrape = response.json()

            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Failed to get next store from API: {e}. Retrying in 60 seconds..."))
                time.sleep(60)
                continue

            try:
                self._scrape_single_store(store_to_scrape['pk'])
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"A critical network error occurred during scraping: {e}"))
                self.stdout.write(self.style.ERROR("Stopping the scraper worker due to network issues."))
                break
            

        self.stdout.write(self.style.SUCCESS('Scraping worker stopped.'))

    def _scrape_single_store(self, store_pk):
        # Import scraper classes locally to prevent ModuleNotFoundError on startup
        from scraping.scrapers.product_scraper_woolworths import ProductScraperWoolworths
        from scraping.scrapers.product_scraper_coles import ColesScraper as ProductScraperColes
        from scraping.scrapers.product_scraper_aldi import ProductScraperAldi
        from scraping.scrapers.product_scraper_iga import IgaScraper as ProductScraperIga

        try:
            store = Store.objects.select_related('company').get(pk=store_pk)
            company_name = store.company.name
            self.stdout.write(self.style.SUCCESS(f"-- Scraping: {store.store_name} ({company_name}) [PK: {store_pk}]"))

            scraper = None
            # This logic correctly dispatches the right scraper based on the store's company
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

        except Store.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Store with PK {store_pk} not found."))