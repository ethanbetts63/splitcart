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
            
            # Link brand from cache
            normalized_brand = product_dict.get('normalized_brand')
            brand_obj = self.caches['normalized_brand_names'].get(normalized_brand)
            if not brand_obj:
                # This should not happen if BrandManager runs first, but as a safeguard:
                self.command.stderr.write(self.command.style.ERROR(f"      - ERROR: Brand '{normalized_brand}' not found in cache. Skipping product '{product_dict.get('name')}'.'"))
                continue

            # Create new Product instance
            new_product = Product(
                name=product_dict.get('name', ''),
                brand=brand_obj,
                barcode=product_dict.get('barcode'),
                normalized_name_brand_size=product_dict.get('normalized_name_brand_size'),
                # Add other fields as necessary
            )
            product_objects_to_create.append(new_product)
        return product_objects_to_create

    def _prepare_updates(self, products_to_update_data):
        """Enriches existing Product objects and returns a list of those that changed."""
        product_objects_to_update = []
        for existing_product, data in products_to_update_data:
            product_dict = data['product']
            updated = False

            # Example enrichment logic: add a new barcode if one wasn't present
            new_barcode = product_dict.get('barcode')
            if new_barcode and not existing_product.barcode:
                existing_product.barcode = new_barcode
                updated = True
            
            # Add more enrichment logic here for other fields...

            if updated:
                product_objects_to_update.append(existing_product)
        return product_objects_to_update

    def _update_caches(self, created_products, updated_products):
        """Updates the shared caches with new and updated product info."""
        self.command.stdout.write("    - Updating shared product caches...")
        # Update for newly created products
        for product in created_products:
            if product.barcode:
                self.cache_updater('products_by_barcode', product.barcode, product)
            if product.normalized_name_brand_size:
                self.cache_updater('products_by_norm_string', product.normalized_name_brand_size, product)
            # Add SKU cache update logic here...

        # Update for updated products (in case a key like barcode was added)
        for product in updated_products:
            if product.barcode:
                self.cache_updater('products_by_barcode', product.barcode, product)
            # No need to update norm_string cache as it's the key and shouldn't change
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
                    update_fields = ['barcode'] # Add other enriched fields here
                    Product.objects.bulk_update(objects_to_update, update_fields, batch_size=500)

            # 4. Cache Update (only after successful transaction)
            # Re-fetch created products to get their DB-assigned pks
            if objects_to_create:
                norm_strings = [p.normalized_name_brand_size for p in objects_to_create]
                newly_created_products = list(Product.objects.filter(normalized_name_brand_size__in=norm_strings))
            
            self._update_caches(newly_created_products, objects_to_update)

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"    - Error processing products: {e}"))
            raise
