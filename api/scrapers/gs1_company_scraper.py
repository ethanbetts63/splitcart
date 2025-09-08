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
    Encapsulates the entire process of scraping and writing to an inbox file.
    """
    def __init__(self, command):
        self.command = command
        self.driver = None
        self.session = None
        self.form_build_id = None

    def run(self, barcode: str, target_brand, output_file: str) -> bool:
        """
        Orchestrates a single scrape and writes the result to the output file.
        Returns True on success, False on failure.
        """
        try:
            self._initialize_driver()
            self._warm_up_session(barcode)
            result = self._get_company_info(barcode)

            if result and result.get('license_key'):
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
                return True
            else:
                self.command.stderr.write(self.command.style.ERROR(f"Scrape failed for {target_brand.name}."))
                return False
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"An unexpected error occurred during scrape for {barcode}: {e}"))
            return False
        finally:
            self.close()

    def _initialize_driver(self):
        self.command.stdout.write("--- Initializing Selenium browser ---")
        options = webdriver.ChromeOptions()
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
        options.add_argument("--incognito")
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    def _warm_up_session(self, barcode: str):
        url = f"https://www.gs1.org/services/verified-by-gs1/results?gtin={barcode}"
        self.driver.get(url)
        
        self.command.stdout.write("\n--------------------------------------------------")
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

    def _get_company_info(self, barcode: str):
        if not self.session or not self.form_build_id:
            self.command.stderr.write(self.command.style.ERROR("Session not warmed up."))
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

            # Find the single 'insert' command that contains the final rendered HTML data.
            for command in json_response:
                if command.get('command') == 'insert' and command.get('selector') == '#product-container':
                    html_data = command['data']

                    # Extract License Key from the HTML
                    key_match = re.search(r"License Key</td>\s*<td><strong>(\d+)</strong></td>", html_data)
                    if key_match:
                        license_key = key_match.group(1)

                    # Extract Company Name from the HTML
                    # This is more robust than relying on the settings -> statusMessage path.
                    name_match = re.search(r"registered to <strong>(.*?)</strong>", html_data)
                    if name_match:
                        company_name = name_match.group(1).strip()

                    # Once we've processed the main data block, we can exit the loop.
                    break

            if license_key and company_name:
                return {'license_key': license_key, 'company_name': company_name}
            else:
                with open('gs1_response.json', 'w') as f:
                    json.dump(json_response, f, indent=4)
                return None
        except requests.exceptions.RequestException as e:
            self.command.stderr.write(self.command.style.ERROR(f"An error occurred during the request: {e}"))
            return None
        except json.JSONDecodeError:
            self.command.stderr.write(self.command.style.ERROR("Failed to decode JSON from the response."))
            return None

    def close(self):
        if self.driver:
            self.driver.quit()
            self.command.stdout.write("Browser closed.")