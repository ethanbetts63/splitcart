import requests
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

class Gs1CompanyScraper:
    """
    Scrapes GS1 to find company information for a given barcode.
    The process is optimized to use a browser only once to establish a session,
    then use a requests.Session for all subsequent scrapes.
    """
    def __init__(self, command):
        self.command = command
        self.driver = None
        self.session = None
        self.form_build_id = None

    def initialize_session(self, initial_barcode: str) -> bool:
        """
        Uses Selenium to perform the initial browser interaction, get session cookies,
        and then closes the browser.

        Args:
            initial_barcode: A valid barcode needed to visit the results page.

        Returns:
            True if the session was established successfully, False otherwise.
        """
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
        """
        Performs a single scrape using the established requests.Session.
        This method does not use Selenium and is therefore fast.

        Args:
            barcode: The barcode (GTIN) to scrape.

        Returns:
            A dictionary with scrape results or None on failure.
        """
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
                # Save the raw response for debugging if parsing fails
                with open('gs1_response.json', 'w') as f:
                    json.dump(json_response, f, indent=4)
                return None
        except requests.exceptions.RequestException as e:
            self.command.stderr.write(self.command.style.ERROR(f"An error occurred during the request for {barcode}: {e}"))
            return None
        except json.JSONDecodeError:
            self.command.stderr.write(self.command.style.ERROR(f"Failed to decode JSON for {barcode}."))
            return None

    def _initialize_driver(self):
        self.command.stdout.write("--- Initializing Selenium browser for session setup ---")
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
        self.command.stdout.write("Session created successfully.")

    def _close_driver(self):
        if self.driver:
            self.driver.quit()
            self.command.stdout.write("Selenium browser closed.")
