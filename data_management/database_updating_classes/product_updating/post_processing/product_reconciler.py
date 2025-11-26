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

        translation_items = list(translations.items())
        CHUNK_SIZE = 1000
        total_merged = 0
        total_updated = 0

        for i in range(0, len(translation_items), CHUNK_SIZE):
            chunk_items = translation_items[i:i + CHUNK_SIZE]
            chunk_translations = dict(chunk_items)
            # self.command.stdout.write(f"\nProcessing chunk {i//CHUNK_SIZE + 1}/{(len(translation_items) + CHUNK_SIZE - 1)//CHUNK_SIZE}...")

            variation_strings = list(chunk_translations.keys())
            canonical_strings = list(set(chunk_translations.values()))

            all_products = list(Product.objects.filter(
                Q(normalized_name_brand_size__in=variation_strings) |
                Q(normalized_name_brand_size__in=canonical_strings)
            ).select_related('brand'))

            if not all_products:
                # self.command.stdout.write("  - No products found in this chunk. Skipping.")
                continue

            product_map = {p.normalized_name_brand_size: p for p in all_products}
            
            products_to_update = {}
            fk_updates = {}
            products_to_delete_ids = set()

            for variation_name, canonical_name in chunk_translations.items():
                duplicate_product = product_map.get(variation_name)
                canonical_product = product_map.get(canonical_name)

                if not duplicate_product or not canonical_product or duplicate_product.id == canonical_product.id:
                    continue

                fk_updates.setdefault(canonical_product.id, []).append(duplicate_product.id)
                products_to_delete_ids.add(duplicate_product.id)

                if canonical_product.id not in products_to_update:
                    products_to_update[canonical_product.id] = canonical_product
                
                canon_obj = products_to_update[canonical_product.id]
                ProductEnricher.enrich_canonical_product(canon_obj, duplicate_product)

            if not products_to_delete_ids:
                # self.command.stdout.write("  - No product duplicates found to merge in this chunk.")
                continue

            # self.command.stdout.write(f"  - Found {len(products_to_delete_ids)} duplicate products to merge in this chunk.")
            total_merged += len(products_to_delete_ids)
            total_updated += len(products_to_update)

            try:
                with transaction.atomic():
                    # self.command.stdout.write("    - Re-assigning prices from duplicate products...")
                    for canon_id, dupe_ids in fk_updates.items():
                        involved_prices = list(Price.objects.filter(
                            Q(product_id=canon_id) | Q(product_id__in=dupe_ids)
                        ))

                        prices_by_store = {}
                        for p in involved_prices:
                            prices_by_store.setdefault(p.store_id, []).append(p)

                        prices_to_delete_pks = []
                        prices_to_update_pks = []

                        for store_id, price_group in prices_by_store.items():
                            if len(price_group) == 1:
                                price = price_group[0]
                                if price.product_id in dupe_ids:
                                    prices_to_update_pks.append(price.pk)
                            else:
                                price_group.sort(key=lambda x: x.scraped_date, reverse=True)
                                winner = price_group[0]
                                losers = price_group[1:]
                                
                                for loser in losers:
                                    prices_to_delete_pks.append(loser.pk)
                                
                                if winner.product_id in dupe_ids:
                                    prices_to_update_pks.append(winner.pk)
                        
                        if prices_to_delete_pks:
                            Price.objects.filter(pk__in=prices_to_delete_pks).delete()
                        
                        if prices_to_update_pks:
                            Price.objects.filter(pk__in=prices_to_update_pks).update(product_id=canon_id)

                    Product.objects.filter(id__in=products_to_delete_ids).delete()
                    
                    if products_to_update:
                        update_fields = [
                            'barcode', 'url', 'aldi_image_url', 'has_no_coles_barcode',
                            'sizes', 'normalized_name_brand_size_variations', 'brand_name_company_pairs'
                        ]
                        Product.objects.bulk_update(list(products_to_update.values()), update_fields, batch_size=500)

            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"An error occurred during product reconciliation chunk: {e}"))
                raise

        self.command.stdout.write("\n--- Product Reconciler Summary ---")
        self.command.stdout.write(f"Total duplicate products merged: {total_merged}")
        self.command.stdout.write(f"Total canonical products updated: {total_updated}")
        self.command.stdout.write(self.command.style.SUCCESS("Product reconciliation completed successfully."))