import requests
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

class Gs1CompanyScraper:
    """
    Scrapes GS1 to find company information for a given barcode.
    Uses a Selenium warm-up phase to handle cookie consent, then uses requests.
    """
    def __init__(self, command):
        self.command = command
        self.session = None
        self.driver = None

    def warm_up_session(self, barcode: str):
        """
        Uses Selenium to allow the user to manually accept cookies, then creates
        a valid requests session.
        """
        try:
            url = f"https://www.gs1.org/services/verified-by-gs1/results?gtin={barcode}"
            
            options = webdriver.ChromeOptions()
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
            
            self.command.stdout.write("--- Initializing Selenium browser ---")
            self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
            
            self.driver.get(url)
            
            self.command.stdout.write("\n--------------------------------------------------")
            self.command.stdout.write("ACTION REQUIRED: Please accept cookies in the browser.")
            input("Press Enter in this terminal after you have accepted the cookies...")
            self.command.stdout.write("--------------------------------------------------\n")
            
            self.command.stdout.write("Creating session from browser cookies...")
            self.session = requests.Session()
            # Using a simplified header, as requested
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
            })
            for cookie in self.driver.get_cookies():
                self.session.cookies.set(cookie['name'], cookie['value'])

        except Exception as e:
            raise InterruptedError(f"An error occurred during the Selenium phase: {e}")

        if not self.session:
            raise InterruptedError("Failed to create a requests session. Aborting.")

    def get_company_info(self, barcode: str):
        """
        Uses the warmed-up session to fetch and parse the company info.
        """
        if not self.session:
            self.command.stderr.write(self.command.style.ERROR("Session not warmed up. Please run warm_up_session first."))
            return None

        self.command.stdout.write(f"--- Scraping GS1 API for barcode: {barcode} ---")
        # NOTE: This is the AJAX URL the page calls, not the page URL itself.
        url = f"https://www.gs1.org/services/verified-by-gs1/results?gtin={barcode}&ajax_form=1&_wrapper_format=drupal_ajax"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            json_response = response.json()

            company_name = None
            for command in json_response:
                if command.get('command') == 'settings':
                    status_message = command.get('settings', {}).get('gsone_verified_search', {}).get('statusMessage', '')
                    match = re.search(r'registered to (?:company: )?(.*?)\.', status_message, re.IGNORECASE)
                    if match:
                        company_name = match.group(1).strip()
                        break
            
            if company_name:
                self.command.stdout.write(self.command.style.SUCCESS(f"Success! Company Name: {company_name}"))
                return company_name
            else:
                self.command.stderr.write(self.command.style.ERROR("Could not find company name in the API response."))
                with open('gs1_response.json', 'w') as f:
                    json.dump(json_response, f, indent=4)
                self.command.stdout.write("Saved API response to gs1_response.json")
                return None

        except requests.exceptions.RequestException as e:
            self.command.stderr.write(self.command.style.ERROR(f"An error occurred during the request: {e}"))
            return None
        except json.JSONDecodeError:
            self.command.stderr.write(self.command.style.ERROR("Failed to decode JSON from the response."))
            return None

    def run(self, barcode: str):
        """
        Orchestrates the entire scraping process.
        """
        try:
            self.warm_up_session(barcode)
            self.get_company_info(barcode)

            self.command.stdout.write("\n--------------------------------------------------")
            input("Process complete. Browser is still open for inspection. Press Enter to close...")
            self.command.stdout.write("--------------------------------------------------\n")

        except InterruptedError as e:
            self.command.stderr.write(self.command.style.ERROR(f"Process stopped: {e}"))
        finally:
            if self.driver:
                self.driver.quit()
