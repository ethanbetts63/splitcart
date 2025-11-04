import numpy as np
import requests
import json
import os
from sklearn.cluster import DBSCAN
from django.conf import settings

class StoreClustersGenerator:
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
        self.command.stdout.write(self.command.style.SUCCESS(f"--- Starting Store Cluster Generation using API at {server_url} ---"))

        try:
            self.command.stdout.write("Fetching stores...")
            stores_data = self._fetch_paginated_data(f"{server_url}/api/export/stores/", headers, "stores")

        except requests.exceptions.RequestException as e:
            self.command.stderr.write(f"Failed to fetch data: {e}"); return
        except json.JSONDecodeError as e:
            self.command.stderr.write(f"Failed to decode JSON: {e}"); return

        # --- DBSCAN Parameters ---
        eps_km = 25 
        min_samples = 3
        kms_per_radian = 6371.0088
        epsilon = eps_km / kms_per_radian

        companies = list(set([store['company'] for store in stores_data]))
        all_clusters = []

        for company in companies:
            self.command.stdout.write(f"\nProcessing {company}...")

            if company.lower() == 'iga':
                self.command.stdout.write("  Applying special handling for IGA: Creating single-store clusters.")
                iga_stores = [s for s in stores_data if s['company'] == company]
                for store in iga_stores:
                    all_clusters.append({
                        'company': company,
                        'stores': [store['id']]
                    })
                self.command.stdout.write(f"  Result: Created {len(iga_stores)} single-store clusters.")
                continue

            stores = [s for s in stores_data if s['company'] == company and s['latitude'] is not None and s['longitude'] is not None]

            if len(stores) < min_samples:
                self.command.stdout.write(f"Skipping {company}, not enough stores ({len(stores)}) to form clusters.")
                continue

            coords = np.array([[float(s['latitude']), float(s['longitude'])] for s in stores])
            
            db = DBSCAN(
                eps=epsilon, 
                min_samples=min_samples, 
                algorithm='ball_tree', 
                metric='haversine'
            ).fit(np.radians(coords))

            labels = db.labels_
            unique_labels = set(labels) - {-1}

            for label in unique_labels:
                cluster_stores = [stores[i]['id'] for i, store_label in enumerate(labels) if store_label == label]
                all_clusters.append({
                    'company': company,
                    'stores': cluster_stores
                })

            num_outliers = np.sum(labels == -1)
            self.command.stdout.write(f"  Result: Found {len(unique_labels)} clusters and {num_outliers} outliers.")

        outbox_dir = 'data_management/data/outboxes/store_clusters_outbox'
        os.makedirs(outbox_dir, exist_ok=True)
        output_path = os.path.join(outbox_dir, 'store_clusters.json')
        with open(output_path, 'w') as f:
            json.dump(all_clusters, f, indent=4)

        self.command.stdout.write(self.command.style.SUCCESS(f"Successfully generated {len(all_clusters)} store clusters and saved to {output_path}."))
