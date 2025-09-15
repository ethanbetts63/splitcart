import re
import unicodedata
from itertools import combinations
from collections import defaultdict
from companies.models import Category, CategoryLink

class ExactCategoryMatcher:
    def __init__(self, command):
        self.command = command
        self.links_created = 0

    def _clean_value(self, value: str) -> str:
        """ Normalizes a category name for exact matching. """
        if not isinstance(value, str):
            return ""
        value = value.replace('&', 'and') # Replace & with and
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf-8')
        value = value.lower()
        value = re.sub(r'[^a-z0-9\s]', '', value)
        
        # Remove trailing 's' from words
        words = value.split()
        processed_words = []
        for word in words:
            if word.endswith('s') and len(word) > 1: # Avoid removing 's' from single-letter words or words like 'bus'
                processed_words.append(word[:-1])
            else:
                processed_words.append(word)
        
        words = sorted(list(set(processed_words))) # Use processed_words here
        return "".join(words)

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("--- Running Automatic Category Linker ---"))
        
        # 1. Fetch all categories and prepare data structures
        all_categories = list(Category.objects.all().prefetch_related('company', 'products'))
        cleaned_groups = defaultdict(list)
        for category in all_categories:
            cleaned_name = self._clean_value(category.name)
            if cleaned_name:
                cleaned_groups[cleaned_name].append(category)

        # --- Stage 1: Create 'MATCH' links using Semantic Similarity ---
        self.command.stdout.write("--- Finding 'MATCH' links based on semantic name similarity (>=75%) ---")
        
        try:
            from sentence_transformers import SentenceTransformer, util
            import torch
        except ImportError:
            self.command.stderr.write(self.command.style.ERROR("SentenceTransformers library not found. Please run 'pip install sentence-transformers torch'"))
            return

        # Load model
        model_name = 'all-MiniLM-L6-v2'
        self.command.stdout.write(f"  Loading Sentence Transformer model: {model_name}...")
        model = SentenceTransformer(model_name)
        self.command.stdout.write("  Model loaded successfully.")

        similarity_threshold = 0.75

        # Prepare corpus of category names
        category_list = all_categories
        corpus = [cat.name for cat in category_list]
        corpus_embeddings = model.encode(corpus, convert_to_tensor=True)

        # Calculate cosine similarity
        cosine_scores = util.cos_sim(corpus_embeddings, corpus_embeddings)
        
        # Find pairs above threshold
        indices_rows, indices_cols = torch.where(cosine_scores > similarity_threshold)

        # Get existing links to avoid duplication
        existing_links = set()
        for link in CategoryLink.objects.all():
            existing_links.add(tuple(sorted((link.category_a_id, link.category_b_id))))

        match_links_to_create = []
        for idx_a, idx_b in zip(indices_rows, indices_cols):
            idx_a = idx_a.item()
            idx_b = idx_b.item()

            if idx_a >= idx_b:
                continue

            cat_a = category_list[idx_a]
            cat_b = category_list[idx_b]

            # Ensure they are from different companies
            if cat_a.company_id == cat_b.company_id:
                continue
            
            # Check if a link (of any type) already exists
            if tuple(sorted((cat_a.id, cat_b.id))) in existing_links:
                continue

            # This is a new potential MATCH link
            match_links_to_create.append(
                CategoryLink(category_a=cat_a, category_b=cat_b, link_type='MATCH')
            )
        
        # Create new MATCH links and report accurately
        new_matches_created = 0
        if match_links_to_create:
            self.command.stdout.write(f"  Found {len(match_links_to_create)} potential 'MATCH' links.")
            try:
                count_before = CategoryLink.objects.count()
                CategoryLink.objects.bulk_create(match_links_to_create, ignore_conflicts=True)
                count_after = CategoryLink.objects.count()
                new_matches_created = count_after - count_before
                self.links_created += new_matches_created
                if new_matches_created > 0:
                    self.command.stdout.write(self.command.style.SUCCESS(f"  Created {new_matches_created} new 'MATCH' links."))
                else:
                    self.command.stdout.write("  No new 'MATCH' links created (all potential links already exist).")
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"  Error bulk creating MATCH links: {e}"))
        else:
            self.command.stdout.write("  No potential 'MATCH' links found.")


        # --- Stage 2: Create 'CLOSE' and 'DISTANT' links ---
        self.command.stdout.write("--- Finding 'CLOSE'/'DISTANT' links based on Jaccard similarity ---")
        
        # Prepare data for Jaccard
        product_sets = {cat.id: set(p.id for p in cat.products.all()) for cat in all_categories}
        categories_by_company = defaultdict(list)
        for cat in all_categories: categories_by_company[cat.company.name].append(cat)

        # Get all links that now exist in the DB (including newly created MATCH links)
        existing_links = set()
        for link in CategoryLink.objects.all():
            existing_links.add(tuple(sorted((link.category_a_id, link.category_b_id))))

        # Find potential CLOSE and DISTANT links
        close_distant_links_to_create = []
        company_names = list(categories_by_company.keys())

        for company1_name, company2_name in combinations(company_names, 2):
            for cat1 in categories_by_company[company1_name]:
                for cat2 in categories_by_company[company2_name]:
                    sorted_cat_ids = tuple(sorted((cat1.id, cat2.id)))
                    if sorted_cat_ids in existing_links:
                        continue

                    set1 = product_sets.get(cat1.id, set())
                    set2 = product_sets.get(cat2.id, set())

                    if not set1 or not set2: continue
                    intersection_size = len(set1.intersection(set2))
                    if intersection_size == 0: continue

                    union_size = len(set1.union(set2))
                    jaccard_similarity = intersection_size / union_size if union_size > 0 else 0

                    link_type = None
                    if jaccard_similarity >= 0.80: link_type = 'CLOSE'
                    elif jaccard_similarity >= 0.60: link_type = 'DISTANT'
                    
                    if link_type:
                        close_distant_links_to_create.append(
                            CategoryLink(category_a=cat1, category_b=cat2, link_type=link_type)
                        )
        
        # Create new CLOSE/DISTANT links and report accurately
        new_close_created = 0
        new_distant_created = 0
        if close_distant_links_to_create:
            potential_close = sum(1 for link in close_distant_links_to_create if link.link_type == 'CLOSE')
            potential_distant = sum(1 for link in close_distant_links_to_create if link.link_type == 'DISTANT')
            self.command.stdout.write(f"  Found {potential_close} potential 'CLOSE' links.")
            self.command.stdout.write(f"  Found {potential_distant} potential 'DISTANT' links.")

            try:
                # We can't easily get separate counts for new CLOSE vs DISTANT links with one bulk_create
                # So we do it in two passes. It's less efficient but gives correct output.
                close_links = [l for l in close_distant_links_to_create if l.link_type == 'CLOSE']
                distant_links = [l for l in close_distant_links_to_create if l.link_type == 'DISTANT']

                if close_links:
                    count_before = CategoryLink.objects.count()
                    CategoryLink.objects.bulk_create(close_links, ignore_conflicts=True)
                    count_after = CategoryLink.objects.count()
                    new_close_created = count_after - count_before
                    self.links_created += new_close_created
                    if new_close_created > 0:
                        self.command.stdout.write(self.command.style.SUCCESS(f"  Created {new_close_created} new 'CLOSE' links."))

                if distant_links:
                    count_before = CategoryLink.objects.count()
                    CategoryLink.objects.bulk_create(distant_links, ignore_conflicts=True)
                    count_after = CategoryLink.objects.count()
                    new_distant_created = count_after - count_before
                    self.links_created += new_distant_created
                    if new_distant_created > 0:
                        self.command.stdout.write(self.command.style.SUCCESS(f"  Created {new_distant_created} new 'DISTANT' links."))
                
                if new_close_created == 0 and new_distant_created == 0:
                    self.command.stdout.write("  No new 'CLOSE' or 'DISTANT' links created (all potential links already exist).")

            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"  Error bulk creating CLOSE/DISTANT links: {e}"))
        else:
            self.command.stdout.write("  No potential 'CLOSE' or 'DISTANT' links found.")

        # --- Final Summary ---
        self.command.stdout.write("--- Summary ---")
        if self.links_created == 0:
            self.command.stdout.write("No new automatic links were created in this run.")
        else:
            self.command.stdout.write(self.command.style.SUCCESS(f"Total new automatic links created: {self.links_created}"))
