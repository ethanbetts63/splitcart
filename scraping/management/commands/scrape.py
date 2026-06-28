import os
import time
from django.conf import settings
from django.core.management.base import BaseCommand
from scraping.scrapers.product_scraper_coles_v2 import ColesScraperV2
from scraping.scrapers.product_scraper_woolworths import ProductScraperWoolworths
from scraping.scrapers.product_scraper_aldi import ProductScraperAldi
from scraping.utils.coles_session_manager import ColesSessionManager
from scraping.utils.product_scraping_utils.get_woolworths_categories import get_woolworths_categories
from scraping.utils.product_scraping_utils.get_coles_categories import get_coles_categories
from scraping.utils.python_file_downloader import fetch_python_file

COLES_STORE_ID = 'COL:001'
WOOLWORTHS_STORE_ID = '1147'
ALDI_STORE_ID = 'ALDI001'


class Command(BaseCommand):
    help = (
        'Scrapes product data. '
        '--coles: session-persistent Coles scraper using a hardcoded API store ID. '
        '--woolworths/--aldi: single-company scraper using hardcoded API fulfilment IDs.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--woolworths', action='store_true', help='Scrape Woolworths products.')
        parser.add_argument('--coles', action='store_true', help='Run the session-persistent Coles v2 scraper.')
        parser.add_argument('--aldi', action='store_true', help='Scrape Aldi products.')
        parser.add_argument('--dev', action='store_true', help='Use the local dev server instead of the production server.')

    def handle(self, *args, **options):
        base_url = "http://127.0.0.1:8000" if options['dev'] else settings.API_SERVER_URL

        # All product scraping paths need up-to-date translation tables
        self._fetch_translation_tables(base_url)

        if options['coles']:
            self._scrape_coles()
            return

        if options['woolworths']:
            self._scrape_woolworths()
            return

        if options['aldi']:
            self._scrape_aldi()
            return

        self.stdout.write(self.style.WARNING("No company flag supplied. Use --coles, --woolworths, or --aldi."))

    def _fetch_translation_tables(self, base_url):
        self.stdout.write(self.style.SUCCESS('Updating translation tables...'))
        product_table_path = os.path.join(settings.BASE_DIR, 'scraping', 'data', 'product_normalized_name_brand_size_translation_table.json')
        brand_table_path = os.path.join(settings.BASE_DIR, 'scraping', 'data', 'brand_translation_table.json')
        fetch_python_file('product_translations', product_table_path, self, base_url)
        fetch_python_file('brand_translations', brand_table_path, self, base_url)
        self.stdout.write(self.style.SUCCESS('Translation tables are up to date.'))

    def _scrape_coles(self):
        """
        Phase 1 of the Coles scraping workflow. Visits category/list pages and
        writes JSONL files to the barcode_scraper_inbox. Run scrape_barcodes
        afterwards to complete phase 2 (individual product pages).
        """
        self.stdout.write(self.style.SUCCESS("--- Starting Coles Scraper ---"))
        session_manager = ColesSessionManager(self)

        try:
            session = session_manager.get_session(COLES_STORE_ID)
            categories = get_coles_categories()
            if not categories:
                self.stdout.write(self.style.ERROR('Could not fetch Coles categories. Aborting scrape.'))
                return

            scraper = ColesScraperV2(
                command=self,
                company="Coles",
                store_id=COLES_STORE_ID,
                store_name="Coles",
                state="",
                categories_to_fetch=categories,
                session=session,
                session_manager=session_manager
            )
            t_start = time.time()
            scraper.run()
            self.stdout.write(self.style.SUCCESS(f"Coles scraped in {time.time() - t_start:.0f}s"))
        finally:
            session_manager.close()

    def _scrape_woolworths(self):
        categories = get_woolworths_categories(self)
        if not categories:
            self.stdout.write(self.style.ERROR('Could not fetch Woolworths categories. Aborting scrape.'))
            return
        scraper = ProductScraperWoolworths(
            command=self, company="Woolworths", store_id=WOOLWORTHS_STORE_ID,
            store_name="Woolworths", state="", categories_to_fetch=categories
        )
        scraper.run()

    def _scrape_aldi(self):
        scraper = ProductScraperAldi(
            command=self, company="Aldi", store_id=ALDI_STORE_ID,
            store_name="Aldi", state=""
        )
        scraper.run()
