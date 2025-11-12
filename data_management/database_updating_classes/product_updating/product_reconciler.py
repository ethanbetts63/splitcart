import os
from products.models import Product, Price
from .base_reconciler import BaseReconciler
from .product_enricher import ProductEnricher
from django.db.models import Q

TRANSLATION_TABLE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '..',
    'data',
    'product_normalized_name_brand_size_translation_table.py'
))

class ProductReconciler(BaseReconciler):
    def __init__(self, command, unit_of_work):
        super().__init__(command, TRANSLATION_TABLE_PATH)
        self.unit_of_work = unit_of_work
        # These lists are for items that the UoW doesn't handle, like deleting products
        self.products_to_update = []
        self.prices_to_delete_ids = []

    def get_model(self):
        return Product

    def get_variation_field_name(self):
        return 'normalized_name_brand_size'

    def get_canonical_field_name(self):
        return 'normalized_name_brand_size'

    def run(self):
        """
        Orchestrates the reconciliation process by finding duplicates and delegating
        the merging logic to merge_items. It relies on pre-fetched data.
        """
        self.command.stdout.write("--- Product Reconciler run started. ---")
        translation_dict = self._load_translation_table()
        if not translation_dict:
            self.command.stdout.write("Product translation table is empty or could not be loaded. Nothing to reconcile.")
            return

        variation_strings = list(translation_dict.keys())
        canonical_strings = list(translation_dict.values())

        all_involved_products = list(self.get_model().objects.filter(
            Q(**{f"{self.get_variation_field_name()}__in": variation_strings}) |
            Q(**{f"{self.get_canonical_field_name()}__in": canonical_strings})
        ).select_related('brand'))

        all_involved_product_ids = [p.id for p in all_involved_products]
        all_prices = Price.objects.filter(product_id__in=all_involved_product_ids).select_related('store')

        self.prices_by_product_id = {}
        for price in all_prices:
            if price.product_id not in self.prices_by_product_id:
                self.prices_by_product_id[price.product_id] = []
            self.prices_by_product_id[price.product_id].append(price)

        super().run(all_involved_products=all_involved_products)

    def merge_items(self, canonical_item, duplicate_item):
        """
        Merges a duplicate product into a canonical one by staging changes
        in the central UnitOfWork.
        """
        self.command.stdout.write(f"  - Staging merge of '{duplicate_item.name}' (PK: {duplicate_item.pk}) into '{canonical_item.name}' (PK: {canonical_item.pk})")
        
        was_updated = ProductEnricher.enrich_from_product(canonical_item, duplicate_item)
        if was_updated and canonical_item not in self.products_to_update:
            self.products_to_update.append(canonical_item)

        prices_to_move = self.prices_by_product_id.get(duplicate_item.id, [])
        for price in prices_to_move:
            # The UoW's add_price is designed for scraped dicts, not Price objects.
            # So, we'll manually create the dict it expects.
            price_details = {
                'price_current': price.price,
                'was_price': price.was_price,
                'unit_price': price.unit_price,
                'unit_of_measure': price.unit_of_measure,
                'per_unit_price_string': price.per_unit_price_string,
                'is_on_special': price.is_on_special,
                'price_hash': price.price_hash,
            }
            metadata = {'scraped_date': price.scraped_date.strftime('%Y-%m-%d')}
            
            # Delegate price handling to the central UnitOfWork
            self.unit_of_work.add_price(canonical_item, price.store, price_details, metadata)
            self.prices_to_delete_ids.append(price.id)
