from django.core.management.base import BaseCommand
from django.utils import timezone
from companies.models.store import Store
from scraping.scrapers.product_scraper_woolworths import ProductScraperWoolworths
from scraping.scrapers.product_scraper_coles import ColesScraper as ProductScraperColes
from scraping.scrapers.product_scraper_aldi import ProductScraperAldi
from scraping.scrapers.product_scraper_iga import IgaScraper as ProductScraperIga
from scraping.utils.product_scraping_utils.get_woolworths_categories import get_woolworths_categories
from scraping.utils.product_scraping_utils.get_coles_categories import get_coles_categories
from scraping.scrapers.gs1_company_scraper import Gs1CompanyScraper
from scraping.utils.product_scraping_utils.scrape_scheduler import ScrapeScheduler
import os
import time

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

    def handle(self, *args, **options):
        stop_file = 'stop.txt'
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
        self._run_worker_loop(options)

    def _run_worker_loop(self, options):
        companies_to_scrape = []
        if options['woolworths']: companies_to_scrape.append('Woolworths')
        if options['coles']: companies_to_scrape.append('Coles')
        if options['aldi']: companies_to_scrape.append('Aldi')
        if options['iga']: companies_to_scrape.append('Iga')

        # If no specific companies are flagged, the scheduler will run on all companies
        scheduler = ScrapeScheduler(companies=companies_to_scrape if companies_to_scrape else None)
        
        scope_message = f" for {', '.join(companies_to_scrape)}" if companies_to_scrape else " for all companies"
        self.stdout.write(self.style.SUCCESS(f"Starting scraper in persistent worker mode{scope_message}..."))
        self.stdout.write(self.style.SUCCESS("Create a 'stop.txt' file in the root directory to gracefully stop the worker."))

        while True:
            if os.path.exists('stop.txt'):
                self.stdout.write(self.style.WARNING("Stop signal detected. Shutting down worker."))
                break

            self.stdout.write(self.style.HTTP_INFO("\nRequesting next candidate from scheduler..."))
            store_to_scrape = scheduler.get_next_candidate()

            if not store_to_scrape:
                self.stdout.write(self.style.WARNING("Scheduler returned no store. Waiting 30 seconds..."))
                time.sleep(30)
                continue

            self._scrape_single_store(store_to_scrape.pk)
            
            self.stdout.write(self.style.SUCCESS(f"Completed scrape. Waiting 5 seconds before next run..."))
            time.sleep(5)

        self.stdout.write(self.style.SUCCESS('Scraping worker stopped.'))

    def _scrape_single_store(self, store_pk):
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
                store.last_scraped = timezone.now()
                store.save()

        except Store.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Store with PK {store_pk} not found."))