from products.models import Product, Price
import os
import json
import itertools
import time
from decimal import Decimal
import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from math import radians, sin, cos, sqrt, asin

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

        # 1. Get all relevant product IDs directly from the database
        self.command.stdout.write("  - Getting all relevant product IDs...")
        if self.use_stale:
            # If using stale, get all product IDs that have at least one price
            product_ids = list(Price.objects.values_list('product_id', flat=True).distinct())
        else:
            # If not using stale, only get products that have a recent price
            freshness_threshold = timezone.now() - timedelta(days=7)
            product_ids = list(Price.objects.filter(
                scraped_date__gte=freshness_threshold.date()
            ).values_list('product_id', flat=True).distinct())
        
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
        output_path = os.path.join(self.outbox_dir, 'bargains.json')
        total_bargains_found = 0
        processed_products = 0
        total_products = len(prices_by_product)
        is_first_bargain = True

        try:
            with open(output_path, 'w') as f:
                f.write('[') # Start the JSON array

                for product_id, prices in prices_by_product.items():
                    processed_products += 1
                    if len(prices) < 2:
                        continue

                    for price1, price2 in itertools.combinations(prices, 2):
                        if 'id' not in price1 or 'id' not in price2 or 'store__company_id' not in price1 or 'store__company_id' not in price2:
                            continue
                        
                        # Optimization: Skip if stores are not in the same state.
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
                            
                            if 10 <= discount <= 75:
                                bargain_dict = {
                                    'product_id': product_id,
                                    'discount_percentage': discount,
                                    'cheaper_price_id': cheaper['id'],
                                    'expensive_price_id': expensive['id'],
                                    'cheaper_store_id': cheaper['store_id'],
                                    'expensive_store_id': expensive['store_id'],
                                }
                                
                                if not is_first_bargain:
                                    f.write(',')
                                f.write('\n') # Add newline for readability
                                json.dump(bargain_dict, f)
                                is_first_bargain = False
                                total_bargains_found += 1
                    
                    if processed_products % 500 == 0 or processed_products == total_products:
                        self.command.stdout.write(f"\r    - Processed {processed_products}/{total_products} products...", ending="")

                f.write('\n]') # End the JSON array

            self.command.stdout.write(f"\r    - Processed {total_products}/{total_products} products. Done.                 ")
            self.command.stdout.write(f"    - Found and wrote {total_bargains_found} total bargains to {output_path}.")

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"\nAn error occurred during bargain calculation and writing: {e}"))
            # Clean up partially written file if an error occurs
            if os.path.exists(output_path):
                os.remove(output_path)
            raise

        self.command.stdout.write(self.command.style.SUCCESS("--- New Bargain Generation Complete ---"))
