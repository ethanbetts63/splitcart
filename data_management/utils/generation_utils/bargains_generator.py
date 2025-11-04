import os
import json
import requests
from django.conf import settings
from decimal import Decimal
import time

class BargainsGenerator:
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
            self.command.stdout.write(f"  Fetched {len(all_results)} / {data['count']} {data_type}.")
            time.sleep(0.1)
        return all_results

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
        self.command.stdout.write(self.command.style.SUCCESS(f"--- Starting Bargain Generation using API at {server_url} ---"))

        try:
            self.command.stdout.write("Fetching products...")
            products = self._fetch_paginated_data(f"{server_url}/api/export/products/", headers, "products")

            self.command.stdout.write("Fetching prices...")
            prices = self._fetch_paginated_data(f"{server_url}/api/export/prices/", headers, "prices")

        except requests.exceptions.RequestException as e:
            self.command.stderr.write(f"Failed to fetch data: {e}"); return
        except json.JSONDecodeError as e:
            self.command.stderr.write(f"Failed to decode JSON: {e}"); return

        self.command.stdout.write("Processing bargains...")
        bargains_data = []
        bargain_count = 0

        products_by_id = {p['id']: p for p in products}
        prices_by_product = {}
        for price in prices:
            if price['product_id'] not in prices_by_product:
                prices_by_product[price['product_id']] = []
            prices_by_product[price['product_id']].append(price)

        for product_id, product_prices in prices_by_product.items():
            if len(product_prices) < 2:
                continue

            min_price_entry = min(product_prices, key=lambda p: Decimal(p['price']))
            max_price_entry = max(product_prices, key=lambda p: Decimal(p['price']))

            if min_price_entry['store_id'] == max_price_entry['store_id']:
                continue

            min_price = Decimal(min_price_entry['price'])
            max_price = Decimal(max_price_entry['price'])


                # what is the point of this line? 
            if min_price > 0 and max_price > (min_price * Decimal('1.5')):

                bargains_data.append({
                    'product_id': product_id,
                    'store_id': min_price_entry['store_id'],
                    'cheapest_price_record_id': min_price_entry['price_record_id'],
                    'most_expensive_price_record_id': max_price_entry['price_record_id'],
                })
                bargain_count += 1

        outbox_dir = 'data_management/data/outboxes/bargains_outbox'
        os.makedirs(outbox_dir, exist_ok=True)
        output_path = os.path.join(outbox_dir, 'bargains.json')
        with open(output_path, 'w') as f:
            json.dump(bargains_data, f, indent=4)

        self.command.stdout.write(self.command.style.SUCCESS(f"Successfully found {bargain_count} bargains and saved to {output_path}."))
