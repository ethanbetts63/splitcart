import requests
import json
import os
from django.core.management.base import BaseCommand
from collections import defaultdict

# Adapted Logic from ExactCategoryMatcher to work with JSON data
class LocalExactCategoryMatcher:
    def __init__(self, command, categories):
        self.command = command
        self.categories = categories

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("--- Running Offline Automatic Category Linker ---"))
        try:
            from sentence_transformers import SentenceTransformer, util
            import torch
        except ImportError:
            self.command.stderr.write(self.command.style.ERROR("SentenceTransformers library not found. Please run 'pip install sentence-transformers torch'"))
            return []

        model_name = 'all-MiniLM-L6-v2'
        model = SentenceTransformer(model_name)
        similarity_threshold = 0.75

        corpus = [cat['name'] for cat in self.categories]
        corpus_embeddings = model.encode(corpus, convert_to_tensor=True)
        cosine_scores = util.cos_sim(corpus_embeddings, corpus_embeddings)
        
        indices_rows, indices_cols = torch.where(cosine_scores > similarity_threshold)

        match_links = []
        for idx_a, idx_b in zip(indices_rows, indices_cols):
            if idx_a.item() >= idx_b.item(): continue
            cat_a = self.categories[idx_a.item()]
            cat_b = self.categories[idx_b.item()]
            if cat_a['company'] == cat_b['company']: continue
            match_links.append({'category_a': cat_a['id'], 'category_b': cat_b['id'], 'link_type': 'MATCH'})
        
        self.command.stdout.write(f"  Found {len(match_links)} potential 'MATCH' links.")
        return match_links

class Command(BaseCommand):
    help = 'Fetches category data from the server, generates semantic links, and saves them to an outbox.'

    def add_arguments(self, parser):
        parser.add_argument('--api-base-url', type=str, default='http://127.0.0.1:8000', help='The base URL of the production server API.')
        parser.add_argument('--outbox-dir', type=str, default='data_management/data/category_links_outbox', help='Directory to save the generated JSON file.')

    def handle(self, *args, **options):
        base_url = options['api_base_url']
        outbox_dir = options['outbox_dir']
        self.stdout.write(self.style.SUCCESS(f"--- Starting Category Link Generation using API at {base_url} ---"))

        # Ensure outbox directory exists
        os.makedirs(outbox_dir, exist_ok=True)

        self.stdout.write("Fetching categories from the server...")
        try:
            categories_response = requests.get(f'{base_url}/api/export/categories/')
            categories_response.raise_for_status()
            categories = categories_response.json()
            self.stdout.write(self.style.SUCCESS(f"Successfully fetched {len(categories)} categories."))
        except requests.exceptions.RequestException as e:
            self.stderr.write(self.style.ERROR(f"Failed to fetch data from the server: {e}"))
            return

        # Run Category Linking
        category_matcher = LocalExactCategoryMatcher(self, categories)
        category_links = category_matcher.run()

        # Save results to JSON file in outbox
        output_filename = os.path.join(outbox_dir, 'category_links.json')
        with open(output_filename, 'w') as f:
            json.dump(category_links, f, indent=4)
        self.stdout.write(self.style.SUCCESS(f"Saved {len(category_links)} category links to {output_filename}"))
        
        self.stdout.write(self.style.SUCCESS("--- Category Link Generation Finished ---"))