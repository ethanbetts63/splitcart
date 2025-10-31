import json
import os
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from itertools import combinations
from collections import defaultdict
import re
import unicodedata

class Command(BaseCommand):
    help = 'Generates category links locally and saves them to an outbox.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dev',
            action='store_true',
            help='Use development server URL (http://127.0.0.1:8000) instead of API_SERVER_URL.'
        )

    def _fetch_paginated_data(self, url, headers, data_type):
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

    def _clean_value(self, value: str) -> str:
        if not isinstance(value, str):
            return ""
        value = value.replace('&', 'and')
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf-8')
        value = value.lower()
        value = re.sub(r'[^a-z0-9\s]', '', value)
        words = value.split()
        processed_words = []
        for word in words:
            if word.endswith('s') and len(word) > 1:
                processed_words.append(word[:-1])
            else:
                processed_words.append(word)
        words = sorted(list(set(processed_words)))
        return "".join(words)

    def handle(self, *args, **options):
        if options['dev']:
            server_url = "http://127.0.0.1:8000"
            api_key = settings.INTERNAL_API_KEY
        else:
            try:
                server_url = settings.API_SERVER_URL
                api_key = settings.INTERNAL_API_KEY
            except AttributeError:
                self.stderr.write("API_SERVER_URL and INTERNAL_API_KEY must be set in settings.")
                return

        headers = {'X-Internal-API-Key': api_key, 'Accept': 'application/json'}
        self.stdout.write(self.style.SUCCESS(f"--- Starting Category Link Generation using API at {server_url} ---"))

        # 1. Fetch category data
        try:
            self.stdout.write("Fetching categories with products...")
            all_categories = self._fetch_paginated_data(f"{server_url}/api/export/categories-with-products/", headers, "categories")
        except requests.exceptions.RequestException as e:
            self.stderr.write(f"Failed to fetch data: {e}"); return

        # 2. Run Semantic Similarity (MATCH)
        self.stdout.write("--- Finding 'MATCH' links based on semantic name similarity (>=75%) ---")
        try:
            from sentence_transformers import SentenceTransformer, util
            import torch
        except ImportError:
            self.stderr.write(self.command.style.ERROR("SentenceTransformers library not found. Please run 'pip install sentence-transformers torch'"))
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
        
        self.stdout.write(self.style.SUCCESS(f"  Found {len(all_links)} potential 'MATCH' links."))

        # 3. Run Jaccard Similarity (CLOSE/DISTANT)
        self.stdout.write("--- Finding 'CLOSE'/'DISTANT' links based on Jaccard similarity ---")
        product_sets = {cat['id']: set(cat['product_ids']) for cat in all_categories}
        categories_by_company = defaultdict(list)
        for cat in all_categories: categories_by_company[cat['company']].append(cat)

        company_ids = list(categories_by_company.keys())
        potential_close_distant_links = 0

        for company1_id, company2_id in combinations(company_ids, 2):
            for cat1 in categories_by_company[company1_id]:
                for cat2 in categories_by_company[company2_id]:
                    link_tuple = tuple(sorted((cat1['id'], cat2['id'])))
                    if link_tuple in existing_links_check: continue

                    set1 = product_sets.get(cat1['id'], set())
                    set2 = product_sets.get(cat2['id'], set())

                    if not set1 or not set2: continue
                    intersection_size = len(set1.intersection(set2))
                    if intersection_size == 0: continue

                    union_size = len(set1.union(set2))
                    jaccard_similarity = intersection_size / union_size if union_size > 0 else 0

                    link_type = None
                    if jaccard_similarity >= 0.80: link_type = 'CLOSE'
                    elif jaccard_similarity >= 0.60: link_type = 'DISTANT'
                    
                    if link_type:
                        all_links.append({'category_a': cat1['id'], 'category_b': cat2['id'], 'link_type': link_type})
                        existing_links_check.add(link_tuple)
                        potential_close_distant_links += 1

        self.stdout.write(self.style.SUCCESS(f"  Found {potential_close_distant_links} potential 'CLOSE' or 'DISTANT' links."))

        # 4. Save to outbox
        outbox_dir = 'data_management/data/outboxes/category_links_outbox'
        os.makedirs(outbox_dir, exist_ok=True)
        output_path = os.path.join(outbox_dir, 'category_links.json')
        with open(output_path, 'w') as f:
            json.dump(all_links, f, indent=4)
        
        self.stdout.write(self.style.SUCCESS(f"Saved {len(all_links)} total potential links to {output_path}"))
        self.stdout.write(self.style.SUCCESS("--- Category Link Generation Finished ---"))
