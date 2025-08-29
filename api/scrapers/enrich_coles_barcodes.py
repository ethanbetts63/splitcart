from django.conf import settings
import time
import json
import requests
import os
import shutil
from bs4 import BeautifulSoup

from api.utils.normalizer import ProductNormalizer
from api.utils.database_updating_utils.prefill_barcodes import prefill_barcodes_from_db

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def enrich_coles_file(source_file_path, command):
    """
    Orchestrates the enrichment of a single Coles product file in a non-destructive way.
    Uses the source file as the master list and a .progress file as an append-only cache of completed items.
    """
    command.stdout.write(f"\n--- Enriching file: {os.path.basename(source_file_path)} ---")

    progress_file_path = source_file_path + ".progress"

    while True: # Main loop to handle session restarts
        # --- Step 1: Load Progress Cache ---
        found_products = {}
        if os.path.exists(progress_file_path):
            with open(progress_file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        sku = data.get('product', {}).get('product_id_store')
                        if sku:
                            found_products[sku] = data
                    except json.JSONDecodeError:
                        continue # Ignore corrupted lines in progress file

        # --- Step 2: Load Master File and Determine Work ---
        try:
            with open(source_file_path, 'r') as f:
                master_line_list = [json.loads(line) for line in f if line.strip()]
        except (IOError, json.JSONDecodeError) as e:
            command.stderr.write(command.style.ERROR(f"  - CRITICAL: Could not read source file: {e}"))
            return

        # Prefill from the main DB first
        master_product_list = [line.get('product') for line in master_line_list]
        enriched_master_list = prefill_barcodes_from_db(master_product_list, command)
        for i, line_data in enumerate(master_line_list):
            if 'product' in line_data:
                line_data['product'] = enriched_master_list[i]

        lines_to_scrape = []
        final_line_list = []
        for line_data in master_line_list:
            sku = line_data.get('product', {}).get('product_id_store')
            # If product is in our cache, use that enriched version
            if sku in found_products:
                final_line_list.append(found_products[sku])
            # Otherwise, if it needs a barcode, add to scrape list
            elif not line_data.get('product', {}).get('barcode') and line_data.get('product', {}).get('url'):
                lines_to_scrape.append(line_data)
                final_line_list.append(line_data) # Add to final list, will be updated in-memory
            # Else, it's a product that didn't need scraping in the first place (e.g. Coles brand)
            else:
                final_line_list.append(line_data)

        if not lines_to_scrape:
            command.stdout.write(command.style.SUCCESS("\n  - Enrichment 100% complete."))
            try:
                with open(source_file_path, 'w') as f:
                    for line_data in final_line_list:
                        f.write(json.dumps(line_data) + '\n')
                command.stdout.write(f"  - Final enriched file saved to: {os.path.basename(source_file_path)}")
                if os.path.exists(progress_file_path):
                    os.remove(progress_file_path)
            except (OSError, IOError) as e:
                command.stderr.write(command.style.ERROR(f"  - CRITICAL: Could not write final file or clean up: {e}"))
            break # Exit main while loop

        command.stdout.write(f"\n  - {len(lines_to_scrape)} products require web scraping.")

        # --- Step 3: Selenium Session Creation ---
        session = None
        driver = None
        try:
            store_id = [line.get('metadata', {}).get('store_id') for line in master_line_list if line.get('metadata')][0]
            numeric_store_id = store_id.split(':')[-1] if ':' in store_id else store_id
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
        except Exception as e:
            raise InterruptedError(f"A critical error occurred during the Selenium phase: {e}")
        finally:
            if driver:
                driver.quit()

        if not session:
            raise InterruptedError("Failed to create a requests session. Aborting.")

        # --- Step 4: Scrape and Append to Progress File ---
        session_interrupted = False
        consecutive_failures = 0
        
        total_to_scrape = len(lines_to_scrape)
        with open(progress_file_path, 'a') as progress_f:
            for i, line_data in enumerate(lines_to_scrape):
                product_data = line_data['product']
                try:
                    response = session.get(product_data['url'], timeout=30)
                    if '<script id="__NEXT_DATA__"' not in response.text:
                        command.stderr.write(command.style.ERROR(f"\n    - High-level block detected. Ending session."))
                        session_interrupted = True
                        break

                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    page_scrape_successful = False
                    gtin = None

                    # Try ld+json first
                    json_ld_scripts = soup.find_all('script', {'type': 'application/ld+json'})
                    for script in json_ld_scripts:
                        if script.string:
                            try:
                                data = json.loads(script.string)
                                items = [data] if isinstance(data, dict) else data if isinstance(data, list) else []
                                for item in items:
                                    if isinstance(item, dict) and item.get('@type') == 'Product':
                                        page_scrape_successful = True
                                        gtin = item.get('gtin') or item.get('gtin13') or item.get('gtin14') or item.get('mpn')
                                        break
                                if page_scrape_successful: break
                            except (json.JSONDecodeError): continue
                        if page_scrape_successful: break

                    # If not in ld+json, try __NEXT_DATA__
                    if not page_scrape_successful:
                        json_element = soup.find('script', {'id': '__NEXT_DATA__'})
                        if json_element and json_element.string:
                            page_data = json.loads(json_element.string)
                            product_json = None
                            # Try to find the product data in a few common locations
                            if page_data.get('pageProps', {}).get('product'):
                                product_json = page_data.get('pageProps', {}).get('product')
                            elif page_data.get('pageProps', {}).get('pdpLayout', {}).get('product'):
                                product_json = page_data.get('pageProps', {}).get('pdpLayout', {}).get('product')
                            
                            if product_json:
                                page_scrape_successful = True
                                gtin = product_json.get('gtin')

                    # --- Process Scrape Outcome ---
                    if page_scrape_successful:
                        consecutive_failures = 0
                        normalizer = ProductNormalizer({'barcode': str(gtin) if gtin else None, 'sku': product_data.get('sku')})
                        cleaned_barcode = normalizer.get_cleaned_barcode()
                        
                        if cleaned_barcode:
                            product_data['barcode'] = cleaned_barcode
                            command.stdout.write(command.style.SUCCESS(f"    - ({i + 1}/{total_to_scrape}) Found barcode for {product_data.get('name')}"))
                        else:
                            product_data['barcode'] = None # Mark as processed
                            command.stdout.write(f"    - ({i + 1}/{total_to_scrape}) Product has no barcode: {product_data.get('name')}")
                        
                        progress_f.write(json.dumps(line_data) + '\n')
                    else:
                        # This is a true failure - page structure is unexpected
                        consecutive_failures += 1
                        command.stderr.write(command.style.ERROR(f"    - Failed to find product data for {product_data.get('name')}"))
                        command.stderr.write(f"      -> URL: {product_data.get('url')}")
                        debug_dir = os.path.join(settings.BASE_DIR, 'debug_output')
                        if not os.path.exists(debug_dir):
                            os.makedirs(debug_dir)
                        file_name = f"coles_failure_{consecutive_failures}.html"
                        debug_file_path = os.path.join(debug_dir, file_name)
                        try:
                            with open(debug_file_path, 'w', encoding='utf-8') as f:
                                f.write(response.text)
                            command.stderr.write(f"      -> Saved failing page HTML to {debug_file_path}")
                        except Exception as write_e:
                            command.stderr.write(f"      -> Could not write debug file: {write_e}")

                    if consecutive_failures >= 15:
                        command.stderr.write(command.style.ERROR("\n    - 15 consecutive structural failures detected. Assuming block. Ending session."))
                        session_interrupted = True
                        break

                except Exception as e:
                    command.stderr.write(command.style.ERROR(f"    - Error scraping {product_data.get('name')}: {e}"))
                    continue

        if session_interrupted:
            command.stdout.write("--------------------------------------------------")
            time.sleep(2)
            continue
        else:
            command.stdout.write("  - Finished scraping batch.")
            continue
