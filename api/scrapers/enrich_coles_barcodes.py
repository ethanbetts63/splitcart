import time
import json
import requests
from bs4 import BeautifulSoup
from products.models import Product
from api.utils.normalizer import ProductNormalizer
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def fetch_and_update_coles_barcodes(command):
    """
    Finds a small batch of Coles products without a barcode and attempts to fetch the GTIN
    from the individual product page for debugging purposes.
    """
    command.stdout.write(command.style.SQL_FIELD("--- Starting Coles Barcode Enrichment Process (Batch of 3) ---"))
    
    # Find the first 3 unique products that have a price from a Coles store and have no barcode.
    products_to_enrich = Product.objects.filter(
        prices__store__company__name__iexact='Coles',
        barcode__isnull=True
    ).distinct()[:3]

    product_count = len(products_to_enrich)
    if not products_to_enrich:
        command.stdout.write("No Coles products missing a barcode were found.")
        return

    command.stdout.write(f"Found {product_count} products to test.")

    # --- Selenium Warm-up ---
    # Get a store_id for session initialization
    first_price_record = products_to_enrich[0].prices.filter(store__company__name__iexact='Coles').first()
    if not first_price_record or not first_price_record.store or not first_price_record.store.store_id:
        command.stderr.write(command.style.ERROR("Could not find a Coles price record with a store ID for session initialization."))
        return
    
    store_id = first_price_record.store.store_id
    numeric_store_id = store_id.split(':')[-1] if store_id and ':' in store_id else store_id

    driver = None
    session = None
    try:
        command.stdout.write("Initializing browser for CAPTCHA...")
        options = webdriver.ChromeOptions()
        options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com)")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        
        driver.get("https://www.coles.com.au")
        
        driver.delete_all_cookies()
        driver.add_cookie({"name": "fulfillmentStoreId", "value": str(numeric_store_id)})
        driver.refresh()

        command.stdout.write("ACTION REQUIRED: Please solve any CAPTCHA in the browser.")
        command.stdout.write("Waiting for page to load after CAPTCHA...")
        
        WebDriverWait(driver, 300, poll_frequency=2).until(
            EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
        )

        command.stdout.write("CAPTCHA solved. Creating session...")
        session = requests.Session()
        session.headers.update({"User-Agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)"})
        for cookie in driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])

        driver.quit()
        driver = None

    except Exception as e:
        if driver:
            driver.quit()
        command.stderr.write(command.style.ERROR(f"A critical error occurred during the Selenium phase: {e}"))
        return

    if not session:
        command.stderr.write(command.style.ERROR("Failed to create a requests session after Selenium warm-up."))
        return
    # --- End Selenium Warm-up ---
    
    updated_count = 0
    failed_count = 0

    for i, product in enumerate(products_to_enrich):
        command.stdout.write(f"\n--- Processing product {i+1}/{product_count}: {product.name} ---")
        
        price_record = product.prices.filter(store__company__name__iexact='Coles').first()
        sku = price_record.sku if price_record else 'Not Found'

        command.stdout.write(f"  - Brand: {product.brand}")
        command.stdout.write(f"  - Sizes: {product.sizes}")
        command.stdout.write(f"  - SKU: {sku}")
        command.stdout.write(f"  - DB URL: {product.url}")

        if not product.url:
            command.stderr.write(command.style.ERROR("  - Product has no URL. Skipping."))
            failed_count += 1
            continue

        try:
            command.stdout.write(f"  - Fetching URL: {product.url}")
            response = session.get(product.url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            gtin = None

            # 1. Try JSON-LD scripts first
            command.stdout.write("  - Attempting to find GTIN in JSON-LD script tags...")
            json_ld_scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for script in json_ld_scripts:
                if script.string:
                    try:
                        data = json.loads(script.string)
                        items_to_check = []
                        if isinstance(data, dict):
                            items_to_check.append(data)
                        elif isinstance(data, list):
                            items_to_check.extend(data)
                        
                        for item in items_to_check:
                            if isinstance(item, dict):
                                # Common keys for GTIN in schema.org
                                for key in ['gtin', 'gtin13', 'gtin14', 'mpn']:
                                    if key in item and item[key]:
                                        gtin = item[key]
                                        break
                            if gtin:
                                break
                    except (json.JSONDecodeError):
                        continue
                if gtin:
                    break
            
            if gtin:
                command.stdout.write(f"  - Found GTIN '{gtin}' in JSON-LD.")
            else:
                command.stdout.write("  - GTIN not found in JSON-LD. Falling back to __NEXT_DATA__.")
                # 2. & 3. Fallback to __NEXT_DATA__ (API or direct)
                json_element = soup.find('script', {'id': '__NEXT_DATA__'})
                if json_element and json_element.string:
                    try:
                        page_data = json.loads(json_element.string)
                        build_id = page_data.get('buildId')

                        # Try API method first
                        if build_id:
                            product_slug = product.url.split('/product/')[-1]
                            if product_slug:
                                json_url = f"https://www.coles.com.au/_next/data/{build_id}/en/product/{product_slug}.json?slug={product_slug}"
                                command.stdout.write(f"  - Found buildId, fetching JSON from API: {json_url}")
                                
                                try:
                                    json_response = session.get(json_url, timeout=30)
                                    json_response.raise_for_status()
                                    product_data = json_response.json()
                                    gtin = product_data.get('pageProps', {}).get('product', {}).get('gtin')
                                except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                                    command.stderr.write(command.style.ERROR(f"  - Failed to fetch or parse product JSON from API: {e}"))
                        
                        # 4. Fallback to direct __NEXT_DATA__ parsing
                        if not gtin:
                            command.stdout.write("  - API method failed or was skipped, falling back to parsing page data.")
                            gtin = page_data.get('pageProps', {}).get('product', {}).get('gtin')
                    except json.JSONDecodeError:
                        command.stderr.write(command.style.ERROR("  - Failed to parse __NEXT_DATA__ JSON."))
                else:
                    command.stderr.write(command.style.ERROR("  - Could not find __NEXT_DATA__ script tag on page."))

            # Now process the found gtin
            if gtin:
                normalizer = ProductNormalizer({'barcode': str(gtin), 'sku': sku})
                cleaned_barcode = normalizer.get_cleaned_barcode()

                if cleaned_barcode:
                    command.stdout.write(command.style.SUCCESS(f"  - Found and cleaned barcode: {cleaned_barcode}"))
                    product.barcode = cleaned_barcode
                    product.save(update_fields=['barcode'])
                    updated_count += 1
                else:
                    command.stderr.write(command.style.ERROR(f"  - Found GTIN '{gtin}' but it was deemed invalid after cleaning."))
                    failed_count += 1
            else:
                command.stderr.write(command.style.ERROR("  - Could not find GTIN using any method."))
                failed_count += 1

            time.sleep(1) # Be respectful to the server

        except Exception as e:
            command.stderr.write(command.style.ERROR(f"  - An error occurred: {e}"))
            failed_count += 1
            continue

    command.stdout.write(command.style.SUCCESS(f"\n--- Enrichment Complete ---"))
    command.stdout.write(f"Successfully updated {updated_count} products.")
    command.stdout.write(f"Failed to find barcodes for {failed_count} products.")