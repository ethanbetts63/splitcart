import re
from collections import defaultdict
from django.core.management.base import BaseCommand
from products.models import Product
import os

def advanced_normalize_name(name):
    """
    Normalizes a product name with advanced rules.
    """
    if not name:
        return ''
    common_words = [
        'pack', 'each', 'pk', 'pce', 'pc', 'g', 'kg', 'ml', 'l', 'box', 'bunch',
        'bag', 'punnet', 'set', 'of', 'the', 'and', 'a', 'for', 'in', 'with'
    ]
    name = name.lower()
    name = ' '.join([word for word in name.split() if word not in common_words])
    # name = re.sub(r'\d+', '', name) # Removed to keep numbers
    name = re.sub(r'[^\w\s]', '', name)
    tokens = sorted(name.split())
    return ' '.join(tokens)

def title_word_similarity(name1, name2):
    """
    Calculates the percentage of shared words between two titles.
    """
    words1 = set(name1.lower().split())
    words2 = set(name2.lower().split())
    if not words1 or not words2:
        return 0.0
    shared_words = words1.intersection(words2)
    all_words = words1.union(words2)
    return (len(shared_words) / len(all_words)) * 100 if all_words else 0.0

def format_group_output(writer, group_type, criteria, products, similarity=None):
    """Formats the output for a group of duplicate products."""
    writer.write(f'\n' + '='*60 + '\n')
    writer.write(f'** {group_type.upper()} MATCH **\n')
    writer.write(f'Criteria: {criteria}\n')
    if similarity is not None:
        writer.write(f'Similarity: {similarity:.2f}%\n')
    writer.write(f'----------------------------------------\n')
    for p in products:
        stores_info = ", ".join(sorted(list(set([price.store.store_name for price in p.prices.all()]))))
        writer.write(f"  - ID: {p.id:<5} | Brand: {p.brand:<20} | Name: {p.name:<50} | Size: {p.size:<15} | Stores: {stores_info}\n")
    writer.write(f'='*60+'\n')

class Command(BaseCommand):
    help = 'Finds advanced fuzzy duplicates and outputs them to a file or console.'

    def handle(self, *args, **options):
        output_file_path = r"C:\Users\ethan\coding\splitcart\splitcart.txt"
        writer = open(output_file_path, 'w')
        
        try:
            self._execute(writer)
        finally:
            writer.close()

    def _execute(self, writer):
        writer.write('--- Starting advanced fuzzy duplicate detection ---\n')

        products_by_brand_size = defaultdict(list)
        for product in Product.objects.select_related('prices__store').all():
            brand = product.brand.lower().strip() if product.brand else ''
            size = product.size.lower().strip() if product.size else ''
            products_by_brand_size[(brand, size)].append(product)

        # Phase 1: Direct Matches
        writer.write('\n--- Phase 1: Finding direct matches based on advanced normalization ---\n')
        direct_match_groups = 0
        processed_ids = set()

        for (brand, size), products in products_by_brand_size.items():
            if len(products) < 2:
                continue
            
            normalized_groups = defaultdict(list)
            for p in products:
                normalized_name = advanced_normalize_name(p.name)
                normalized_groups[normalized_name].append(p)

            for normalized_name, group in normalized_groups.items():
                if len(group) > 1:
                    direct_match_groups += 1
                    criteria = f"Brand='{brand}', Size='{size}', Normalized='{normalized_name}'"
                    format_group_output(writer, 'Direct', criteria, group)
                    for p in group:
                        processed_ids.add(p.id)
        
        writer.write(f'--- Phase 1 complete. Found {direct_match_groups} direct match groups. ---\n')

        # Phase 2: Similarity Matching
        writer.write('\n--- Phase 2: Finding similarity matches for remaining products (>75%) ---\n')
        similarity_match_groups = 0
        
        for (brand, size), products in products_by_brand_size.items():
            remaining_products = [p for p in products if p.id not in processed_ids]
            if len(remaining_products) < 2:
                continue

            # Group similar products together
            for i in range(len(remaining_products)):
                p1 = remaining_products[i]
                if p1.id in processed_ids: continue

                # Find all products similar to p1
                similar_group = [p1]
                for j in range(i + 1, len(remaining_products)):
                    p2 = remaining_products[j]
                    if p2.id in processed_ids: continue
                    
                    similarity = title_word_similarity(p1.name, p2.name)
                    if similarity > 75:
                        similar_group.append(p2)

                if len(similar_group) > 1:
                    similarity_match_groups += 1
                    # Mark all in this group as processed to avoid re-matching
                    for p in similar_group:
                        processed_ids.add(p.id)
                    
                    criteria = f"Brand='{brand}', Size='{size}"
                    # For display, we show the similarity of the first item to the rest
                    # A more complex logic could show pair-wise similarity
                    base_name = similar_group[0].name
                    avg_similarity = sum(title_word_similarity(base_name, p.name) for p in similar_group[1:]) / (len(similar_group) -1)

                    format_group_output(writer, 'Similarity', criteria, similar_group, similarity=avg_similarity)

        writer.write(f'--- Phase 2 complete. Found {similarity_match_groups} similarity match groups. ---\n')
        writer.write('\n--- Advanced fuzzy duplicate detection finished. ---\n')
