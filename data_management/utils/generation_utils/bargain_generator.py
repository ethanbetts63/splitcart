import os
import json
import itertools
from decimal import Decimal
import requests
from django.conf import settings

class BargainGenerator:
    """
    Finds all viable bargain combinations between store prices for every product
    by fetching data from the API and exports them to a JSON file.
    """
    def __init__(self, command, dev=False, use_stale=False):
        self.command = command
        self.dev = dev
        self.use_stale = use_stale
        self.outbox_dir = 'data_management/data/outboxes/bargains_outbox'
        os.makedirs(self.outbox_dir, exist_ok=True)

    def run(self):
        """
        Orchestrates the entire bargain generation process.
        """
        self.command.stdout.write(self.command.style.SUCCESS("--- Starting New Bargain Generation (Bulk PK Lookup) ---"))
        
        # Set up server URL and API key based on dev flag
        if self.dev:
            server_url = "http://127.0.0.1:8000"
            api_key = settings.INTERNAL_API_KEY
        else:
            try:
                server_url = settings.API_SERVER_URL
                api_key = settings.INTERNAL_API_KEY
            except AttributeError:
                self.command.stderr.write("API_SERVER_URL and INTERNAL_API_KEY must be set in settings.")
                return
        
        headers = {'X-Internal-API-Key': api_key, 'Content-Type': 'application/json'}
        self.command.stdout.write(f"  - Targeting API server at {server_url}")

        # 1. Get all product IDs from the API
        self.command.stdout.write("  - Getting all product IDs from API...")
        product_ids = []
        products_url = f"{server_url}/api/export/products/"
        page_num = 1

        while products_url:
            self.command.stdout.write(f"\r    - Fetching product ID page {page_num}...", ending="")
            try:
                response = requests.get(products_url, headers=headers, timeout=60)
                response.raise_for_status()
                data = response.json()
                product_ids.extend([p['id'] for p in data.get('results', [])])
                products_url = data.get('next')  # Get URL for the next page
                page_num += 1
            except requests.exceptions.RequestException as e:
                self.command.stderr.write(self.command.style.ERROR(f"\nError fetching products from {products_url}: {e}"))
                return
        
        self.command.stdout.write("\n")
        
        if not product_ids:
            self.command.stdout.write(self.command.style.WARNING("  - No relevant products found. Nothing to do."))
            return
        
        self.command.stdout.write(f"  - Found {len(product_ids)} products to process.")

        # 2. Fetch all prices for these products in chunks via the new bulk API
        all_prices = []
        chunk_size = 2500
        prices_url = f"{server_url}/api/internal/prices-for-products/"

        self.command.stdout.write(f"  - Fetching prices from API in chunks of {chunk_size} product IDs...")
        for i in range(0, len(product_ids), chunk_size):
            chunk_of_ids = product_ids[i:i + chunk_size]
            self.command.stdout.write(f"\r    - Fetching chunk {i // chunk_size + 1}/{(len(product_ids) // chunk_size) + 1}...", ending="")
            
            try:
                response = requests.post(prices_url, headers=headers, json={'product_ids': chunk_of_ids}, timeout=120)
                response.raise_for_status()
                all_prices.extend(response.json())
            except requests.exceptions.RequestException as e:
                self.command.stderr.write(self.command.style.ERROR(f"\nAborting due to failure in price fetching for chunk starting with product ID {chunk_of_ids[0]}: {e}"))
                return

        self.command.stdout.write(f"\n  - Total prices fetched across all chunks: {len(all_prices)}.")

        # 3. Fetch company data (this is small, so original method is fine)
        self.command.stdout.write("  - Fetching companies to identify IGA...")
        companies_url = f"{server_url}/api/export/companies/"
        try:
            response = requests.get(companies_url, headers=headers, timeout=60)
            response.raise_for_status()
            all_companies = response.json().get('results', [])
        except requests.exceptions.RequestException as e:
            self.command.stderr.write(self.command.style.ERROR(f"\nError fetching data from {companies_url}: {e}"))
            return
        
        try:
            iga_company_id = next(c['id'] for c in all_companies if c['name'].upper() == 'IGA')
            self.command.stdout.write(f"    - Identified IGA with company ID: {iga_company_id}")
        except StopIteration:
            self.command.stdout.write(self.command.style.WARNING("  - Could not find company 'IGA' via API. No special intra-company logic will be applied."))
            iga_company_id = None

        # Group prices by product
        self.command.stdout.write("  - Grouping prices by product...")
        prices_by_product = {}
        for price_data in all_prices:
            product_id = price_data['product_id']
            if product_id not in prices_by_product:
                prices_by_product[product_id] = []
            prices_by_product[product_id].append(price_data)
        self.command.stdout.write(f"    - Grouped prices for {len(prices_by_product)} unique products.")

        # Filter out products that don't have prices from at least two companies
        self.command.stdout.write("  - Filtering products for multiple company presence...")
        products_with_multiple_companies = {}
        for product_id, prices in prices_by_product.items():
            # Get unique company IDs for the current product's prices
            if not prices: continue
            companies = {price['store__company_id'] for price in prices if 'store__company_id' in price}
            if len(companies) >= 2:
                products_with_multiple_companies[product_id] = prices
        
        self.command.stdout.write(f"    - Found {len(products_with_multiple_companies)} products with multi-company prices (out of {len(prices_by_product)} total).")
        prices_by_product = products_with_multiple_companies

        # Calculate all viable bargain combinations and stream to file
        self.command.stdout.write("  - Calculating and streaming viable inter-company bargain combinations...")
        
        total_bargains_found = 0
        processed_products = 0
        total_products = len(prices_by_product)
        
        # File splitting variables
        file_counter = 1
        bargains_in_current_file = 0
        MAX_BARGAINS_PER_FILE = 1_000_000
        current_file_handle = None
        is_first_bargain_in_file = True

        def open_new_file(counter):
            nonlocal current_file_handle, is_first_bargain_in_file
            if current_file_handle:
                current_file_handle.write('\n]')
                current_file_handle.close()
            
            # Use a simple counter for subsequent files, but keep the first as `bargains.json`
            filename = 'bargains.json' if counter == 1 else f'bargains_{counter}.json'
            output_path = os.path.join(self.outbox_dir, filename)
            
            self.command.stdout.write(f"\n    - Creating new file: {output_path}")
            current_file_handle = open(output_path, 'w')
            current_file_handle.write('[')
            is_first_bargain_in_file = True
            return current_file_handle

        try:
            for product_id, prices in prices_by_product.items():
                processed_products += 1
                if len(prices) < 2:
                    continue

                for price1, price2 in itertools.combinations(prices, 2):
                    if 'id' not in price1 or 'id' not in price2 or 'store__company_id' not in price1 or 'store__company_id' not in price2:
                        continue
                    
                    if price1.get('store__state') != price2.get('store__state'):
                        continue

                    store1_id = price1['store_id']
                    store2_id = price2['store_id']
                    if store1_id == store2_id:
                        continue

                    if price1['store__company_id'] == price2['store__company_id']:
                        if iga_company_id is None or price1['store__company_id'] != iga_company_id:
                            continue

                    price1_decimal = Decimal(price1['price'])
                    price2_decimal = Decimal(price2['price'])

                    cheaper, expensive = (price1, price2) if price1_decimal < price2_decimal else (price2, price1)
                    min_price, max_price = Decimal(cheaper['price']), Decimal(expensive['price'])

                    if min_price > 0 and max_price > min_price:
                        discount = int(round(((max_price - min_price) / max_price) * 100))
                        
                        if 20 <= discount <= 70:
                            # Check if we need to create a new file
                            if current_file_handle is None or bargains_in_current_file >= MAX_BARGAINS_PER_FILE:
                                open_new_file(file_counter)
                                file_counter += 1
                                bargains_in_current_file = 0

                            bargain_dict = {
                                'product_id': product_id,
                                'discount_percentage': discount,
                                'cheaper_price_id': cheaper['id'],
                                'expensive_price_id': expensive['id'],
                                'cheaper_store_id': cheaper['store_id'],
                                'expensive_store_id': expensive['store_id'],
                            }
                            
                            if not is_first_bargain_in_file:
                                current_file_handle.write(',')
                            current_file_handle.write('\n')
                            json.dump(bargain_dict, current_file_handle)
                            
                            is_first_bargain_in_file = False
                            total_bargains_found += 1
                            bargains_in_current_file += 1
                
                if processed_products % 500 == 0 or processed_products == total_products:
                    self.command.stdout.write(f"\r    - Processed {processed_products}/{total_products} products...", ending="")

        finally:
            # Ensure the last file is properly closed
            if current_file_handle:
                current_file_handle.write('\n]')
                current_file_handle.close()

        self.command.stdout.write(f"\r    - Processed {total_products}/{total_products} products. Done.                 ")
        self.command.stdout.write(f"    - Found and wrote {total_bargains_found} total bargains to disk.")
        self.command.stdout.write(self.command.style.SUCCESS("--- New Bargain Generation Complete ---"))
