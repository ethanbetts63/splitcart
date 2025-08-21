
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from products.models import Product, Price
from collections import defaultdict
import sys

class Command(BaseCommand):
    help = 'Extracts size from product name and brand, merges conflicting products, and updates the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate the process and show what would be changed without saving to the database.'
        )

    def _extract_sizes(self, text):
        if not text:
            return []
        
        extracted_sizes = []
        units = {
            'g': ['g', 'gram', 'grams'],
            'kg': ['kg', 'kilogram', 'kilograms'],
            'ml': ['ml', 'millilitre', 'millilitres'],
            'l': ['l', 'litre', 'litres'],
            'pk': ['pk', 'pack'],
            'ea': ['each', 'ea'],
        }

        for standard_unit, variations in units.items():
            for unit in variations:
                pattern = r'(\d+\.?\d*)\s*' + re.escape(unit) + r'\b'
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    extracted_sizes.append(f"{match.group(1)}{standard_unit}")
        return extracted_sizes

    def _clean_value(self, value):
        if value is None:
            return ''
        words = sorted(str(value).lower().split())
        sorted_string = ' '.join(words)
        cleaned_value = re.sub(r'[^a-z0-9]', '', sorted_string)
        return cleaned_value

    def _get_cleaned_name(self, product):
        name = product.name
        if product.brand and product.brand.lower() in name.lower():
            name = re.sub(r'\b' + re.escape(product.brand) + r'\b', '', name, flags=re.IGNORECASE).strip()
        
        if product.sizes:
            units = ['g', 'gram', 'grams', 'kg', 'kilogram', 'kilograms', 'ml', 'millilitre', 'millilitres', 'l', 'litre', 'litres', 'pk', 'pack', 'each', 'ea']
            size_pattern = r'\b\d+\s*(' + '|'.join(units) + r')\b'
            for s in product.sizes:
                name = re.sub(size_pattern, '', name, flags=re.IGNORECASE).strip()
                name = name.replace(s, '').strip()
        
        return name

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING("--- DRY RUN ---"))
            self._execute_logic(dry_run=True)
        else:
            with transaction.atomic():
                self.stdout.write(self.style.WARNING("--- RUNNING IN LIVE MODE ---"))
                self._execute_logic(dry_run=False)
        
        self.stdout.write(self.style.SUCCESS("Process finished."))

    def _execute_logic(self, dry_run):
        self.stdout.write("Step 1: Calculating potential new normalized keys and identifying conflicts...")
        
        potential_normalized_map = defaultdict(list)
        products = Product.objects.all()
        total_products = products.count()

        for i, product in enumerate(products):
            new_sizes = self._extract_sizes(product.name) + self._extract_sizes(product.brand)
            updated_sizes = sorted(list(set(product.sizes + new_sizes)))

            temp_product = Product(name=product.name, brand=product.brand, sizes=updated_sizes)
            cleaned_name = self._get_cleaned_name(temp_product)
            
            normalized_key = (
                self._clean_value(cleaned_name) +
                self._clean_value(temp_product.brand) +
                self._clean_value(" ".join(temp_product.sizes))
            )
            
            potential_normalized_map[normalized_key].append({
                'product': product,
                'updated_sizes': updated_sizes
            })

            sys.stdout.write(f"\rProcessing product {i+1}/{total_products}")
            sys.stdout.flush()
        
        sys.stdout.write("\n")

        self.stdout.write("Step 2: Merging conflicting products...")
        
        products_to_save = []
        products_to_delete = []

        for normalized_key, items in potential_normalized_map.items():
            if len(items) > 1:
                items.sort(key=lambda x: x['product'].id)
                main_item = items[0]
                duplicate_items = items[1:]
                
                main_product = main_item['product']
                main_product.sizes = main_item['updated_sizes']
                
                self.stdout.write(self.style.WARNING(f"Conflict for key '{normalized_key}'. Merging {len(duplicate_items)} duplicates into product {main_product.id}."))
                
                if dry_run:
                    self.stdout.write(f"  Primary: ID={main_product.id}, Name='{main_product.name}', Brand='{main_product.brand}', New Sizes={main_product.sizes}")

                for item in duplicate_items:
                    duplicate_product = item['product']
                    if dry_run:
                        self.stdout.write(f"  Duplicate: ID={duplicate_product.id}, Name='{duplicate_product.name}', Brand='{duplicate_product.brand}', Original Sizes={duplicate_product.sizes}")
                        self.stdout.write(f"    [DRY RUN] Would merge prices and relations from {duplicate_product.id} to {main_product.id}")
                        self.stdout.write(f"    [DRY RUN] Would delete product {duplicate_product.id}")
                    else:
                        barcode_to_transfer = self.merge_products(main_product, duplicate_product)
                        if barcode_to_transfer:
                            self.stdout.write(f"    Transferring barcode {barcode_to_transfer} from {duplicate_product.id} to {main_product.id}")
                            duplicate_product.delete()
                            main_product.barcode = barcode_to_transfer
                        else:
                            products_to_delete.append(duplicate_product)

                products_to_save.append(main_product)
            else:
                item = items[0]
                product = item['product']
                if product.sizes != item['updated_sizes']:
                    product.sizes = item['updated_sizes']
                    products_to_save.append(product)

        if not dry_run:
            self.stdout.write(f"Saving {len(products_to_save)} products...")
            for product in products_to_save:
                product.save()
            
            self.stdout.write(f"Deleting {len(products_to_delete)} products...")
            for product in products_to_delete:
                product.delete()

    def merge_products(self, main_product, duplicate_product):
        barcode_to_transfer = None
        if not main_product.barcode and duplicate_product.barcode:
            if not Product.objects.filter(barcode=duplicate_product.barcode).exclude(id=duplicate_product.id).exists():
                barcode_to_transfer = duplicate_product.barcode

        for field in ['image_url', 'url', 'description', 'country_of_origin', 'allergens', 'ingredients']:
            if not getattr(main_product, field) and getattr(duplicate_product, field):
                setattr(main_product, field, getattr(duplicate_product, field))

        Price.objects.filter(product=duplicate_product).update(product=main_product)

        for category in duplicate_product.category.all():
            main_product.category.add(category)
        for substitute in duplicate_product.substitute_goods.all():
            main_product.substitute_goods.add(substitute)
        for variant in duplicate_product.size_variants.all():
            main_product.size_variants.add(variant)
            
        return barcode_to_transfer
