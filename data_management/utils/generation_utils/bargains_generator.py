import os
import json
import requests
from django.conf import settings
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from products.models import Product

class BargainsGenerator:
    """
    Identifies products with significant price variations across all anchor stores
    and sets a `has_bargain` flag on the Product model for fast sorting.
    """
    def __init__(self, command, dev=False):
        self.command = command
        self.dev = dev

    def _fetch_paginated_data(self, url, headers, data_type):
        """Fetches all pages of data from a paginated API endpoint."""
        all_results = []
        next_url = url
        while next_url:
            response = requests.get(next_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            all_results.extend(data['results'])
            next_url = data.get('next')
            self.command.stdout.write(f"  Fetched {len(all_results)} {data_type}...", ending='\r')
        self.command.stdout.write(f"  Fetched {len(all_results)} {data_type}.")
        return all_results

    def _fetch_anchor_store_ids(self, url, headers):
        """Fetches anchor store IDs from the API."""
        self.command.stdout.write("Fetching anchor stores...")
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            self.command.stderr.write(f"Failed to fetch anchor stores: {e}")
            return None

    def run(self):
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
        self.command.stdout.write(self.command.style.SUCCESS(f"--- Starting Bargain Flag Generation using API at {server_url} ---"))

        # Step 1: Reset all existing flags
        self.command.stdout.write("  - Resetting all `has_bargain` flags to False...")
        num_reset = Product.objects.all().update(has_bargain=False)
        self.command.stdout.write(f"  - Reset {num_reset} products.")

        # Step 2: Fetch anchor stores and all their prices
        anchor_store_ids = self._fetch_anchor_store_ids(f"{server_url}/api/export/anchor-stores/", headers)
        if anchor_store_ids is None:
            return

        try:
            store_ids_str = ','.join(map(str, anchor_store_ids))
            freshness_threshold = timezone.now() - timedelta(days=7)
            prices_url = f"{server_url}/api/export/prices/?store_ids={store_ids_str}&scraped_date_gte={freshness_threshold.date().isoformat()}"
            prices = self._fetch_paginated_data(prices_url, headers, "prices")
        except requests.exceptions.RequestException as e:
            self.command.stderr.write(f"Failed to fetch price data: {e}"); return

        # Step 3: Process prices to find bargains
        self.command.stdout.write("  - Grouping prices by product...")
        prices_by_product = {}
        for price in prices:
            if price['product_id'] not in prices_by_product:
                prices_by_product[price['product_id']] = []
            prices_by_product[price['product_id']].append(price)

        self.command.stdout.write("  - Identifying products with bargain-level discounts...")
        product_ids_to_flag = []
        for product_id, product_prices in prices_by_product.items():
            # We need prices from at least two different stores to compare
            if len(product_prices) < 2:
                continue

            min_price = Decimal(min(p['price'] for p in product_prices))
            max_price = Decimal(max(p['price'] for p in product_prices))

            if min_price > 0 and max_price > min_price:
                discount_percentage = round(((max_price - min_price) / max_price) * 100)
                
                # New rule: Discount between 10% and 75%
                if 10 <= discount_percentage <= 75:
                    product_ids_to_flag.append(product_id)
        
        self.command.stdout.write(f"  - Found {len(product_ids_to_flag)} products to flag as bargains.")

        # Step 4: Bulk update the products that are bargains
        if product_ids_to_flag:
            self.command.stdout.write("  - Updating `has_bargain` flag in the database...")
            updated_count = Product.objects.filter(id__in=product_ids_to_flag).update(has_bargain=True)
            self.command.stdout.write(f"  - Successfully flagged {updated_count} products.")

        self.command.stdout.write(self.command.style.SUCCESS("--- Bargain Flag Generation Complete ---"))
