import json
import os
import requests
from django.conf import settings

class CategoryLinksGenerator:
    def __init__(self, command, dev=False):
        self.command = command
        self.dev = dev

    def _fetch_paginated_data(self, url, headers, data_type):
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
        self.command.stdout.write(self.command.style.SUCCESS(f"--- Starting Category Link Generation using API at {server_url} ---"))

        # 1. Fetch category data
        try:
            self.command.stdout.write("Fetching categories with products...")
            all_categories = self._fetch_paginated_data(f"{server_url}/api/export/categories-with-products/", headers, "categories")
        except requests.exceptions.RequestException as e:
            self.command.stderr.write(f"Failed to fetch data: {e}"); return

        # 2. Run semantic category-name similarity (MATCH)
        self.command.stdout.write("--- Finding 'MATCH' links based on semantic name similarity (>=75%) ---")
        try:
            from sentence_transformers import SentenceTransformer, util
            import torch
        except ImportError:
            self.command.stderr.write(self.command.style.ERROR("SentenceTransformers library not found. Please run 'pip install sentence-transformers torch'"))
            return

        model = SentenceTransformer('all-MiniLM-L6-v2')
        corpus = [cat['name'] for cat in all_categories]
        corpus_embeddings = model.encode(corpus, convert_to_tensor=True)
        cosine_scores = util.cos_sim(corpus_embeddings, corpus_embeddings)
        indices_rows, indices_cols = torch.where(cosine_scores > 0.75)

        all_links = []
        existing_links_check = set()

        for idx_a, idx_b in zip(indices_rows, indices_cols):
            idx_a, idx_b = idx_a.item(), idx_b.item()
            if idx_a >= idx_b: continue

            cat_a = all_categories[idx_a]
            cat_b = all_categories[idx_b]

            if cat_a['company'] == cat_b['company']: continue

            link_tuple = tuple(sorted((cat_a['id'], cat_b['id'])))
            if link_tuple in existing_links_check: continue

            all_links.append({'category_a': cat_a['id'], 'category_b': cat_b['id'], 'link_type': 'MATCH'})
            existing_links_check.add(link_tuple)
        
        self.command.stdout.write(self.command.style.SUCCESS(f"  Found {len(all_links)} potential 'MATCH' links."))

        # 3. Save to outbox
        outbox_dir = 'data_management/data/outboxes/category_links_outbox'
        os.makedirs(outbox_dir, exist_ok=True)
        output_path = os.path.join(outbox_dir, 'category_links.json')
        with open(output_path, 'w') as f:
            json.dump(all_links, f, indent=4)
        
        self.command.stdout.write(self.command.style.SUCCESS(f"Saved {len(all_links)} total potential links to {output_path}"))
        self.command.stdout.write(self.command.style.SUCCESS("--- Category Link Generation Finished ---"))
