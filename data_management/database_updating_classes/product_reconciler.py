import os
from products.models import Product, Price
from .base_reconciler import BaseReconciler
from .product_enricher import ProductEnricher

TRANSLATION_TABLE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '..',
    'data',
    'product_normalized_name_brand_size_translation_table.py'
))

class ProductReconciler(BaseReconciler):
    def __init__(self, command):
        super().__init__(command, TRANSLATION_TABLE_PATH)

    def get_model(self):
        return Product

    def get_variation_field_name(self):
        return 'normalized_name_brand_size'

    def get_canonical_field_name(self):
        return 'normalized_name_brand_size'

    def merge_items(self, canonical_item, duplicate_item):
        """
        Merges the duplicate product into the canonical product.
        """
        self.command.stdout.write(f"  - Merging '{duplicate_item.name}' into '{canonical_item.name}'")
        
        # --- Enrich Fields ---
        ProductEnricher.enrich_from_product(canonical_item, duplicate_item)

        # --- De-duplicate and Move Prices ---
        # Get all prices associated with the duplicate product
        prices_to_move = Price.objects.filter(product=duplicate_item)

        for price_to_move in prices_to_move:
            # Prepare data for update_or_create
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
            
            # Perform an upsert for the canonical product and the store group
            Price.objects.update_or_create(
                product=canonical_item,
                store_group=price_to_move.store_group,
                defaults=price_data
            )
            
            # Delete the original price object associated with the duplicate product
            price_to_move.delete()
