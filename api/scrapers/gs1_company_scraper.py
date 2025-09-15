import requests
import json
import re
import os
import time
from django.conf import settings
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from products.models import BrandPrefix, Product, ProductBrand

class Gs1CompanyScraper:
    """
    Scrapes GS1 to find company information for a given barcode.
    This class orchestrates the entire strategic scraping process.
    """
    def __init__(self, command):
        self.command = command
        self.driver = None
        self.session = None
        self.form_build_id = None

    def run(self):
        """
        Runs the entire strategic scraping process: prioritize brands, initialize
        a session, and then loop through the top 30 unverified brands.
        """
        self.command.stdout.write(self.command.style.SUCCESS('--- Running GS1 Strategic Scraper to Inbox ---\n'))
        
        # --- Setup ---
        inbox_dir = os.path.join(settings.BASE_DIR, 'api', 'data', 'prefix_inbox')
        os.makedirs(inbox_dir, exist_ok=True)
        timestamp = timezone.now().strftime('%Y-%m-%d_%H-%M-%S')
        output_file = os.path.join(inbox_dir, f'gs1_results_{timestamp}.jsonl')
        self.command.stdout.write(f"Saving results to: {output_file}\n")

        # --- Prioritize Brands ---
        self.command.stdout.write("Prioritizing unconfirmed brands by product count...")
        
        unconfirmed_brands = []
        all_brands = ProductBrand.objects.all().prefetch_related('prefix_analysis')

        for brand in all_brands:
            try:
                if brand.prefix_analysis.confirmed_official_prefix:
                    continue
            except BrandPrefix.DoesNotExist:
                pass
            
            count = Product.objects.filter(brand=brand.name).count()
            if count > 0:
                unconfirmed_brands.append({'brand': brand, 'count': count})
        
        sorted_brands = sorted(unconfirmed_brands, key=lambda x: x['count'], reverse=True)
        self.command.stdout.write(f"Found {len(sorted_brands)} unconfirmed brands with products to scrape.")

        # --- Initialize Scraper Session (ONCE) ---
        first_product_for_session = Product.objects.exclude(barcode__isnull=True).exclude(barcode__exact='').first()
        if not first_product_for_session:
            self.command.stdout.write(self.command.style.ERROR("No products with barcodes found in the database. Cannot initialize GS1 session."))
            return

        if not self.initialize_session(first_product_for_session.barcode):
            self.command.stdout.write(self.command.style.ERROR("Failed to initialize GS1 session. Aborting scrape."))
            return

        # --- Main Scraping Loop ---
        successful_scrapes = 0
        target_brands = sorted_brands[:30]

        for i, brand_info in enumerate(target_brands):
            target_brand = brand_info['brand']
            self.command.stdout.write(f"--- Scrape Attempt {i + 1}/{len(target_brands)} ---\n")
            self.command.stdout.write(f"Selected brand: {target_brand.name}\n")

            product_with_barcode = Product.objects.filter(
                brand=target_brand.name
            ).exclude(barcode__isnull=True).exclude(barcode__exact='').first()

            if not product_with_barcode:
                self.command.stdout.write(self.command.style.WARNING(f"Brand {target_brand.name} has no products with barcodes. Skipping."))
                continue

            result = self.scrape_barcode(product_with_barcode.barcode)

            if result and result.get('license_key'):
                self._write_result_to_inbox(result, target_brand, product_with_barcode.barcode, output_file)
                successful_scrapes += 1
            else:
                self.command.stderr.write(self.command.style.ERROR(f"Scrape failed for {target_brand.name}."))

            if i < len(target_brands) - 1:
                self.command.stdout.write("Waiting 5 seconds before next scrape...")
                time.sleep(5)
        
        self.command.stdout.write(self.command.style.SUCCESS(f'--- GS1 Scraper Run Complete. {successful_scrapes} new records saved to inbox. ---\n'))

    def _write_result_to_inbox(self, result, target_brand, barcode, output_file):
        self.command.stdout.write(self.command.style.SUCCESS(f"Successfully scraped {target_brand.name}."))
        output_record = {
            'scraped_at': timezone.now().isoformat(),
            'target_brand_id': target_brand.id,
            'target_brand_name': target_brand.name,
            'scraped_barcode': barcode,
            'confirmed_license_key': result['license_key'],
            'confirmed_company_name': result['company_name'],
        }
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(output_record) + '\n')

    def initialize_session(self, initial_barcode: str) -> bool:
        try:
            self._initialize_driver()
            self._warm_up_session(initial_barcode)
            return True
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"An unexpected error occurred during session initialization: {e}"))
            return False
        finally:
            self._close_driver()

    def scrape_barcode(self, barcode: str):
        if not self.session or not self.form_build_id:
            self.command.stderr.write(self.command.style.ERROR("Session not initialized. Cannot perform scrape."))
            return None

        url = f"https://www.gs1.org/services/verified-by-gs1/results?gtin={barcode}&ajax_form=1&_wrapper_format=drupal_ajax"
        try:
            data = {
                'gtin': barcode,
                'search_type': 'gtin',
                'form_build_id': self.form_build_id,
                'form_id': 'verified_search_form',
                'gtin_submit': 'Search',
            }
            response = self.session.post(url, data=data)
            response.raise_for_status()
            json_response = response.json()

            license_key = None
            company_name = None

            for command in json_response:
                if command.get('command') == 'insert' and command.get('selector') == '#product-container':
                    html_data = command['data']
                    key_match = re.search(r"License Key</td>\s*<td><strong>(\d+)</strong></td>", html_data)
                    if key_match:
                        license_key = key_match.group(1)
                    name_match = re.search(r"registered to <strong>(.*?)</strong>", html_data)
                    if name_match:
                        company_name = name_match.group(1).strip()
                    break

            if license_key and company_name:
                return {'license_key': license_key, 'company_name': company_name}
            else:
                return None
        except requests.exceptions.RequestException as e:
            self.command.stderr.write(self.command.style.ERROR(f"An error occurred during the request for {barcode}: {e}"))
            return None
        except json.JSONDecodeError:
            self.command.stderr.write(self.command.style.ERROR(f"Failed to decode JSON for {barcode}."))
            return None

    def _initialize_driver(self):
        self.command.stdout.write("--- Initializing Selenium browser for session setup ---\n")
        options = webdriver.ChromeOptions()
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
        options.add_argument("--incognito")
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    def _warm_up_session(self, barcode: str):
        url = f"https://www.gs1.org/services/verified-by-gs1/results?gtin={barcode}"
        self.driver.get(url)
        
        self.command.stdout.write("\n--------------------------------------------------\n")
        self.command.stdout.write("ACTION REQUIRED: Please accept cookies in the browser.")
        input("Press Enter in this terminal after you have accepted the cookies...")
        self.command.stdout.write("--------------------------------------------------\n")
        
        self.command.stdout.write("Creating session from browser cookies...")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Referer': url
        })
        for cookie in self.driver.get_cookies():
            self.session.cookies.set(cookie['name'], cookie['value'])
        
        self.form_build_id = self.driver.find_element(By.NAME, "form_build_id").get_attribute("value")
        self.command.stdout.write("Session created successfully.")

    def _close_driver(self):
        if self.driver:
            self.driver.quit()
            self.command.stdout.write("Selenium browser closed.")