import difflib
import os
import re
import sys
from django.core.management.base import BaseCommand
from products.models.product import Product

class Command(BaseCommand):
    help = 'Finds similar brand names based on string similarity for potential merging.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--threshold',
            type=float,
            default=0.95,
            help='Similarity threshold (0.0 to 1.0) for considering brands as similar. Default is 0.95.'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='similar_brands.txt',
            help='Output file name for similar brand matches. Default is similar_brands.txt.'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print results to console instead of writing to file.'
        )

    def handle(self, *args, **options):
        threshold = options['threshold']
        output_file = options['output']
        dry_run = options['dry_run']

        self.stdout.write(f"Finding similar brands with a threshold of {threshold}...")

        # Get all unique brands (lowercased, stripped, and punctuation removed)
        all_brands_raw_products = Product.objects.values('brand', 'name', 'sizes').filter(brand__isnull=False).exclude(brand='')
        
        # Store unique brands and their first encountered example product
        unique_brands_map = {} # {normalized_brand: (raw_name, sizes_list)}
        for p_data in all_brands_raw_products:
            # Remove punctuation, then strip and lower
            cleaned_brand = re.sub(r'[^\w\s]', '', p_data['brand']).strip().lower()
            if cleaned_brand and cleaned_brand not in unique_brands_map:
                unique_brands_map[cleaned_brand] = (p_data['name'], p_data['sizes'])

        unique_brands_list = sorted(list(unique_brands_map.keys()))

        if len(unique_brands_list) < 2:
            self.stdout.write(self.style.WARNING("Not enough unique brands to compare."))
            return

        total_unique_brands = len(unique_brands_list)
        total_comparisons = (total_unique_brands * (total_unique_brands - 1)) / 2
        self.stdout.write(f"Total unique brands: {total_unique_brands}")
        self.stdout.write(f"Estimated total comparisons: {int(total_comparisons)}")
        self.stdout.write("Starting pairwise comparisons...")

        similar_pairs = []
        comparisons_made = 0
        
        for i in range(total_unique_brands):
            brand1_name = unique_brands_list[i]
            for j in range(i + 1, total_unique_brands):
                brand2_name = unique_brands_list[j]

                # Calculate similarity ratio
                s = difflib.SequenceMatcher(None, brand1_name, brand2_name)
                ratio = s.ratio()

                if ratio >= threshold:
                    # Get example product data for output
                    example_name1, example_sizes1 = unique_brands_map[brand1_name]
                    example_name2, example_sizes2 = unique_brands_map[brand2_name]
                    
                    # Format sizes list to string
                    sizes_str1 = ", ".join(example_sizes1) if example_sizes1 else "N/A"
                    sizes_str2 = ", ".join(example_sizes2) if example_sizes2 else "N/A"

                    similar_pairs.append((
                        brand1_name, brand2_name, ratio,
                        f"({example_name1}, {sizes_str1})",
                        f"({example_name2}, {sizes_str2})"
                    ))
                
                comparisons_made += 1
                if comparisons_made % 1000 == 0:
                    sys.stdout.write(f"\r  Processed {comparisons_made} comparisons...")
                    sys.stdout.flush()
        
        sys.stdout.write("\r" + " " * 50 + "\r") # Clear the line
        sys.stdout.flush()
        self.stdout.write(f"Finished {comparisons_made} comparisons.")

        if not similar_pairs:
            self.stdout.write(self.style.SUCCESS("No similar brand pairs found above the specified threshold."))
            return

        # Sort by ratio (descending) and then by brand names for consistent output
        similar_pairs.sort(key=lambda x: (-x[2], x[0], x[1]))

        if dry_run:
            self.stdout.write(self.style.SQL_FIELD("\n--- Similar Brand Pairs (Dry Run) ---"))
            for b1, b2, r, ex1, ex2 in similar_pairs:
                self.stdout.write(f"'{b1}' {ex1} vs '{b2}' {ex2}: {r:.4f}")
            self.stdout.write(self.style.SQL_FIELD("-------------------------------------"))
        else:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Similar Brand Pairs (Threshold: {threshold})\n")
                f.write("-----------------------------------------")
                for b1, b2, r, ex1, ex2 in similar_pairs:
                    f.write(f"'{b1}' {ex1} vs '{b2}' {ex2}: {r:.4f}\n")
            self.stdout.write(self.style.SUCCESS(f"Successfully wrote similar brand pairs to {output_file}"))
