from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


class ColesBrowserSessionV4:
    """
    Manages a persistent Chrome session for Coles scraping.

    Fetches product data using the browser's fetch() API against Coles'
    internal _next/data JSON endpoints. These return only the pageProps JSON
    (no HTML), so responses are ~10x smaller and faster than full page loads.

    Falls back to driver.get() if the buildId has expired (Coles deployed a
    new version), refreshes the buildId, then retries.
    """

    def __init__(self, command):
        self.command = command
        self.driver = None
        self.build_id = None
        self.current_store_id = None

    def start(self, store_id: str):
        """Launches Chrome, sets the initial store, waits for CAPTCHA, extracts buildId."""
        numeric_id = self._numeric(store_id)
        self.command.stdout.write(self.command.style.SUCCESS("--- Starting Coles V4 browser session ---"))

        options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options,
        )
        self.driver.set_script_timeout(45)

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
        self.build_id = self.driver.execute_script("return window.__NEXT_DATA__.buildId")
        self.current_store_id = store_id
        self.command.stdout.write(self.command.style.SUCCESS(f"Session ready. Build ID: {self.build_id}"))

    def switch_store(self, store_id: str):
        """Updates the fulfillmentStoreId cookie and reloads to register the new store."""
        if store_id == self.current_store_id:
            return
        numeric_id = self._numeric(store_id)
        self.command.stdout.write(f"--- Switching Coles store to {store_id} ---")
        self.driver.add_cookie({"name": "fulfillmentStoreId", "value": numeric_id})
        self.driver.get("https://www.coles.com.au")
        self._wait_for_ready(60)
        self.build_id = self.driver.execute_script("return window.__NEXT_DATA__.buildId")
        self.current_store_id = store_id
        self.command.stdout.write("Store switched.")

    def fetch_browse_page(self, url: str):
        """
        Fetches a Coles browse URL using the _next/data JSON endpoint.

        Extracts the slug and page number from the browse URL, then fetches
        /_next/data/{buildId}/en/browse/{slug}.json?page={page} which returns
        only the pageProps JSON. Returns the pageProps dict directly, or None
        if blocked/failed.

        If the buildId has expired (404), refreshes it and retries once.
        """
        slug, page = self._parse_browse_url(url)
        result = self._fetch_next_data(slug, page)

        if result == 'BUILD_ID_EXPIRED':
            self.command.stdout.write(self.command.style.WARNING(
                "Build ID expired. Refreshing..."
            ))
            self._refresh_build_id()
            result = self._fetch_next_data(slug, page)

        if result == 'BUILD_ID_EXPIRED' or result is None:
            return None

        return result

    def wait_for_recaptcha(self):
        """Shows the browser and waits for the user to solve a CAPTCHA."""
        self.command.stdout.write(self.command.style.WARNING(
            "Session blocked. Please solve the CAPTCHA in the browser window."
        ))
        self.driver.maximize_window()
        self.driver.get("https://www.coles.com.au")
        self._wait_for_ready(300)
        self.build_id = self.driver.execute_script("return window.__NEXT_DATA__.buildId")
        self.command.stdout.write(self.command.style.SUCCESS("Browser ready again."))

    def close(self):
        if self.driver:
            self.command.stdout.write("--- Closing Coles V4 browser session ---")
            self.driver.quit()
            self.driver = None

    def _fetch_next_data(self, slug: str, page: int):
        """
        Fetches /_next/data/{buildId}/en/browse/{slug}.json via browser fetch().
        Returns the parsed JSON, 'BUILD_ID_EXPIRED' on 404, or None on failure.
        """
        data_url = f"https://www.coles.com.au/_next/data/{self.build_id}/en/browse/{slug}.json?page={page}"
        try:
            result = self.driver.execute_async_script("""
                var done = arguments[0];
                var url = arguments[1];
                fetch(url, {credentials: 'include', headers: {'x-nextjs-data': '1'}})
                    .then(function(r) {
                        if (r.status === 404) { done('BUILD_ID_EXPIRED'); return; }
                        if (!r.ok) { done(null); return; }
                        return r.json();
                    })
                    .then(function(data) { if (data !== undefined) done(data); })
                    .catch(function() { done(null); });
            """, data_url)
            return result
        except (TimeoutException, WebDriverException) as e:
            self.command.stderr.write(self.command.style.ERROR(f"V4 fetch error: {e}"))
            return None

    def _refresh_build_id(self):
        """Navigates to the homepage to get a fresh buildId."""
        self.driver.get("https://www.coles.com.au")
        self._wait_for_ready(60)
        self.build_id = self.driver.execute_script("return window.__NEXT_DATA__.buildId")
        self.command.stdout.write(self.command.style.SUCCESS(f"Build ID refreshed: {self.build_id}"))

    def _wait_for_ready(self, timeout: int):
        WebDriverWait(self.driver, timeout, poll_frequency=2).until(
            EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
        )

    def _parse_browse_url(self, url: str):
        """Extracts (slug, page) from a browse URL like /browse/meat-seafood?page=2."""
        parsed = urlparse(url)
        slug = parsed.path.split('/browse/')[-1].rstrip('/')
        page = int(parse_qs(parsed.query).get('page', ['1'])[0])
        return slug, page

    def _numeric(self, store_id: str) -> str:
        return store_id.split(':')[-1] if store_id and ':' in store_id else store_id
