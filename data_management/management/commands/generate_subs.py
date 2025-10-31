import json
import os
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from data_management.utils.local_substitution_generators.local_lvl1_generator import LocalLvl1SubGenerator
from data_management.utils.local_substitution_generators.local_lvl2_generator import LocalLvl2SubGenerator
from data_management.utils.local_substitution_generators.local_lvl3_generator import LocalLvl3SubGenerator
from data_management.utils.local_substitution_generators.local_lvl4_generator import LocalLvl4SubGenerator

class Command(BaseCommand):
    help = 'Generates product substitutions locally and saves them to an outbox.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dev',
            action='store_true',
            help='Use development server URL (http://127.0.0.1:8000) instead of API_SERVER_URL.'
        )

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
            self.stdout.write(f"  Fetched {len(all_results)} / {data['count']} {data_type}.")
        return all_results

    def handle(self, *args, **options):
        if options['dev']:
            server_url = "http://127.0.0.1:8000"
            api_key = settings.INTERNAL_API_KEY # Assuming INTERNAL_API_KEY is used for dev
        else:
            try:
                server_url = settings.API_SERVER_URL
                api_key = settings.INTERNAL_API_KEY
            except AttributeError:
                self.stderr.write("API_SERVER_URL and INTERNAL_API_KEY must be set in settings.")
                return

        headers = {'X-Internal-API-Key': api_key, 'Accept': 'application/json'}
        self.stdout.write(self.style.SUCCESS(f"--- Starting Substitution Generation using API at {server_url} ---"))

        # 1. Fetch all necessary data with pagination
        try:
            self.stdout.write("Fetching products...")
            products = self._fetch_paginated_data(f"{server_url}/api/export/products/", headers, "products")

            self.stdout.write("Fetching categories...")
            categories = self._fetch_paginated_data(f"{server_url}/api/export/categories/", headers, "categories")

            self.stdout.write("Fetching category links...")
            category_links = self._fetch_paginated_data(f"{server_url}/api/export/category_links/", headers, "category links")

        except requests.exceptions.RequestException as e:
            self.stderr.write(f"Failed to fetch data: {e}"); return
        except json.JSONDecodeError as e:
            self.stderr.write(f"Failed to decode JSON: {e}"); return

        # 2. Run all generators
        lvl1_subs = LocalLvl1SubGenerator().generate(self, products)
        lvl2_subs = LocalLvl2SubGenerator().generate(self, products)
        lvl3_subs = LocalLvl3SubGenerator().generate(self, products, categories)
        lvl4_subs = LocalLvl4SubGenerator().generate(self, products, category_links)

        all_subs = lvl1_subs + lvl2_subs + lvl3_subs + lvl4_subs
        self.stdout.write(self.style.SUCCESS(f"Total substitutions generated: {len(all_subs)}"))

        # 3. Save to outbox
        outbox_dir = 'data_management/data/outboxes/substitutions_outbox'
        os.makedirs(outbox_dir, exist_ok=True)
        output_path = os.path.join(outbox_dir, 'substitutions.json')
        with open(output_path, 'w') as f:
            json.dump(all_subs, f, indent=4)
        
        self.stdout.write(self.style.SUCCESS(f"Saved {len(all_subs)} substitutions to {output_path}"))
        self.stdout.write(self.style.SUCCESS("--- Substitution Generation Finished ---"))