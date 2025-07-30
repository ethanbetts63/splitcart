import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from typing import Tuple, List, Dict

def get_coles_session_details() -> Tuple[str | None, List[Dict]]:
    """
    Launches a stealth-configured browser to visit the Coles homepage, bypasses
    security, and retrieves the site's current buildId and session cookies.

    Returns:
        A tuple containing:
        - The buildId string (or None if not found).
        - A list of cookie dictionaries (or an empty list).
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    build_id = None
    cookies = []
    try:
        # Go to the main homepage as you suggested.
        driver.get("https://www.coles.com.au/")
        time.sleep(10) # Wait for anti-bot checks to pass.
        
        # 1. Get the Build ID from the page source using the pattern you found.
        page_source = driver.page_source
        match = re.search(r'"buildId":"([^"]+)"', page_source)
        if match:
            build_id = match.group(1)
            
        # 2. Get the cookies from the browser session
        cookies = driver.get_cookies()
            
    except Exception as e:
        print(f"An error occurred during Selenium execution: {e}")
        
    finally:
        driver.quit()
        
    return build_id, cookies

