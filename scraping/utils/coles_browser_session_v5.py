from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


class ColesBrowserSessionV5:
    """
    Manages a persistent Chrome session for Coles scraping.

    Fetches product data using the browser's fetch() API against the standard
    HTML browse URLs, then extracts __NEXT_DATA__ with a string search rather
    than DOMParser. This avoids the DOMParser slowness that caused script
    timeouts in the original fetch() approach.
    """

    def __init__(self, command):
        self.command = command
        self.driver = None
        self.current_store_id = None

    def start(self, store_id: str):
        """Launches Chrome, sets the initial store, and waits for CAPTCHA solve."""
        numeric_id = self._numeric(store_id)
        self.command.stdout.write(self.command.style.SUCCESS("--- Starting Coles V5 browser session ---"))

        options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options,
        )
        self.driver.set_script_timeout(90)

        self.driver.execute_cdp_cmd("Network.enable", {})
        self.driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": [
            "*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp", "*.svg", "*.ico",
            "*.woff", "*.woff2", "*.ttf",
            "*google-analytics*", "*googletagmanager*", "*doubleclick*",
            "*facebook*", "*analytics*", "*segment.io*",
        ]})

        self.driver.get("https://www.coles.com.au")
        self.driver.delete_all_cookies()
        self.driver.add_cookie({"name": "fulfillmentStoreId", "value": numeric_id})
        self.driver.refresh()

        self.command.stdout.write(self.command.style.WARNING(
            "ACTION REQUIRED: Please solve any CAPTCHA in the browser."
        ))
        self._wait_for_ready(300)
        self.current_store_id = store_id
        self.command.stdout.write(self.command.style.SUCCESS("Session ready."))

    def switch_store(self, store_id: str):
        """Updates the fulfillmentStoreId cookie and reloads to register the new store."""
        if store_id == self.current_store_id:
            return
        numeric_id = self._numeric(store_id)
        self.command.stdout.write(f"--- Switching Coles store to {store_id} ---")
        self.driver.add_cookie({"name": "fulfillmentStoreId", "value": numeric_id})
        self.driver.get("https://www.coles.com.au")
        self._wait_for_ready(60)
        self.current_store_id = store_id
        self.command.stdout.write("Store switched.")

    def fetch_browse_page(self, url: str):
        """
        Fetches a Coles browse URL using the browser's fetch() API, then
        extracts __NEXT_DATA__ via string search (no DOMParser). Returns the
        full __NEXT_DATA__ dict, or None if blocked/failed.
        """
        try:
            return self.driver.execute_async_script("""
                var done = arguments[0];
                var url = arguments[1];
                fetch(url, {credentials: 'include'})
                    .then(function(r) { return r.ok ? r.text() : null; })
                    .then(function(html) {
                        if (!html) { done(null); return; }
                        var marker = 'id="__NEXT_DATA__"';
                        var idx = html.indexOf(marker);
                        if (idx < 0) { done(null); return; }
                        var start = html.indexOf('>', idx) + 1;
                        var end = html.indexOf('</script>', start);
                        if (start <= 0 || end < 0) { done(null); return; }
                        try { done(JSON.parse(html.substring(start, end))); }
                        catch(e) { done(null); }
                    })
                    .catch(function() { done(null); });
            """, url)
        except (TimeoutException, WebDriverException) as e:
            self.command.stderr.write(self.command.style.ERROR(
                f"V5 fetch error for {url}: {e}"
            ))
            return None

    def wait_for_recaptcha(self):
        """Shows the browser and waits for the user to solve a CAPTCHA."""
        self.command.stdout.write(self.command.style.WARNING(
            "Session blocked. Please solve the CAPTCHA in the browser window."
        ))
        self.driver.maximize_window()
        self.driver.get("https://www.coles.com.au")
        self._wait_for_ready(300)
        self.command.stdout.write(self.command.style.SUCCESS("Browser ready again."))

    def close(self):
        if self.driver:
            self.command.stdout.write("--- Closing Coles V5 browser session ---")
            self.driver.quit()
            self.driver = None

    def _wait_for_ready(self, timeout: int):
        WebDriverWait(self.driver, timeout, poll_frequency=2).until(
            EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
        )

    def _numeric(self, store_id: str) -> str:
        return store_id.split(':')[-1] if store_id and ':' in store_id else store_id
