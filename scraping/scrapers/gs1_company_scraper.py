import requests
import json
import re
import os
from django.conf import settings
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

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
        
        base_url = "http://127.0.0.1:8000" # Assuming local dev server for scraper
        headers = {'X-Internal-API-Key': settings.INTERNAL_API_KEY}

        # --- Setup ---
        outbox_dir = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'outboxes', 'gs1_outbox')
        os.makedirs(outbox_dir, exist_ok=True)
        timestamp = timezone.now().strftime('%Y-%m-%d_%H-%M-%S')
        output_file = os.path.join(outbox_dir, f'gs1_results_{timestamp}.jsonl')
        self.command.stdout.write(f"Saving results to: {output_file}\n")

        # --- Prioritize Brands (via API) ---
        self.command.stdout.write("Fetching unconfirmed brands from API...")
        try:
            api_url = f"{base_url}/api/gs1/unconfirmed-brands/"
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            unconfirmed_brands_data = response.json()
            self.command.stdout.write(f"Found {len(unconfirmed_brands_data)} unconfirmed brands to scrape.")
        except requests.exceptions.RequestException as e:
            self.command.stderr.write(self.command.style.ERROR(f"Failed to fetch unconfirmed brands from API: {e}"))
            return

        # --- Initialize Scraper Session (ONCE) ---
        if not unconfirmed_brands_data:
            self.command.stdout.write(self.command.style.WARNING("No unconfirmed brands found. Skipping session initialization."))
            return

        # Get a barcode for the first unconfirmed brand to initialize the session
        first_brand_id = unconfirmed_brands_data[0]['brand_id']
        first_brand_name = unconfirmed_brands_data[0]['brand_name']
        initial_barcode = None
        try:
            api_url = f"{base_url}/api/brands/{first_brand_id}/sample-barcode/"
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            barcode_data = response.json()
            initial_barcode = barcode_data.get('barcode')
            if not initial_barcode:
                self.command.stderr.write(self.command.style.ERROR(f"No barcode found for brand {first_brand_name} (ID: {first_brand_id}). Cannot initialize GS1 session."))
                return
        except requests.exceptions.RequestException as e:
            self.command.stderr.write(self.command.style.ERROR(f"Failed to fetch initial barcode for brand {first_brand_name} (ID: {first_brand_id}) from API: {e}"))
            return

        if not self.initialize_session(initial_barcode):
            self.command.stdout.write(self.command.style.ERROR("Failed to initialize GS1 session. Aborting scrape."))
            return

        # --- Main Scraping Loop ---
        successful_scrapes = 0
        consecutive_failures = 0
        MAX_SUCCESSFUL_SCRAPES = 30
        MAX_CONSECUTIVE_FAILURES = 5
        
        brand_index = 0
        target_brands = unconfirmed_brands_data # Initial fetch

        while successful_scrapes < MAX_SUCCESSFUL_SCRAPES and consecutive_failures < MAX_CONSECUTIVE_FAILURES:
            if not target_brands: # No brands to scrape, or ran out
                self.command.stdout.write(self.command.style.WARNING("No more unconfirmed brands to scrape. Stopping."))
                break

            if brand_index >= len(target_brands):
                self.command.stdout.write("Ran out of brands in current list. Fetching more...")
                try:
                    api_url = f"{base_url}/api/gs1/unconfirmed-brands/"
                    response = requests.get(api_url, headers=headers, timeout=30)
                    response.raise_for_status()
                    new_unconfirmed_brands_data = response.json()
                    if not new_unconfirmed_brands_data:
                        self.command.stdout.write(self.command.style.WARNING("No new unconfirmed brands found. Stopping."))
                        break
                    target_brands = new_unconfirmed_brands_data
                    brand_index = 0 # Reset index for the new list
                    self.command.stdout.write(f"Fetched {len(target_brands)} new unconfirmed brands.")
                except requests.exceptions.RequestException as e:
                    self.command.stderr.write(self.command.style.ERROR(f"Failed to fetch more unconfirmed brands from API: {e}. Stopping."))
                    break

            brand_info = target_brands[brand_index]
            target_brand_id = brand_info['brand_id']
            target_brand_name = brand_info['brand_name']
            
            self.command.stdout.write(f"--- Scrape Attempt (Successes: {successful_scrapes}/{MAX_SUCCESSFUL_SCRAPES}, Failures: {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}) ---")
            self.command.stdout.write(f"Selected brand: {target_brand_name}\n")

            brand_index += 1 # Move to the next brand for the next iteration

            barcode_to_scrape = None
            try:
                api_url = f"{base_url}/api/brands/{target_brand_id}/sample-barcode/"
                response = requests.get(api_url, headers=headers, timeout=30)
                response.raise_for_status()
                barcode_data = response.json()
                barcode_to_scrape = barcode_data.get('barcode')
                if not barcode_to_scrape:
                    self.command.stdout.write(self.command.style.WARNING(f"No barcode found for brand {target_brand_name} (ID: {target_brand_id}). Skipping."))
                    consecutive_failures += 1
                    continue
            except requests.exceptions.RequestException as e:
                self.command.stderr.write(self.command.style.ERROR(f"Failed to fetch barcode for brand {target_brand_name} (ID: {target_brand_id}) from API: {e}. Skipping."))
                consecutive_failures += 1
                continue

            result = self.scrape_barcode(barcode_to_scrape)

            if result and result.get('license_key'):
                self._write_result_to_inbox(result, target_brand_id, target_brand_name, barcode_to_scrape, output_file)
                successful_scrapes += 1
                consecutive_failures = 0 # Reset on success
            else:
                self.command.stderr.write(self.command.style.ERROR(f"Scrape failed for {target_brand_name}."))
                consecutive_failures += 1
        
        self.command.stdout.write(self.command.style.SUCCESS(f'--- GS1 Scraper Run Complete. {successful_scrapes} new records saved to inbox. ---\n'))

    def _write_result_to_inbox(self, result, target_brand_id, target_brand_name, barcode, output_file):
        self.command.stdout.write(self.command.style.SUCCESS(f"Successfully scraped {target_brand_name}."))
        output_record = {
            'scraped_date': timezone.now().date().isoformat(),
            'target_brand_id': target_brand_id,
            'target_brand_name': target_brand_name,
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