import os
import json
import requests
from django.conf import settings

class StoreClustersGenerator:
    def __init__(self, command, dev=False):
        self.command = command
        self.dev = dev
        self.outbox_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'outboxes', 'store_clusters_outbox')
        self.file_name = 'store_clusters.json'

    def _fetch_paginated_data(self, url, headers, data_type):
        """Fetches all pages of data from a paginated API endpoint."""
        all_results = []
        next_url = url
        while next_url:
            try:
                response = requests.get(next_url, headers=headers)
                response.raise_for_status()
                data = response.json()
                results = data.get('results', [])
                all_results.extend(results)
                next_url = data.get('next')
                count = data.get('count', 0)
                if count > 0:
                    self.command.stdout.write(f"  Fetched {len(all_results)} / {count} {data_type}.")
                else:
                     self.command.stdout.write(f"  Fetched {len(all_results)} {data_type}.")
            except requests.exceptions.RequestException as e:
                self.command.stderr.write(f"Failed to fetch data from {next_url}: {e}")
                return None # Indicate failure
            except json.JSONDecodeError as e:
                self.command.stderr.write(f"Failed to decode JSON from {next_url}: {e}")
                return None # Indicate failure
        return all_results

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("--- Generating Store Clusters File via API ---"))
        
        if self.dev:
            server_url = "http://127.0.0.1:8000"
            api_key = getattr(settings, 'INTERNAL_API_KEY', None)
        else:
            server_url = getattr(settings, 'API_SERVER_URL', None)
            api_key = getattr(settings, 'INTERNAL_API_KEY', None)

        if not server_url or not api_key:
            self.command.stderr.write("API_SERVER_URL and INTERNAL_API_KEY must be set in settings.")
            return

        headers = {'X-Internal-API-Key': api_key, 'Accept': 'application/json'}

        # 1. Fetch all stores from the API
        self.command.stdout.write("Fetching stores from API...")
        stores_url = f"{server_url}/api/export/stores/"
        all_stores = self._fetch_paginated_data(stores_url, headers, "stores")

        if all_stores is None: # Check for fetch failure
            self.command.stderr.write(self.command.style.ERROR("Aborting due to failure in fetching store data."))
            return

        if not all_stores:
            self.command.stdout.write(self.command.style.WARNING("No stores found from the API."))
            return

        self.command.stdout.write(f"  - Found {len(all_stores)} stores to process.")
        
        # 2. Generate cluster data
        clusters_data = []
        for store in all_stores:
            cluster = {
                "company": store.get('company'),
                "stores": [store.get('id')]
            }
            clusters_data.append(cluster)

        # 3. Write the data to the JSON file
        try:
            os.makedirs(self.outbox_path, exist_ok=True)
            file_path = os.path.join(self.outbox_path, self.file_name)
            with open(file_path, 'w') as f:
                json.dump(clusters_data, f, indent=4)

            self.command.stdout.write(self.command.style.SUCCESS(f"  Successfully generated {self.file_name} with {len(clusters_data)} clusters."))

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"An error occurred while writing the file: {e}"))
            return
