from django.db import transaction
from products.models import Product

class ProductManager:
    """
    Manages the creation and updating of Product objects.
    This class encapsulates the logic for resolving, enriching, mapping,
    persisting, and caching products.
    """
    def __init__(self, command, caches, cache_updater):
        self.command = command
        self.caches = caches
        self.cache_updater = cache_updater

    def _resolve_products(self, raw_product_data):
        """Sorts raw product data into 'create' and 'update' lists."""
        self.command.stdout.write("    - Resolving products (create vs. update)...")
        products_to_create_data = []
        products_to_update_data = []

        for data in raw_product_data:
            product_dict = data.get('product', {})
            if not product_dict:
                continue

            match = None
            # Tier 1: Barcode
            barcode = product_dict.get('barcode')
            if barcode and barcode in self.caches['products_by_barcode']:
                match = self.caches['products_by_barcode'][barcode]

            # Tier 2: SKU (if no barcode match)
            if not match:
                company = data.get('metadata', {}).get('company')
                sku = product_dict.get('sku')
                if company and sku and sku in self.caches['products_by_sku'].get(company, {}):
                    match = self.caches['products_by_sku'][company][sku]
            
            # Tier 3: Normalized String (if still no match)
            if not match:
                norm_string = product_dict.get('normalized_name_brand_size')
                if norm_string and norm_string in self.caches['products_by_norm_string']:
                    match = self.caches['products_by_norm_string'][norm_string]

            if match:
                products_to_update_data.append((match, data))
            else:
                products_to_create_data.append(data)
        
        self.command.stdout.write(f"      - To create: {len(products_to_create_data)}, To update: {len(products_to_update_data)}")
        return products_to_create_data, products_to_update_data

    def _prepare_creations(self, products_to_create_data):
        """Maps raw data dictionaries to new Product model instances."""
        product_objects_to_create = []
        for data in products_to_create_data:
            product_dict = data['product']
            metadata = data['metadata']
            
            normalized_brand = product_dict.get('normalized_brand')
            brand_obj = self.caches['normalized_brand_names'].get(normalized_brand)
            if not brand_obj:
                self.command.stderr.write(self.command.style.ERROR(f"      - ERROR: Brand '{normalized_brand}' not found in cache. Skipping product '{product_dict.get('name')}'.'"))
                continue

            new_product = Product(
                name=product_dict.get('name', ''),
                brand=brand_obj,
                barcode=product_dict.get('barcode'),
                normalized_name_brand_size=product_dict.get('normalized_name_brand_size'),
                size=product_dict.get('size'),
                sizes=product_dict.get('sizes', []),
                has_no_coles_barcode=product_dict.get('has_no_coles_barcode', False),
                aldi_image_url=product_dict.get('aldi_image_url'),
                url=product_dict.get('url'),
                brand_name_company_pairs=[[product_dict.get('brand'), metadata.get('company')]]
                # company_skus will be handled later
            )
            product_objects_to_create.append(new_product)
        return product_objects_to_create

    def _prepare_updates(self, products_to_update_data):
        """Enriches existing Product objects and returns a list of those that changed."""
        product_objects_to_update = []
        for existing_product, data in products_to_update_data:
            product_dict = data['product']
            metadata = data['metadata']
            updated = False

            # Simple fields (update if blank)
            if not existing_product.barcode and product_dict.get('barcode'):
                existing_product.barcode = product_dict.get('barcode')
                updated = True
            if not existing_product.url and product_dict.get('url'):
                existing_product.url = product_dict.get('url')
                updated = True
            if not existing_product.aldi_image_url and product_dict.get('aldi_image_url'):
                existing_product.aldi_image_url = product_dict.get('aldi_image_url')
                updated = True

            # Boolean field
            if product_dict.get('has_no_coles_barcode') and not existing_product.has_no_coles_barcode:
                existing_product.has_no_coles_barcode = True
                updated = True

            # JSON list fields (merge unique)
            new_sizes = set(existing_product.sizes)
            incoming_sizes = product_dict.get('sizes', [])
            initial_size_count = len(new_sizes)
            for s in incoming_sizes:
                new_sizes.add(s)
            if len(new_sizes) > initial_size_count:
                existing_product.sizes = sorted(list(new_sizes))
                updated = True

            # Logic for normalized_name_brand_size_variations
            new_variations = set(existing_product.normalized_name_brand_size_variations)
            incoming_variation = product_dict.get('normalized_name_brand_size')
            initial_variation_count = len(new_variations)
            if incoming_variation:
                new_variations.add(incoming_variation)
            if len(new_variations) > initial_variation_count:
                existing_product.normalized_name_brand_size_variations = sorted(list(new_variations))
                updated = True

            # Logic for brand_name_company_pairs
            new_pairs = list(existing_product.brand_name_company_pairs)
            company = metadata.get('company')
            raw_brand = product_dict.get('brand')
            # Add pair only if a pair for that company doesn't already exist
            if company and raw_brand and not any(p[1] == company for p in new_pairs):
                new_pairs.append([raw_brand, company])
                existing_product.brand_name_company_pairs = new_pairs
                updated = True

            # company_skus will be handled later

            if updated:
                product_objects_to_update.append(existing_product)
        return product_objects_to_update

    def _update_caches(self, created_products, updated_products):
        """Updates the shared caches with new and updated product info."""
        self.command.stdout.write("    - Updating shared product caches...")
        products_to_process = created_products + updated_products
        
        for product in products_to_process:
            if product.barcode:
                self.cache_updater('products_by_barcode', product.barcode, product)
            if product.normalized_name_brand_size:
                self.cache_updater('products_by_norm_string', product.normalized_name_brand_size, product)
            # Add SKU cache update logic here...
        self.command.stdout.write("      - Caches updated.")


    def process(self, raw_product_data):
        """
        Creates and updates products based on the raw data, using the shared caches.
        """
        self.command.stdout.write("  - ProductManager: Processing products...")

        # 1. Resolution
        to_create_data, to_update_data = self._resolve_products(raw_product_data)

        # 2. Data Preparation
        objects_to_create = self._prepare_creations(to_create_data)
        objects_to_update = self._prepare_updates(to_update_data)

        if not objects_to_create and not objects_to_update:
            self.command.stdout.write("    - No new or updated products to persist.")
            return

        # 3. Persistence
        newly_created_products = []
        try:
            with transaction.atomic():
                if objects_to_create:
                    self.command.stdout.write(f"    - Creating {len(objects_to_create)} new products...")
                    Product.objects.bulk_create(objects_to_create, batch_size=500)
                
                if objects_to_update:
                    self.command.stdout.write(f"    - Updating {len(objects_to_update)} existing products...")
                    update_fields = [
                        'barcode', 'url', 'aldi_image_url', 'has_no_coles_barcode',
                        'sizes', 'normalized_name_brand_size_variations', 'brand_name_company_pairs'
                    ]
                    Product.objects.bulk_update(objects_to_update, update_fields, batch_size=500)

            # 4. Cache Update (only after successful transaction)
            if objects_to_create:
                norm_strings = [p.normalized_name_brand_size for p in objects_to_create]
                newly_created_products = list(Product.objects.filter(normalized_name_brand_size__in=norm_strings))
            
            self._update_caches(newly_created_products, objects_to_update)

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"    - Error processing products: {e}"))
            raise
