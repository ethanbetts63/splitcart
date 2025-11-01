import os
import json
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from collections import defaultdict
import re
import unicodedata

# --- Primary Categories (Hardcoded) ---
PRIMARY_CATEGORIES = [
    "Fruit", "Veg", "Meat", "Seafood", "Dairy", "Eggs", "Freezer",
    "Snacks", "Pantry", "Non-Alcoholic Drinks", "Alcoholic Drinks",
    "Health and Beauty", "Cleaning", "Pet", "Baby", "Electronics",
    "Bakery", "Garden"
]

# --- Output file for mappings ---
MAPPINGS_FILE = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'category_mappings.py')

class Command(BaseCommand):
    help = 'Analyzes and helps curate category mappings to primary categories.'

    def add_arguments(self, parser):
        parser.add_argument('--company', type=str, required=True, help='The company to analyze categories for (e.g., Coles).')
        parser.add_argument('--dev', action='store_true', help='Use development server URL.')

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

    def _load_existing_mappings(self):
        if not os.path.exists(MAPPINGS_FILE):
            return {}
        
        with open(MAPPINGS_FILE, 'r') as f:
            content = f.read()
            # Safely evaluate the dictionary from the file
            mappings = {}
            exec(content, {'__builtins__': None}, mappings)
            return mappings.get('CATEGORY_MAPPINGS', {})

    def _save_mappings(self, mappings):
        with open(MAPPINGS_FILE, 'w') as f:
            f.write("CATEGORY_MAPPINGS = ")
            f.write(json.dumps(mappings, indent=4))

    def _clean_name_for_semantic_comparison(self, name: str) -> str:
        if not isinstance(name, str):
            return ""
        name = name.replace('&', 'and')
        name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
        name = name.lower()
        name = re.sub(r'[^a-z0-9\s]', '', name)
        return name

    def _get_product_overlap_suggestion(self, category_id: int, all_category_links: list, all_categories_dict: dict, all_mappings: dict) -> tuple[str, float]:
        linked_categories = [link for link in all_category_links if link['category_a'] == category_id or link['category_b'] == category_id]
        
        for link in linked_categories:
            other_category_id = link['category_a'] if link['category_a'] != category_id else link['category_b']
            other_category = all_categories_dict.get(other_category_id)
            if other_category and other_category['company'] in all_mappings:
                mapped_primary = all_mappings[other_category['company']].get(other_category['name'])
                if mapped_primary:
                    return mapped_primary, 1.0 # Strong suggestion if linked category is already mapped
        return None, 0.0

    def _get_semantic_suggestion(self, category_name: str, primary_categories: list, model, util, torch) -> tuple[str, float]:
        """
        Get a semantic suggestion for a category based on sentence similarity.
        """
        if not category_name:
            return None, 0.0

        # Clean the category name for better comparison
        cleaned_category_name = self._clean_name_for_semantic_comparison(category_name)

        # Encode the category name and primary categories
        category_embedding = model.encode(cleaned_category_name, convert_to_tensor=True)
        primary_embeddings = model.encode(primary_categories, convert_to_tensor=True)

        # Compute cosine similarity
        cosine_scores = util.pytorch_cos_sim(category_embedding, primary_embeddings)

        # Find the best match
        best_score, best_idx = torch.max(cosine_scores, dim=1)
        best_score = best_score.item()
        best_idx = best_idx.item()

        if best_score > 0.5:  # Set a threshold for suggestions
            return primary_categories[best_idx], best_score
        else:
            return None, 0.0

    def handle(self, *args, **options):
        company_name = options['company']
        dev = options['dev']

        if dev:
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
        self.stdout.write(self.style.SUCCESS(f"--- Starting Category Analyzer for {company_name} using API at {server_url} ---"))

        try:
            from sentence_transformers import SentenceTransformer, util
            import torch
        except ImportError:
            self.stderr.write(self.style.ERROR("SentenceTransformers library not found. Please run 'pip install sentence-transformers torch'"))
            return
        model = SentenceTransformer('all-MiniLM-L6-v2')

        # Load existing mappings
        all_mappings = self._load_existing_mappings()
        company_mappings = all_mappings.get(company_name, {})

        # Fetch categories and category links
        self.stdout.write("Fetching categories with products...")
        all_categories = self._fetch_paginated_data(f"{server_url}/api/export/categories-with-products/", headers, "categories")
        print(all_categories[:5]) # Print the first 5 items for inspection
        all_categories_dict = {cat['id']: cat for cat in all_categories}

        self.stdout.write("Fetching category links...")
        all_category_links = self._fetch_paginated_data(f"{server_url}/api/export/category_links/", headers, "category links")
        
        self.stdout.write("Fetching companies...")
        all_companies = self._fetch_paginated_data(f"{server_url}/api/export/companies/", headers, "companies")

        company_id = None
        for comp in all_companies:
            if comp['name'].lower() == company_name.lower():
                company_id = comp['id']
                break

        if company_id is None:
            self.stderr.write(self.style.ERROR(f"Company '{company_name}' not found."))
            return

        # Filter categories for the current company
        company_categories = [cat for cat in all_categories if cat['company'] == company_id]

        # Determine top-level categories (for simplicity, those with no parents in the fetched data)
        # This is a basic heuristic and might need refinement based on actual data structure
        category_ids_with_parents = set()
        for cat in all_categories:
            for parent_id in cat.get('parents', []):
                category_ids_with_parents.add(parent_id)
        
        top_level_categories = [cat for cat in company_categories if cat['id'] not in category_ids_with_parents]

        # Filter out already mapped categories
        unmapped_categories = [cat for cat in top_level_categories if cat['name'] not in company_mappings]

        self.stdout.write(self.style.SUCCESS(f"Found {len(unmapped_categories)} unmapped top-level categories for {company_name}."))

        for i, category in enumerate(unmapped_categories):
            self.stdout.write(f"\n------------------------------------------------------------------")
            self.stdout.write(f"Category to Map: [{company_name}] -> [{category['name']}] (Remaining: {len(unmapped_categories) - i})")

            semantic_suggestion, semantic_score = self._get_semantic_suggestion(category['name'], PRIMARY_CATEGORIES, model, util, torch)
            overlap_suggestion, overlap_score = self._get_product_overlap_suggestion(category['id'], all_category_links, all_categories_dict, all_mappings)

            suggestion = None
            reason = ""

            if overlap_suggestion and overlap_score > 0.9: # Prioritize strong overlap suggestions
                suggestion = overlap_suggestion
                reason = f"Strong product overlap with already mapped category ('{overlap_suggestion}')"
            elif semantic_suggestion and semantic_score > 0.75: # Then consider high semantic confidence
                suggestion = semantic_suggestion
                reason = f"Semantic match with {semantic_score:.2f}% confidence"
            
            if suggestion:
                self.stdout.write(f"Suggestion: '{suggestion}' (Reason: {reason})")
            else:
                self.stdout.write("Suggestion: None (No strong suggestion)")

            self.stdout.write("\nPrimary Categories:")
            for idx, pc in enumerate(PRIMARY_CATEGORIES):
                self.stdout.write(f"{idx+1}. {pc}")
            
            while True:
                choice = input("Enter the number of the correct primary category (or 's' to skip, 'q' to quit): ").strip().lower()
                if choice == 'q':
                    self._save_mappings(all_mappings)
                    self.stdout.write(self.style.SUCCESS("Exiting analyzer. Mappings saved."))
                    return
                elif choice == 's':
                    break
                elif choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(PRIMARY_CATEGORIES):
                        selected_primary_category = PRIMARY_CATEGORIES[idx]
                        company_mappings[category['name']] = selected_primary_category
                        all_mappings[company_name] = company_mappings
                        self.stdout.write(self.style.SUCCESS(f"Mapped '{category['name']}' to '{selected_primary_category}'"))
                        break
                    else:
                        self.stdout.write(self.style.ERROR("Invalid number. Please try again."))
                else:
                    self.stdout.write(self.style.ERROR("Invalid input. Please enter a number, 's', or 'q'வுகளை."))
        
        self._save_mappings(all_mappings)
        self.stdout.write(self.style.SUCCESS("--- Category Analyzer Finished. Mappings saved. ---"))
