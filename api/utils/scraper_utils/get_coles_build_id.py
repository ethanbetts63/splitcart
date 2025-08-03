import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def get_coles_build_id() -> str | None:
    """
    Launches a stealth-configured browser to visit coles, bypasses security,
    and retrieves the site's current buildId.

    Returns:
        The buildId string if successful, otherwise None.
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
    try:
        # Any browse page will work for finding the build ID.
        driver.get("https://www.coles.com.au/browse/fruit-vegetables")
        time.sleep(10) # Wait for anti-bot checks to pass.
        page_source = driver.page_source
        
        match = re.search(r'/_next/static/([^/]+)/_buildManifest.js', page_source)
        if match:
            build_id = match.group(1)
            
    except Exception as e:
        # In a real application, you'd want to log this error.
        print(f"An error occurred during Selenium execution: {e}")
        
    finally:
        driver.quit()
        
    return build_id

