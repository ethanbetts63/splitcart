import os
from products.models import Product, Price
from .base_reconciler import BaseReconciler
from .product_enricher import ProductEnricher
from django.db import transaction
from django.db.models import Q

TRANSLATION_TABLE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '..',
    'data',
    'product_normalized_name_brand_size_translation_table.py'
))

class ProductReconciler(BaseReconciler):
    def __init__(self, command):
        super().__init__(command, TRANSLATION_TABLE_PATH)
        self.prices_to_create = []
        self.prices_to_update = []
        self.prices_to_delete = []
        self.products_to_update = []

    def get_model(self):
        return Product

    def get_variation_field_name(self):
        return 'normalized_name_brand_size'

    def get_canonical_field_name(self):
        return 'normalized_name_brand_size'

    def run(self):
        """
        Orchestrates the entire reconciliation process, including pre-fetching
        and bulk database operations to ensure performance.
        """
        self.command.stdout.write("--- Product Reconciler run started. ---")
        translation_dict = self._load_translation_table()
        if not translation_dict:
            self.command.stdout.write("Product translation table is empty or could not be loaded. Nothing to reconcile.")
            return

        variation_strings = list(translation_dict.keys())
        canonical_strings = list(translation_dict.values())

        # Get all potential duplicate and canonical products in one go
        all_involved_products = self.get_model().objects.filter(
            Q(**{f"{self.get_variation_field_name()}__in": variation_strings}) |
            Q(**{f"{self.get_canonical_field_name()}__in": canonical_strings})
        ).select_related('brand')

        # Pre-fetch all prices for all involved products
        all_involved_product_ids = [p.id for p in all_involved_products]
        all_prices = Price.objects.filter(product_id__in=all_involved_product_ids).select_related('store')

        # Create maps for easy lookup
        self.prices_by_product_id = {}
        for price in all_prices:
            if price.product_id not in self.prices_by_product_id:
                self.prices_by_product_id[price.product_id] = []
            self.prices_by_product_id[price.product_id].append(price)

        # This will call merge_items for each duplicate, which now uses the cache
        super().run(all_involved_products=all_involved_products)

        # --- Perform all database operations in bulk within a single transaction ---
        with transaction.atomic():
            if self.prices_to_create:
                Price.objects.bulk_create(self.prices_to_create, batch_size=500)
                self.command.stdout.write(f"  - Bulk created {len(self.prices_to_create)} new prices.")

            if self.prices_to_update:
                Price.objects.bulk_update(self.prices_to_update, ['scraped_date', 'price', 'was_price', 'unit_price', 'unit_of_measure', 'per_unit_price_string', 'is_on_special', 'source'], batch_size=500)
                self.command.stdout.write(f"  - Bulk updated {len(self.prices_to_update)} existing prices.")
            
            if self.prices_to_delete:
                price_ids_to_delete = [p.id for p in self.prices_to_delete]
                Price.objects.filter(id__in=price_ids_to_delete).delete()
                self.command.stdout.write(f"  - Bulk deleted {len(self.prices_to_delete)} old prices.")

            # Update canonical products that had variations merged
            if self.products_to_update:
                Product.objects.bulk_update(self.products_to_update, ['normalized_name_brand_size_variations'], batch_size=500)
                self.command.stdout.write(f"  - Bulk updated {len(self.products_to_update)} canonical products with new variations.")

            # Finally, delete the duplicate products themselves
            duplicate_ids = [p.id for p in self.duplicates_to_delete]
            if duplicate_ids:
                Product.objects.filter(id__in=duplicate_ids).delete()
                self.command.stdout.write(f"  - Bulk deleted {len(duplicate_ids)} duplicate products.")

    def merge_items(self, canonical_item, duplicate_item):
        """
        Merges the duplicate product into the canonical product by adding
        their prices to in-memory lists for bulk processing. This method now
        relies on pre-fetched data and performs no DB queries.
        """
        self.command.stdout.write(f"  - Staging merge of '{duplicate_item.name}' (PK: {duplicate_item.pk}) into '{canonical_item.name}' (PK: {canonical_item.pk})")
        
        # --- Stage Field Enrichment ---
        # Note: enrich_from_product now only modifies the object in memory
        was_updated = ProductEnricher.enrich_from_product(canonical_item, duplicate_item)
        if was_updated:
            self.products_to_update.append(canonical_item)

        # --- Stage Price Migrations ---
        existing_canonical_prices = {p.store.id: p for p in self.prices_by_product_id.get(canonical_item.id, [])}
        prices_to_move = self.prices_by_product_id.get(duplicate_item.id, [])

        for price_to_move in prices_to_move:
            price_data = {
                'scraped_date': price_to_move.scraped_date,
                'price': price_to_move.price,
                'was_price': price_to_move.was_price,
                'unit_price': price_to_move.unit_price,
                'unit_of_measure': price_to_move.unit_of_measure,
                'per_unit_price_string': price_to_move.per_unit_price_string,
                'is_on_special': price_to_move.is_on_special,
                'source': price_to_move.source,
            }

            existing_price = existing_canonical_prices.get(price_to_move.store.id)
            if existing_price:
                # It exists, so stage it for an update
                for key, value in price_data.items():
                    setattr(existing_price, key, value)
                self.prices_to_update.append(existing_price)
            else:
                # It's a new price for the canonical product, stage it for creation
                self.prices_to_create.append(Price(
                    product=canonical_item,
                    store=price_to_move.store,
                    **price_data
                ))
            
            self.prices_to_delete.append(price_to_move)