# import requests
# import json
# import re

# def scrape_gs1_company_info(barcode: str):
#     """
#     Scrapes the GS1 website to find the company name for a given barcode (GTIN).
#     This version parses the JSON response directly without BeautifulSoup.
#     """
#     print(f"--- Scraping GS1 for barcode: {barcode} ---")
    
#     url = f"https://www.gs1.org/services/verified-by-gs1/results?gtin={barcode}&ajax_form=1&_wrapper_format=drupal_ajax"
    
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
#         'X-Requested-With': 'XMLHttpRequest',
#     }

#     try:
#         response = requests.get(url, headers=headers)
#         response.raise_for_status() # Raise an exception for bad status codes
        
#         json_response = response.json()

#         # Save the full response to a file for debugging
#         with open('gs1_response.json', 'w') as f:
#             json.dump(json_response, f, indent=4)
#         print("Saved GS1 response to gs1_response.json")
        
#         company_name = None

#         # The response is a list of commands for the browser.
#         # We need to find the command that contains the settings and status message.
#         for command in json_response:
#             if command.get('command') == 'settings':
#                 status_message = command.get('settings', {}).get('gsone_verified_search', {}).get('statusMessage', '')
                
#                 # The company name is in a string like: "This number is registered to company: COMPANY NAME. ..."
#                 match = re.search(r'registered to company: (.*?)\.', status_message)
#                 if match:
#                     company_name = match.group(1).strip()
#                     break # Found it, no need to look further

#         if company_name:
#             print(f"Success! Company Name: {company_name}")
#             return company_name
#         else:
#             print("Could not find company name in the response.")
#             return None

#     except requests.exceptions.RequestException as e:
#         print(f"An error occurred during the request: {e}")
#         return None
#     except json.JSONDecodeError:
#         print("Failed to decode JSON from the response.")
#         return None

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

def scrape_gs1_with_selenium(barcode: str):
    """
    Uses Selenium to open the GS1 results page to check for CAPTCHAs or other blockers.
    """
    print(f"--- Opening GS1 page for barcode: {barcode} with Selenium ---")
    
    # The initial search page URL
    url = f"https://www.gs1.org/services/verified-by-gs1/results?gtin={barcode}"
    
    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        
        driver.get(url)
        
        print("\n--------------------------------------------------")
        print("Browser window is open. Please check for CAPTCHA or other issues.")
        print("The script will close the browser automatically in 5 minutes.")
        print("--------------------------------------------------\n")
        
        # Keep the browser open for a few minutes for inspection
        time.sleep(300)
        
        print("Closing browser.")

    except Exception as e:
        print(f"An error occurred during the Selenium process: {e}")
    finally:
        if driver:
            driver.quit()
