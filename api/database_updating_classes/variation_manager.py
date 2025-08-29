import json
import os
from django.db import transaction
from products.models import Product, Price

class VariationManager:
    """
    Centralizes all logic for handling product name and brand variations.
    Now works entirely in-memory for a single file's processing cycle.
    """
    def __init__(self, command, unit_of_work):
        self.command = command
        self.unit_of_work = unit_of_work
        self.new_hotlist_entries = []

    def check_for_variation(self, incoming_product_details, existing_product, company_name):
        barcode = existing_product.barcode
        if not barcode or barcode == 'notfound':
            return

        incoming_name = incoming_product_details.get('name', '')
        existing_name = existing_product.name
        cleaned_incoming_name = str(incoming_name).strip()

        if cleaned_incoming_name and existing_name and cleaned_incoming_name.lower() != existing_name.lower():
            if not existing_product.name_variations:
                existing_product.name_variations = []
            
            new_variation_tuple = (cleaned_incoming_name, company_name)
            if new_variation_tuple not in existing_product.name_variations:
                existing_product.name_variations.append(new_variation_tuple)
                self.unit_of_work.add_for_update(existing_product)

            hotlist_entry = {
                'new_variation': cleaned_incoming_name,
                'canonical_name': existing_name,
                'barcode': barcode
            }
            self.new_hotlist_entries.append(hotlist_entry)

    def reconcile_duplicates(self):
        """
        Reads the hotlist from memory and merges any potential duplicates.
        """
        self.command.stdout.write(self.command.style.SQL_FIELD("--- Reconciling duplicate products from memory hotlist ---"))
        
        hotlist = self.new_hotlist_entries
        if not hotlist:
            self.command.stdout.write("Hotlist is empty. No duplicates to process.")
            return

        duplicates_to_merge = self._find_duplicates_from_hotlist(hotlist)
        
        if not duplicates_to_merge:
            self.command.stdout.write("No valid duplicate pairs found to merge.")
        else:
            self.command.stdout.write(f"Found {len(duplicates_to_merge)} duplicate products to merge.")
            for item in duplicates_to_merge:
                self._merge_products(item['canonical'], item['duplicate'])
        
        # Clear the in-memory hotlist for the next file
        self.new_hotlist_entries.clear()

    def _find_duplicates_from_hotlist(self, hotlist):
        duplicates_to_merge = []
        for item in hotlist:
            try:
                duplicate_product = Product.objects.get(name=item['new_variation'])
                canonical_product = Product.objects.get(name=item['canonical_name'])

                if duplicate_product.id == canonical_product.id:
                    continue

                c_barcode = canonical_product.barcode
                d_barcode = duplicate_product.barcode
                is_conflict = bool(c_barcode and d_barcode and c_barcode != d_barcode)

                if is_conflict:
                    self._log_barcode_mismatch(canonical_product, duplicate_product)
                    continue

                duplicates_to_merge.append({
                    'canonical': canonical_product,
                    'duplicate': duplicate_product
                })
            except Product.DoesNotExist:
                continue
            except Product.MultipleObjectsReturned as e:
                self.command.stderr.write(self.command.style.ERROR(f"Multiple products found for variation: {item}. Skipping. Error: {e}"))
                continue
        return duplicates_to_merge

    @transaction.atomic
    def _merge_products(self, canonical_product, duplicate_product):
        self.command.stdout.write(f"  - Merging '{duplicate_product.name}' into '{canonical_product.name}'")
        prices_to_move = Price.objects.filter(product=duplicate_product)
        price_count = prices_to_move.count()
        prices_to_move.update(product=canonical_product)
        
        if duplicate_product.name_variations:
            if not canonical_product.name_variations:
                canonical_product.name_variations = []
            for variation in duplicate_product.name_variations:
                if variation not in canonical_product.name_variations:
                    canonical_product.name_variations.append(variation)
            canonical_product.save()

        duplicate_product.delete()
        self.command.stdout.write(f"    - Moved {price_count} prices and deleted duplicate product.")

    def _log_barcode_mismatch(self, canonical_product, duplicate_product):
        with open('barcode_mismatch_log.txt', 'a', encoding='utf-8') as f:
            from datetime import datetime
            f.write(f"--- Mismatch Detected at {datetime.now().isoformat()} ---")
            f.write(f"  Canonical: {canonical_product.name} (Barcode: {canonical_product.barcode})")
            f.write(f"  Duplicate: {duplicate_product.name} (Barcode: {duplicate_product.barcode})")
            f.write("----------------------------------------------------")