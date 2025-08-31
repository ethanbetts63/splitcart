
from abc import abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from api.scrapers.base_store_scraper import BaseStoreScraper

class SeleniumBaseStoreScraper(BaseStoreScraper):
    """
    An abstract base class for store scrapers that use Selenium.
    """
    def __init__(self, command, company: str):
        super().__init__(command, company)
        self.driver = None

    def run(self):
        """The main public method that orchestrates the entire scraping process."""
        try:
            self.setup_driver()
            super().run()
        finally:
            self.teardown_driver()

    def setup_driver(self):
        """Initializes the Selenium driver and performs the warm-up."""
        self.stdout.write("\n--- Launching Selenium browser to warm up session and make API calls ---")
        chrome_options = Options()
        chrome_options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com)")
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        self.driver.set_script_timeout(60)
        self.driver.get(self.get_warmup_url())
        input("ACTION REQUIRED: Please solve any CAPTCHA in the browser, then press Enter here to continue...")
        self.driver.minimize_window()

    def teardown_driver(self):
        """Quits the Selenium driver."""
        if self.driver:
            self.driver.quit()
            self.stdout.write("\nBrowser closed.")

    @abstractmethod
    def get_warmup_url(self) -> str:
        """Returns the URL to use for the warm-up."""
        pass
