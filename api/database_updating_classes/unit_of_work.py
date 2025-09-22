from django.db import transaction
from products.models import Product, Price, ProductBrand, PriceRecord
from .category_manager import CategoryManager
from api.utils.price_normalizer import PriceNormalizer

class UnitOfWork:
    def __init__(self, command):
        self.command = command
        self.new_products_to_process = []
        self.prices_to_create = []
        self.products_to_update = []
        self.brands_to_update = []
        self.groups_to_clear_candidates = []
        self.category_manager = CategoryManager(command)

    def add_new_product(self, product_instance, product_details):
        """
        Adds a new product instance along with its raw details for later processing.
        """
        self.new_products_to_process.append((product_instance, product_details))

    def add_price(self, product, store, product_details):
        price_value = product_details.get('price_current')
        if not price_value:
            return

        scraped_date = product_details.get('scraped_date')
        if not scraped_date:
            return

        # Step 1 & 2: Get or Create PriceRecord
        price_record, _ = PriceRecord.objects.get_or_create(
            product=product,
            price=price_value,
            was_price=product_details.get('price_was'),
            unit_price=product_details.get('unit_price'),
            unit_of_measure=product_details.get('unit_of_measure'),
            per_unit_price_string=product_details.get('per_unit_price_string'),
            is_on_special=product_details.get('is_on_special', False)
        )

        # Step 3: Calculate normalized_key
        price_data = {
            'product_id': product.id,
            'store_id': store.id,
            'price': price_value, # Still needed for the key
            'date': scraped_date
        }
        normalizer = PriceNormalizer(price_data=price_data, company=store.company.name)
        normalized_key = normalizer.get_normalized_key()

        if not normalized_key:
            return

        # Step 4 & 5: Instantiate and append lightweight Price object
        self.prices_to_create.append(
            Price(
                price_record=price_record,
                store=store,
                sku=product_details.get('sku'),
                scraped_date=scraped_date,
                normalized_key=normalized_key,
                is_available=product_details.get('is_available'),
                source='direct_scrape'
            )
        )

    def add_for_update(self, instance):
        if isinstance(instance, Product):
            if instance not in self.products_to_update:
                self.products_to_update.append(instance)
        elif isinstance(instance, ProductBrand):
            if instance not in self.brands_to_update:
                self.brands_to_update.append(instance)

    def add_group_to_clear_candidates(self, group):
        if group not in self.groups_to_clear_candidates:
            self.groups_to_clear_candidates.append(group)

    def _deduplicate_new_products(self, resolver):
        unique_new_products_with_details = []
        seen_barcodes = set(resolver.barcode_cache.keys())
        seen_normalized_strings = set(resolver.normalized_string_cache.keys())

        for product, details in self.new_products_to_process:
            if product.barcode and product.barcode in seen_barcodes:
                continue
            if product.normalized_name_brand_size and product.normalized_name_brand_size in seen_normalized_strings:
                continue
            
            unique_new_products_with_details.append((product, details))
            if product.barcode:
                seen_barcodes.add(product.barcode)
            if product.normalized_name_brand_size:
                seen_normalized_strings.add(product.normalized_name_brand_size)
        return unique_new_products_with_details

    def commit(self, consolidated_data, product_cache, resolver, store_obj):
        self.command.stdout.write("--- Committing changes to database ---")
        try:
            with transaction.atomic():
                # Stage 1: Create new products
                unique_new_products_with_details = self._deduplicate_new_products(resolver)
                
                if unique_new_products_with_details:
                    new_products = [p for p, d in unique_new_products_with_details]
                    self.command.stdout.write(f"  - Creating {len(new_products)} truly unique new products.")
                    # The product objects in `new_products` will have their PKs populated after this call.
                    Product.objects.bulk_create(new_products, batch_size=500)

                    # Now that products are created and have IDs, create their prices
                    for product_instance, product_details in unique_new_products_with_details:
                        self.add_price(product_instance, store_obj, product_details)

                    # Refresh the product_cache with the newly created products
                    for p in new_products:
                        product_cache[p.normalized_name_brand_size] = p

                # Stage 2: Create all prices (for both new and existing products)
                if self.prices_to_create:
                    self.command.stdout.write(f"  - Creating {len(self.prices_to_create)} new price records.")
                    Price.objects.bulk_create(self.prices_to_create, batch_size=500, ignore_conflicts=True)

                # Stage 3: Process categories now that all products exist
                self.category_manager.process_categories(consolidated_data, product_cache, store_obj)

                # Stage 4: Update existing products
                if self.products_to_update:
                    update_fields = [
                        'barcode', 'url', 'image_url', 'description', 
                        'country_of_origin', 'ingredients', 'has_no_coles_barcode', 
                        'name_variations', 'normalized_name_brand_size_variations', 'sizes'
                    ]
                    Product.objects.bulk_update(self.products_to_update, update_fields, batch_size=500)
                    self.command.stdout.write(f"  - Updated {len(self.products_to_update)} products with new information.")

                # Stage 5: Update existing brands
                if self.brands_to_update:
                    brand_update_fields = ['name_variations', 'normalized_name_variations']
                    ProductBrand.objects.bulk_update(self.brands_to_update, brand_update_fields, batch_size=500)
                    self.command.stdout.write(f"  - Updated {len(self.brands_to_update)} brands with new variation info.")

                # Stage 6: Clear candidates from groups that have been processed
                if self.groups_to_clear_candidates:
                    for group in self.groups_to_clear_candidates:
                        group.candidates.clear()
                    self.command.stdout.write(f"  - Cleared candidates from {len(self.groups_to_clear_candidates)} groups.")
            
            self.command.stdout.write(self.command.style.SUCCESS("--- Commit successful ---"))
            return True
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f'An error occurred during commit: {e}'))
            return False