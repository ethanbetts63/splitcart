import csv
import re
from itertools import combinations
from django.core.management.base import BaseCommand
from products.models import Product
from thefuzz import fuzz

class Command(BaseCommand):
    help = 'Finds and exports brand names with high similarity scores.'

    # Define the list of generic/unmatchable brands
    BRAND_STOP_LIST = set([
        'tea', 'real', 'quick', 'power', 'duck', 'chicken', 'dog', 'cookie',
        'black', 'bio', 'bakers', 'aussie', 'australian', 'organic', 'wild',
        'simply', 'royal', 'ocean', 'natural', 'mini', 'la', 'love', 'lolly',
        'just', 'hemp', 'harvest', 'gold', 'double', 'classic', 'baby',
        'queen', 'king', 'milk', 'margaret', 'kids', 'gourmet', 'golden',
        'fresh', 'fine', 'dine', 'byron bay', 'organic', 'everyday', 'every day',
        'deluxe', 'daily', 'cottage', 'classic', 'clean', 'chefs', 'chef',
        'casa', 'cafe', 'butter', 'bush', 'kids', 'home', 'healthy', 'health',
        'garden', 'farm', 'farmer', 'family', 'essentials', 'essence', 'everyday',
        'fancy', 'fresh', 'free', 'la', 'local', 'love', 'lunch', 'lunchbox',
        'lifestyle', 'lite', 'little', 'lolly', 'long', 'dog', 'national'
        # Primary and secondary colors
        'red', 'yellow', 'blue', 'green', 'orange', 'purple',
    ])

    def handle(self, *args, **options):
        self.stdout.write("Fetching unique brand names from products...")
        
        raw_brands = Product.objects.values_list('brand', flat=True).exclude(brand__isnull=True).exclude(brand__exact='').distinct()

        # Create a mapping from cleaned brand name to its original form
        # Filter out brands that are in the stop list
        cleaned_brand_map = {}
        for brand in raw_brands:
            # Lowercase, strip, and remove all non-alphanumeric characters except spaces
            cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', brand).lower().strip()
            
            # Skip if the cleaned brand is in the stop list
            if cleaned in self.BRAND_STOP_LIST:
                continue

            if cleaned not in cleaned_brand_map:
                cleaned_brand_map[cleaned] = brand

        unique_cleaned_brands = list(cleaned_brand_map.keys())
        
        pair_combinations = list(combinations(unique_cleaned_brands, 2))
        total_pairs = len(pair_combinations)

        self.stdout.write(f"Found {len(unique_cleaned_brands)} unique cleaned brands to compare from {len(raw_brands)} total raw brands. Comparing {total_pairs} pairs...")
        
        matches = []
        threshold = 85

        for i, (brand1_cleaned, brand2_cleaned) in enumerate(pair_combinations):
            score = fuzz.token_set_ratio(brand1_cleaned, brand2_cleaned)
            if score >= threshold:
                # Get original brand names back for reporting
                brand1_original = cleaned_brand_map[brand1_cleaned]
                brand2_original = cleaned_brand_map[brand2_cleaned]

                # Fetch one example product for each brand to provide context
                product1 = Product.objects.filter(brand=brand1_original).first()
                product2 = Product.objects.filter(brand=brand2_original).first()
                
                example_product1_name = product1.name if product1 else "N/A"
                example_product2_name = product2.name if product2 else "N/A"
                
                matches.append((brand1_original, example_product1_name, brand2_original, example_product2_name, score))
            
            # Update progress on the same line
            self.stdout.write(f'  Processed {i + 1}/{total_pairs} pairs...', ending='\r')

        self.stdout.write("") # Newline after progress bar finishes
        
        self.stdout.write(f"Found {len(matches)} potential matches.")
        
        if not matches:
            self.stdout.write("No close matches found above the threshold.")
            return

        matches.sort(key=lambda x: x[4], reverse=True) # Sort by score
        
        output_filename = 'brand_matches.csv'
        
        try:
            with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['brand_1', 'example_product_1', 'brand_2', 'example_product_2', 'similarity_score'])
                for match in matches:
                    writer.writerow(match)
            
            self.stdout.write(self.style.SUCCESS(f"Successfully wrote {len(matches)} matches to {output_filename}"))
        except IOError as e:
            self.stderr.write(self.style.ERROR(f"Error writing to file {output_filename}: {e}"))

