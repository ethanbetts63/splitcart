import os
import ast
from django.db import transaction
from django.db.models import Q
from products.models import Product, Price
from .product_enricher import ProductEnricher

TRANSLATION_TABLE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '..',
    '..',
    '..',
    'data',
    'product_normalized_name_brand_size_translation_table.py'
))

class ProductReconciler:
    """
    Finds and merges duplicate Product objects based on a translation table.
    This is a self-contained process that runs after all products have been updated.
    """
    def __init__(self, command):
        self.command = command
        self.translation_table_path = TRANSLATION_TABLE_PATH

    def _load_translation_table(self):
        """Safely loads the translation dictionary from the .py file."""
        try:
            with open(self.translation_table_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            if '=' in file_content:
                dict_str = file_content.split('=', 1)[1].strip()
                return ast.literal_eval(dict_str)
            return {}
        except (FileNotFoundError, SyntaxError, ValueError) as e:
            self.command.stderr.write(self.command.style.ERROR(f"Error loading product translation table: {e}"))
            return {}

    def run(self):
        """
        Orchestrates the entire product reconciliation process.
        """
        self.command.stdout.write("--- Product Reconciler run started. ---")
        translations = self._load_translation_table()
        if not translations:
            self.command.stdout.write("Product translation table is empty. Nothing to reconcile.")
            return

        variation_strings = list(translations.keys())
        canonical_strings = list(set(translations.values()))

        all_products = list(Product.objects.filter(
            Q(normalized_name_brand_size__in=variation_strings) |
            Q(normalized_name_brand_size__in=canonical_strings)
        ).select_related('brand'))

        if not all_products:
            self.command.stdout.write("No products found matching translation table. Nothing to reconcile.")
            return

        product_map = {p.normalized_name_brand_size: p for p in all_products}
        
        products_to_update = {}  # {canonical_id: canonical_obj}
        fk_updates = {}  # {canonical_id: [list_of_duplicate_ids]}
        products_to_delete_ids = set()

        for variation_name, canonical_name in translations.items():
            duplicate_product = product_map.get(variation_name)
            canonical_product = product_map.get(canonical_name)

            if not duplicate_product or not canonical_product or duplicate_product.id == canonical_product.id:
                continue

            # Stage FK update for Price objects
            fk_updates.setdefault(canonical_product.id, []).append(duplicate_product.id)
            
            # Stage product for deletion
            products_to_delete_ids.add(duplicate_product.id)

            # Stage update of canonical product
            if canonical_product.id not in products_to_update:
                products_to_update[canonical_product.id] = canonical_product
            
            canon_obj = products_to_update[canonical_product.id]
            ProductEnricher.enrich_canonical_product(canon_obj, duplicate_product)

        if not products_to_delete_ids:
            self.command.stdout.write("No product duplicates found to merge.")
            return

        self.command.stdout.write(f"Found {len(products_to_delete_ids)} duplicate products to merge.")

        try:
            with transaction.atomic():
                # 1. Update foreign keys on Price table
                self.command.stdout.write("  - Re-assigning prices from duplicate products...")
                for canon_id, dupe_ids in fk_updates.items():
                    # 1. Fetch all prices for both canonical and duplicate products
                    involved_prices = list(Price.objects.filter(
                        Q(product_id=canon_id) | Q(product_id__in=dupe_ids)
                    ))

                    # 2. Group prices by store
                    prices_by_store = {}
                    for p in involved_prices:
                        prices_by_store.setdefault(p.store_id, []).append(p)

                    prices_to_delete_pks = []
                    prices_to_update_pks = []

                    # 3. Process each store group to find conflicts and resolve them
                    for store_id, price_group in prices_by_store.items():
                        if len(price_group) == 1:
                            # No conflict, but if it's a duplicate's price, it needs updating
                            price = price_group[0]
                            if price.product_id in dupe_ids:
                                prices_to_update_pks.append(price.pk)
                        else:
                            # CONFLICT: More than one price for this store. Find the winner.
                            price_group.sort(key=lambda x: x.scraped_date, reverse=True)
                            winner = price_group[0]
                            losers = price_group[1:]
                            
                            # Mark losers for deletion
                            for loser in losers:
                                prices_to_delete_pks.append(loser.pk)
                            
                            # If the winner was a duplicate, it needs to be updated
                            if winner.product_id in dupe_ids:
                                prices_to_update_pks.append(winner.pk)
                    
                    # 4. Perform bulk database operations
                    if prices_to_delete_pks:
                        Price.objects.filter(pk__in=prices_to_delete_pks).delete()
                    
                    if prices_to_update_pks:
                        Price.objects.filter(pk__in=prices_to_update_pks).update(product_id=canon_id)

                # 2. Update canonical products with enriched data
                if products_to_update:
                    update_fields = [
                        'barcode', 'url', 'aldi_image_url', 'has_no_coles_barcode',
                        'sizes', 'normalized_name_brand_size_variations', 'brand_name_company_pairs'
                    ]
                    Product.objects.bulk_update(products_to_update.values(), update_fields, batch_size=500)
                    self.command.stdout.write(f"  - Bulk updated {len(products_to_update)} canonical products.")

                # 3. Delete the duplicate products
                Product.objects.filter(id__in=products_to_delete_ids).delete()
                self.command.stdout.write(f"  - Bulk deleted {len(products_to_delete_ids)} duplicate products.")

            self.command.stdout.write(self.command.style.SUCCESS("Product reconciliation completed successfully."))

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"An error occurred during product reconciliation: {e}"))
            raise