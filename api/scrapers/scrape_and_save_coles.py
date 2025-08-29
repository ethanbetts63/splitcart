import os
import json
import time
import math
import requests
from bs4 import BeautifulSoup
from django.utils.text import slugify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from api.utils.scraper_utils.clean_raw_data_coles import clean_raw_data_coles
from api.utils.scraper_utils.jsonl_writer import JsonlWriter
from api.utils.scraper_utils.output_utils import ScraperOutput
from api.scrapers.enrich_coles_barcodes import enrich_coles_file

def scrape_and_save_coles_data(command, company: str, store_id: str, store_name: str, state: str, categories_to_fetch: list):
    """
    Launches a browser for session setup, then uses a requests session to scrape data.
    """
    numeric_store_id = store_id.split(':')[-1] if store_id and ':' in store_id else store_id
    store_name_slug = f"{slugify(store_name)}-{numeric_store_id}"
    
    output = ScraperOutput(command, company, store_name)

    scrape_successful = False
    jsonl_writer = JsonlWriter(company, store_name_slug, state)

    driver = None
    session = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com)")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        
        driver.get("https://www.coles.com.au")
        
        driver.delete_all_cookies()
        driver.add_cookie({"name": "fulfillmentStoreId", "value": str(numeric_store_id)})
        driver.refresh()

        command.stdout.write("ACTION REQUIRED: Please solve any CAPTCHA in the browser.\n")
        command.stdout.write("Waiting for __NEXT_DATA__ script to appear (indicating main page load).\n")
        
        WebDriverWait(driver, 300, poll_frequency=2).until(
            EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
        )

        session = requests.Session()
        session.headers.update({"User-Agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)"})
        for cookie in driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])

        driver.quit()
        driver = None

    except Exception as e:
        if driver:
            driver.quit()
        command.stdout.write(f"A critical error occurred during the Selenium phase: {e}\n")
        return

    if not session:
        return

    try:
        jsonl_writer.open()
        total_categories = len(categories_to_fetch)
        output.update_progress(total_categories=total_categories)

        for i, category_slug in enumerate(categories_to_fetch):
            output.update_progress(categories_scraped=i + 1)
            page_num = 1
            total_pages = 1

            while True:
                if page_num > total_pages and total_pages > 1:
                    break

                browse_url = f"https://www.coles.com.au/browse/{category_slug}?page={page_num}"
                
                try:
                    response = session.get(browse_url, timeout=30)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, 'html.parser')
                    json_element = soup.find('script', {'id': '__NEXT_DATA__'}) 
                    
                    if not json_element:
                        break

                    full_data = json.loads(json_element.string)

                    if page_num == 1:
                        actual_store_id = full_data.get("props", {}).get("pageProps", {}).get("initStoreId")
                        if str(actual_store_id) != str(numeric_store_id):
                            break
                    
                    search_results = full_data.get("props", {}).get("pageProps", {}).get("searchResults", {})
                    raw_product_list = search_results.get("results", [])

                    if not raw_product_list:
                        break

                    if page_num == 1:
                        total_results = search_results.get("noOfResults", 0)
                        page_size = search_results.get("pageSize", 48)
                        if total_results > 0 and page_size > 0:
                            total_pages = math.ceil(total_results / page_size)

                    from datetime import datetime
                    scrape_timestamp = datetime.now()
                    data_packet = clean_raw_data_coles(raw_product_list, company, store_id, store_name, state, scrape_timestamp)
                    
                    if data_packet['products']:
                        new_products_count = 0
                        duplicate_products_count = 0
                        metadata_for_jsonl = data_packet.get('metadata', {})
                        for product in data_packet['products']:
                            if jsonl_writer.write_product(product, metadata_for_jsonl):
                                new_products_count += 1
                            else:
                                duplicate_products_count += 1
                        output.update_progress(new_products=new_products_count, duplicate_products=duplicate_products_count)

                except (requests.exceptions.RequestException, Exception):
                    break
                
                page_num += 1

        scrape_successful = True
    finally:
        # Close the file handle to ensure all data is written to the temp file
        jsonl_writer.close()

        if scrape_successful:
            # Get the path to the temp file we just created
            temp_file_path = jsonl_writer.temp_file_path
            
            try:
                # Automatically trigger the barcode enrichment process on this file
                command.stdout.write(command.style.SQL_FIELD(f"--- Handing over {os.path.basename(temp_file_path)} for barcode enrichment ---"))
                enrich_coles_file(temp_file_path, command)
                
                # Commit the now-enriched file to the product_inbox
                command.stdout.write(command.style.SUCCESS(f"--- Enrichment complete. Committing {os.path.basename(temp_file_path)} to inbox. ---"))
                jsonl_writer.commit()
            except InterruptedError as e:
                command.stderr.write(command.style.ERROR(f"\n{e}"))
                # Don't commit the file, the enrichment was stopped part-way through.
                # The progress is already saved in the temp file which has replaced the original.
                # The next run of the scraper will re-process this file.
                pass # Gracefully stop.
        else:
            # If the initial scrape failed, clean up the temp file
            jsonl_writer.cleanup()
            
        output.finalize()
