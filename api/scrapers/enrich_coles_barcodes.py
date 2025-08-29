import time
import json
import requests
import os
import glob
from bs4 import BeautifulSoup

from api.utils.normalizer import ProductNormalizer
from api.utils.database_updating_utils.prefill_barcodes import prefill_barcodes_from_db

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def enrich_coles_inbox_files(command):
    """
    Orchestrates the enrichment of Coles product data in the inbox.
    1. Prefills barcodes from the existing database.
    2. Scrapes the web for barcodes of any remaining products.
    """
    command.stdout.write(command.style.SQL_FIELD("--- Starting Coles Inbox Enrichment Process ---"))

    inbox_path = 'api/data/product_inbox/'
    coles_files = glob.glob(os.path.join(inbox_path, 'coles-*.jsonl'))

    if not coles_files:
        command.stdout.write("No Coles inbox files found to enrich.")
        return

    session = None
    updated_count_total = 0
    failed_count_total = 0

    for file_path in coles_files:
        command.stdout.write(f"\n--- Processing file: {os.path.basename(file_path)} ---")
        
        try:
            with open(file_path, 'r') as f:
                product_list = [json.loads(line) for line in f if line.strip()]
        except (IOError, json.JSONDecodeError) as e:
            command.stderr.write(command.style.ERROR(f"  - Could not read or parse file: {e}"))
            continue

        if not product_list:
            command.stdout.write("  - File is empty. Skipping.")
            continue

        # Stage 1: Prefill from Database
        product_list = prefill_barcodes_from_db(product_list, command)

        # Stage 2: Web Scraping for remaining products
        products_to_scrape = [p for p in product_list if not p.get('barcode') and p.get('url')]
        
        if not products_to_scrape:
            command.stdout.write("  - No products require web scraping in this file.")
            with open(file_path, 'w') as f:
                for product_data in product_list:
                    f.write(json.dumps(product_data) + '\n')
            continue

        command.stdout.write(f"  - Found {len(products_to_scrape)} products that require web scraping.")

        if not session:
            command.stdout.write("  - Initializing browser for CAPTCHA...")
            store_id = products_to_scrape[0].get('store_id')
            if not store_id:
                command.stderr.write(command.style.ERROR("  - Cannot initialize session: store_id not found in first product."))
                continue
            
            numeric_store_id = store_id.split(':')[-1] if store_id and ':' in store_id else store_id
            
            driver = None
            try:
                options = webdriver.ChromeOptions()
                options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com)")
                driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
                driver.get("https://www.coles.com.au")
                driver.delete_all_cookies()
                driver.add_cookie({"name": "fulfillmentStoreId", "value": str(numeric_store_id)})
                driver.refresh()
                command.stdout.write("ACTION REQUIRED: Please solve any CAPTCHA in the browser.")
                WebDriverWait(driver, 300, poll_frequency=2).until(EC.presence_of_element_located((By.ID, "__NEXT_DATA__")))
                command.stdout.write("CAPTCHA solved. Creating session...")
                session = requests.Session()
                session.headers.update({"User-Agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)"})
                for cookie in driver.get_cookies():
                    session.cookies.set(cookie['name'], cookie['value'])
                driver.quit()
            except Exception as e:
                if driver:
                    driver.quit()
                command.stderr.write(command.style.ERROR(f"A critical error occurred during the Selenium phase: {e}"))
                command.stderr.write(command.style.ERROR("Aborting web scraping for all remaining files."))
                break # Exit the file loop

        if not session:
            command.stderr.write(command.style.ERROR("Failed to create a requests session. Aborting."))
            break

        file_updated = 0
        file_failed = 0
        for i, product_data in enumerate(products_to_scrape):
            command.stdout.write(f"    - Scraping {i+1}/{len(products_to_scrape)}: {product_data.get('name')}")
            try:
                response = session.get(product_data['url'], timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                gtin = None
                json_ld_scripts = soup.find_all('script', {'type': 'application/ld+json'})
                for script in json_ld_scripts:
                    if script.string:
                        try:
                            data = json.loads(script.string)
                            items_to_check = [data] if isinstance(data, dict) else data if isinstance(data, list) else []
                            for item in items_to_check:
                                if isinstance(item, dict):
                                    for key in ['gtin', 'gtin13', 'gtin14', 'mpn']:
                                        if key in item and item[key]:
                                            gtin = item[key]
                                            break
                                if gtin:
                                    break
                        except (json.JSONDecodeError): continue
                    if gtin: break
                
                if not gtin:
                    json_element = soup.find('script', {'id': '__NEXT_DATA__'}) 
                    if json_element and json_element.string:
                        page_data = json.loads(json_element.string)
                        gtin = page_data.get('pageProps', {}).get('product', {}).get('gtin')

                if gtin:
                    normalizer = ProductNormalizer({'barcode': str(gtin), 'sku': product_data.get('sku')})
                    cleaned_barcode = normalizer.get_cleaned_barcode()
                    if cleaned_barcode:
                        product_data['barcode'] = cleaned_barcode
                        file_updated += 1
                    else:
                        file_failed += 1
                else:
                    file_failed += 1
                time.sleep(1)
            except Exception as e:
                command.stderr.write(f"      - An error occurred: {e}")
                file_failed += 1
                continue
        
        command.stdout.write(f"  - Web scraping complete for this file. Updated: {file_updated}, Failed: {file_failed}")
        updated_count_total += file_updated
        failed_count_total += file_failed

        command.stdout.write(f"  - Saving enriched data back to {os.path.basename(file_path)}")
        with open(file_path, 'w') as f:
            for p_data in product_list:
                f.write(json.dumps(p_data) + '\n')

    command.stdout.write(command.style.SUCCESS(f"\n--- Coles Inbox Enrichment Complete ---"))
    command.stdout.write(f"Successfully updated {updated_count_total} products via web scraping.")
    command.stdout.write(f"Failed to find barcodes for {failed_count_total} products.")
