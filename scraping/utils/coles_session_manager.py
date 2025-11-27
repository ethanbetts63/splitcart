import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ColesSessionManager:
    """
    Manages a persistent Selenium browser and requests.Session for scraping Coles.
    Handles the initial CAPTCHA warm-up and attempts to switch stores without
    restarting the browser.
    """
    def __init__(self, command):
        self.command = command
        self.driver = None
        self.session = None
        self.current_store_id = None

    def _warm_up_session(self, store_id: str):
        """
        Launches the Selenium browser, waits for manual CAPTCHA solving,
        and creates a requests.Session. This is the initial setup.
        """
        self.command.stdout.write(self.command.style.SUCCESS("--- Starting new browser session for Coles ---"))
        numeric_store_id = store_id.split(':')[-1] if store_id and ':' in store_id else store_id

        try:
            options = webdriver.ChromeOptions()
            # This user-agent is critical for Coles not to block us immediately
            options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com.au)")
            
            self.driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()), 
                options=options
            )
            
            self.driver.get("https://www.coles.com.au")
            
            # Set the initial store
            self.driver.delete_all_cookies()
            self.driver.add_cookie({"name": "fulfillmentStoreId", "value": str(numeric_store_id)})
            self.driver.refresh()

            self.command.stdout.write(self.command.style.WARNING("ACTION REQUIRED: Please solve any CAPTCHA in the browser."))
            self.command.stdout.write("Waiting for main page to load after CAPTCHA...")
            
            # This wait is the core of the manual warm-up phase
            WebDriverWait(self.driver, 300, poll_frequency=2).until(
                EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
            )
            self.command.stdout.write(self.command.style.SUCCESS("Browser is ready. Creating requests session."))

            # Copy cookies from Selenium to requests.Session
            self.session = requests.Session()
            self.session.headers.update({"User-Agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com.au)"})
            for cookie in self.driver.get_cookies():
                self.session.cookies.set(cookie['name'], cookie['value'])
            
            self.current_store_id = store_id

            self.command.stdout.write("Session ready. Minimizing browser window until next CAPTCHA is needed.")
            self.driver.minimize_window()

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"A critical error occurred during the Selenium warm-up: {e}"))
            self.close() # Clean up driver if something went wrong
            raise InterruptedError("Failed to warm up session.") from e

    def get_session(self, store_id: str) -> requests.Session:
        """
        Provides a valid requests.Session.
        It will either start a new browser session or switch the store on an existing one.
        """
        if not self.driver or not self.session:
            self._warm_up_session(store_id)
        elif self.current_store_id != store_id:
            self.switch_store(store_id)
        
        return self.session

    def switch_store(self, store_id: str):
        """
        Attempts to switch the store context on the existing session.
        """
        self.command.stdout.write(f"--- Switching Coles store to {store_id} ---")
        numeric_store_id = store_id.split(':')[-1] if store_id and ':' in store_id else store_id
        
        # Update the cookie in the live browser and refresh
        self.driver.add_cookie({"name": "fulfillmentStoreId", "value": str(numeric_store_id)})
        self.driver.refresh()
        
        # We should wait a bit for the page to reload and register the change
        WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
        )

        # Re-sync cookies with the requests.Session to ensure it's up-to-date
        self.session.cookies.clear()
        for cookie in self.driver.get_cookies():
            self.session.cookies.set(cookie['name'], cookie['value'])
        
        self.current_store_id = store_id
        self.command.stdout.write(f"Store switched successfully.")

    def is_blocked(self, response_text: str) -> bool:
        """
        Checks if the response HTML indicates that the session has been blocked
        (e.g., by a CAPTCHA page).
        """
        # A key indicator of a valid page is the __NEXT_DATA__ script.
        # If it's missing, we are likely on a block/CAPTCHA page.
        return '<script id="__NEXT_DATA__"' not in response_text

    def close(self):
        """
        Closes the Selenium browser and cleans up.
        """
        if self.driver:
            self.command.stdout.write("--- Closing browser session ---")
            self.driver.quit()
            self.driver = None
            self.session = None
