import os
import json
import itertools
import time
from decimal import Decimal
import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

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

    def _fetch_paginated_data(self, url, headers, data_type):
        """Fetches all pages of data from a paginated API endpoint."""
        all_results = []
        next_url = url
        page_num = 1
        while next_url:
            try:
                self.command.stdout.write(f"\r    - Requesting page {page_num} from server...", ending="")
                response = requests.get(next_url, headers=headers, timeout=60)
                response.raise_for_status()
                data = response.json()
                all_results.extend(data['results'])
                next_url = data.get('next')
                self.command.stdout.write(f"\r    - Fetched page {page_num} ({len(all_results)} total {data_type})...", ending="")
                page_num += 1
                time.sleep(0.1) # Add a delay to avoid rate-limiting
            except requests.exceptions.RequestException as e:
                self.command.stderr.write(self.command.style.ERROR(f"\nError fetching data from {next_url}: {e}"))
                return None # Indicate failure
        
        self.command.stdout.write(f"\r    - Fetched {len(all_results)} total {data_type}. Done.              ")
        self.command.stdout.write("") # For a newline
        return all_results

    def run(self):
        """
        Orchestrates the entire bargain generation process.
        """
        self.command.stdout.write(self.command.style.SUCCESS("--- Starting New Bargain Generation (All Combinations via API) ---"))
        
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
        
        headers = {'X-Internal-API-Key': api_key, 'Accept': 'application/json'}
        self.command.stdout.write(f"  - Targeting API server at {server_url}")

        # Fetch prices via API, chunking by two-letter prefixes to avoid timeouts
        all_prices = []
        # All possible characters for the start of a normalized name
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
        self.command.stdout.write("  - Fetching prices from API using two-character prefixes...")

        # Create a list of two-character prefixes
        prefixes = [c1 + c2 for c1 in chars for c2 in chars]

        for prefix in prefixes:
            self.command.stdout.write(f"\n  - Fetching prices for products starting with '{prefix}'...")
            
            base_prices_url = f"{server_url}/api/export/prices/"
            
            # Build query parameters
            params = []
            if not self.use_stale:
                freshness_threshold = timezone.now() - timedelta(days=7)
                params.append(f"scraped_date_gte={freshness_threshold.date().isoformat()}")
            
            params.append(f"name_starts_with={prefix}")
            
            prices_url = f"{base_prices_url}?{'&'.join(params)}"
            
            # Fetch all pages for this character chunk
            prefix_prices = self._fetch_paginated_data(prices_url, headers, f"prices for '{prefix}'")
            
            if prefix_prices is None:
                self.command.stderr.write(self.command.style.ERROR(f"Aborting due to failure in price fetching for prefix '{prefix}'."))
                return # Abort the entire run if one chunk fails
                
            all_prices.extend(prefix_prices)

        self.command.stdout.write(f"\n  - Total prices fetched across all prefixes: {len(all_prices)}.")

        # Fetch companies to identify IGA
        self.command.stdout.write("  - Fetching companies to identify IGA...")
        companies_url = f"{server_url}/api/export/companies/"
        all_companies = self._fetch_paginated_data(companies_url, headers, "companies")
        if all_companies is None:
            self.command.stderr.write(self.command.style.ERROR("Aborting due to failure in company fetching."))
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

        # Calculate all viable bargain combinations
        self.command.stdout.write("  - Calculating all viable inter-company bargain combinations...")
        bargains_data = []
        total_products_with_bargains = 0
        processed_products = 0
        total_products = len(prices_by_product)

        for product_id, prices in prices_by_product.items():
            processed_products += 1
            if len(prices) < 2:
                continue

            has_bargain_for_this_product = False
            for price1, price2 in itertools.combinations(prices, 2):
                # Ensure we have the necessary IDs
                if 'id' not in price1 or 'id' not in price2 or 'store__company_id' not in price1 or 'store__company_id' not in price2:
                    continue
                
                # Skip if they are from the same store
                if price1['store_id'] == price2['store_id']:
                    continue

                # NEW: Skip if they are from the same company, UNLESS it's IGA
                if price1['store__company_id'] == price2['store__company_id']:
                    # If we couldn't find IGA or the company isn't IGA, skip.
                    if iga_company_id is None or price1['store__company_id'] != iga_company_id:
                        continue

                price1_decimal = Decimal(price1['price'])
                price2_decimal = Decimal(price2['price'])

                cheaper, expensive = (price1, price2) if price1_decimal < price2_decimal else (price2, price1)
                min_price, max_price = Decimal(cheaper['price']), Decimal(expensive['price'])

                if min_price > 0 and max_price > min_price:
                    discount = int(round(((max_price - min_price) / max_price) * 100))
                    
                    if 5 <= discount <= 75:
                        bargains_data.append({
                            'product_id': product_id,
                            'discount_percentage': discount,
                            'cheaper_price_id': cheaper['id'],
                            'expensive_price_id': expensive['id'],
                            'cheaper_store_id': cheaper['store_id'],
                            'expensive_store_id': expensive['store_id'],
                        })
                        has_bargain_for_this_product = True
            
            if has_bargain_for_this_product:
                total_products_with_bargains += 1
            
            if processed_products % 500 == 0 or processed_products == total_products:
                self.command.stdout.write(f"\r    - Processed {processed_products}/{total_products} products...", ending="")
        
        self.command.stdout.write(f"\r    - Processed {total_products}/{total_products} products. Done.                 ")
        self.command.stdout.write(f"    - Found {len(bargains_data)} total bargains across {total_products_with_bargains} products.")

        # Write to outbox
        output_path = os.path.join(self.outbox_dir, 'bargains.json')
        self.command.stdout.write(f"  - Writing bargain data to {output_path}...")
        with open(output_path, 'w') as f:
            json.dump(bargains_data, f)

        self.command.stdout.write(self.command.style.SUCCESS("--- New Bargain Generation Complete ---"))
