from django.conf import settings
import time
import json
import requests
import os
from bs4 import BeautifulSoup

from api.utils.normalizer import ProductNormalizer
from api.utils.database_updating_utils.prefill_barcodes import prefill_barcodes_from_db

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def enrich_coles_file(file_path, command):
    """
    Orchestrates the enrichment of a single Coles product file.
    Handles the nested {"product": ..., "metadata": ...} structure.
    Writes back to a temp file and replaces original after each scrape.
    """
    command.stdout.write(f"\n--- Enriching file: {os.path.basename(file_path)} ---")
    
    try:
        with open(file_path, 'r') as f:
            line_list = [json.loads(line) for line in f if line.strip()]
    except (IOError, json.JSONDecodeError) as e:
        command.stderr.write(command.style.ERROR(f"  - Could not read or parse file: {e}"))
        return 0, 0

    if not line_list:
        command.stdout.write("  - File is empty. Skipping.")
        return 0, 0

    product_list = [line.get('product') for line in line_list if line.get('product')]
    if not product_list:
        command.stdout.write("  - No products found in file. Skipping.")
        return 0, 0

    # Stage 1: Prefill from Database (in memory)
    enriched_product_list = prefill_barcodes_from_db(product_list, command)
    for i, line_data in enumerate(line_list):
        if 'product' in line_data:
            line_data['product'] = enriched_product_list[i]

    # Stage 2: Web Scraping for remaining products
    lines_to_scrape_count = len([line for line in line_list if line.get('product') and not line['product'].get('barcode') and line['product'].get('url')])
    
    if lines_to_scrape_count == 0:
        command.stdout.write("  - No products require web scraping in this file.")
        with open(file_path, 'w') as f:
            for line_data in line_list:
                f.write(json.dumps(line_data) + '\n')
        return 0, 0

    command.stdout.write(f"  - Found {lines_to_scrape_count} products that require web scraping.")

    session = None
    store_id = [line.get('metadata', {}).get('store_id') for line in line_list if line.get('metadata')][0]
    if not store_id:
        command.stderr.write(command.style.ERROR("  - Cannot initialize session: store_id not found."))
        return 0, 0
    numeric_store_id = store_id.split(':')[-1] if ':' in store_id else store_id
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
        if driver: driver.quit()
        command.stderr.write(command.style.ERROR(f"A critical error occurred during Selenium phase: {e}"))
        return 0, 0

    if not session:
        command.stderr.write(command.style.ERROR("Failed to create a requests session. Aborting."))
        return 0, 0

    file_updated, file_failed = 0, 0
    temp_dir = os.path.join(settings.BASE_DIR, 'api', 'data', 'temp_inbox')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    temp_file_path = os.path.join(temp_dir, os.path.basename(file_path) + ".tmp")
    try:
        with open(temp_file_path, 'w') as temp_f:
            for i, line_data in enumerate(line_list):
                product_data = line_data.get('product')
                if product_data and not product_data.get('barcode') and product_data.get('url'):
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
                                    items = [data] if isinstance(data, dict) else data if isinstance(data, list) else []
                                    for item in items:
                                        if isinstance(item, dict):
                                            for key in ['gtin', 'gtin13', 'gtin14', 'mpn']:
                                                if key in item and item[key]: gtin = item[key]; break
                                        if gtin: break
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
                                name_part = f"    - Scraping {i+1}/{len(line_list)}: {product_data.get('name')}    ."
                                barcode_part = f" barcode: {cleaned_barcode}"
                                command.stdout.write(name_part + command.style.SUCCESS(barcode_part))
                                file_updated += 1
                            else:
                                command.stderr.write(command.style.ERROR(f"      -> Found GTIN '{gtin}' but it was invalid after cleaning."))
                                file_failed += 1
                        else:
                            command.stderr.write(command.style.ERROR("      -> Could not find GTIN using any method."))
                            file_failed += 1
                        time.sleep(1)
                    except Exception as e:
                        command.stderr.write(f"      - An error occurred: {e}")
                        file_failed += 1
                
                # Write line to temp file regardless of outcome
                temp_f.write(json.dumps(line_data) + '\n')

        # After processing all lines, replace the original file
        os.replace(temp_file_path, file_path)
        command.stdout.write(f"  - Processing complete for file. Updated: {file_updated}, Failed: {file_failed}")
        return file_updated, file_failed

    except Exception as e:
        command.stderr.write(command.style.ERROR(f"An error occurred during file writing: {e}"))
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return 0, 0