from django.core.management.base import BaseCommand
from django.db import transaction
from products.models import Product, Price
from companies.models import Category
from collections import defaultdict
import re
import sys

class Command(BaseCommand):
    help = 'Updates all products and merges duplicates based on normalized_name_brand_size.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate the merge process without making changes to the database.'
        )

    def _clean_value(self, value):
        if value is None:
            return ''
        # Split into words, sort them, and join back
        words = sorted(str(value).lower().split())
        sorted_string = ' '.join(words)
        # Remove non-alphanumeric characters and spaces
        cleaned_value = re.sub(r'[^a-z0-9]', '', sorted_string)
        return cleaned_value

    def _get_cleaned_name(self, product):
        name = product.name
        # Remove brand
        if product.brand and product.brand.lower() in name.lower():
            name = re.sub(r'\b' + re.escape(product.brand) + r'\b', '', name, flags=re.IGNORECASE).strip()
        
        # Remove sizes
        if product.sizes:
            # Define unit variations
            units = ['g', 'gram', 'grams', 'kg', 'kilogram', 'kilograms', 'ml', 'millilitre', 'millilitres', 'l', 'litre', 'litres', 'pk', 'pack', 'each', 'ea']
            # Create a regex pattern to find a number followed by a unit
            size_pattern = r'\b\d+\s*(' + '|'.join(units) + r')\b'
            for s in product.sizes:
                name = re.sub(size_pattern, '', name, flags=re.IGNORECASE).strip()
                # Also remove the exact size string, in case it's in a different format (e.g., "6x100g")
                name = name.replace(s, '').strip()
        
        return name

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write("Finding duplicate products based on new normalization...")

        normalized_map = defaultdict(list)
        products = Product.objects.all()
        total_products = products.count()
        for i, product in enumerate(products):
            cleaned_name = self._get_cleaned_name(product)

            normalized_key = (
                self._clean_value(cleaned_name) +
                self._clean_value(product.brand) +
                self._clean_value(product.size)
            )
            normalized_map[normalized_key].append(product)
            sys.stdout.write(f"\rProcessing product {i+1}/{total_products}")
            sys.stdout.flush()
        
        sys.stdout.write("\n")


        duplicates_found = 0
        for normalized_key, products in normalized_map.items():
            if len(products) > 1:
                duplicates_found += 1
                products.sort(key=lambda p: p.id)
                main_product = products[0]
                duplicate_products = products[1:]
                
                self.stdout.write(f"Found {len(duplicate_products)} duplicates for '{main_product.name}' ({main_product.brand})")
                self.merge_products(main_product, duplicate_products, dry_run)

        if duplicates_found == 0:
            self.stdout.write(self.style.SUCCESS("No duplicates found."))

        if not dry_run:
            self.stdout.write("Updating normalized_name_brand_size for all products...")
            products_to_update = Product.objects.all()
            total_to_update = products_to_update.count()
            for i, product in enumerate(products_to_update):
                product.save()
                sys.stdout.write(f"\rUpdating product {i+1}/{total_to_update}")
                sys.stdout.flush()
            sys.stdout.write("\n")
            self.stdout.write(self.style.SUCCESS("Finished updating products."))

    def merge_products(self, main_product, duplicate_products, dry_run=False):
        if dry_run:
            self.stdout.write("  1 = master, 2 = duplicate")
            self.stdout.write(f"  1. Name: {main_product.name}, Brand: {main_product.brand}, Size: {main_product.size}")

            for i, duplicate_product in enumerate(duplicate_products, 2):
                self.stdout.write(f"  {i}. Name: {duplicate_product.name}, Brand: {duplicate_product.brand}, Sizes: {duplicate_product.sizes}")
                self.stdout.write(f"  [DRY RUN] Would merge {duplicate_product.id} into {main_product.id}")
            return

        with transaction.atomic():
            for duplicate_product in duplicate_products:
                # Merge fields
                if not main_product.barcode and duplicate_product.barcode:
                    # Check if the barcode is already used by another product
                    if not Product.objects.filter(barcode=duplicate_product.barcode).exists():
                        main_product.barcode = duplicate_product.barcode
                if not main_product.image_url and duplicate_product.image_url:
                    main_product.image_url = duplicate_product.image_url
                if not main_product.url and duplicate_product.url:
                    main_product.url = duplicate_product.url
                if not main_product.description and duplicate_product.description:
                    main_product.description = duplicate_product.description
                if not main_product.country_of_origin and duplicate_product.country_of_origin:
                    main_product.country_of_origin = duplicate_product.country_of_origin
                if not main_product.allergens and duplicate_product.allergens:
                    main_product.allergens = duplicate_product.allergens
                if not main_product.ingredients and duplicate_product.ingredients:
                    main_product.ingredients = duplicate_product.ingredients
                
                main_product.save()

                # Move prices
                Price.objects.filter(product=duplicate_product).update(product=main_product)
                
                # Move categories
                for category in duplicate_product.category.all():
                    main_product.category.add(category)

                # Move substitute_goods
                for substitute in duplicate_product.substitute_goods.all():
                    main_product.substitute_goods.add(substitute)

                # Move size_variants
                for variant in duplicate_product.size_variants.all():
                    main_product.size_variants.add(variant)

                # Delete the duplicate product
                duplicate_product.delete()
