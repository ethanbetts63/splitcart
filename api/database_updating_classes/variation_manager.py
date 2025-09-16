from django.db import transaction
from products.models import Product, Price, ProductBrand

class VariationManager:
    """
    Centralizes all logic for handling product name and brand variations.
    Now works entirely in-memory for a single file's processing cycle.
    """
    def __init__(self, command, unit_of_work):
        self.command = command
        self.unit_of_work = unit_of_work
        self.product_reconciliation_list = []
        self.brand_reconciliation_list = []

    def check_for_variation(self, incoming_product_details, existing_product, company_name):
        barcode = existing_product.barcode
        if not barcode or barcode == 'notfound':
            return

        # --- Handle Name Variations ---
        incoming_name = incoming_product_details.get('name', '')
        existing_name = existing_product.name
        cleaned_incoming_name = str(incoming_name).strip()

        if cleaned_incoming_name and existing_name and cleaned_incoming_name.lower() != existing_name.lower():
            updated = False
            if not existing_product.name_variations:
                existing_product.name_variations = []
            
            new_variation_entry = [cleaned_incoming_name, company_name]
            if new_variation_entry not in existing_product.name_variations:
                existing_product.name_variations.append(new_variation_entry)
                updated = True

            variation_normalized_string = incoming_product_details.get('normalized_name_brand_size')
            if variation_normalized_string:
                if not existing_product.normalized_name_brand_size_variations:
                    existing_product.normalized_name_brand_size_variations = []
                
                if variation_normalized_string not in existing_product.normalized_name_brand_size_variations:
                    existing_product.normalized_name_brand_size_variations.append(variation_normalized_string)
                    updated = True
            
            if updated:
                self.unit_of_work.add_for_update(existing_product)

            product_reconciliation_entry = {
                'new_variation': cleaned_incoming_name,
                'canonical_name': existing_name,
                'barcode': barcode,
                'canonical_normalized_string': existing_product.normalized_name_brand_size,
                'duplicate_normalized_string': incoming_product_details.get('normalized_name_brand_size')
            }
            self.product_reconciliation_list.append(product_reconciliation_entry)

        # --- Handle Brand Variations ---
        # Get the Normalized Brand Name from both the incoming and existing products.
        incoming_normalized_brand = incoming_product_details.get('normalized_brand')
        existing_normalized_brand = existing_product.normalized_brand

        # If they are different, it means the translation table has changed, or our matching is imperfect.
        # This is a signal to add a variation.
        if incoming_normalized_brand and existing_normalized_brand and incoming_normalized_brand != existing_normalized_brand:
            
            # The "existing" product's brand is the source of truth.
            try:
                brand_to_update = ProductBrand.objects.get(normalized_name=existing_normalized_brand)
            except ProductBrand.DoesNotExist:
                return # Should not happen in practice

            new_variation_name = incoming_product_details.get('brand')
            new_variation_key = incoming_normalized_brand
            
            updated = False
            # Add to name_variations
            if not brand_to_update.name_variations:
                brand_to_update.name_variations = []
            # The variations are stored as (name, company_name) tuples
            new_entry = (new_variation_name, company_name)
            
            if new_entry not in brand_to_update.name_variations:
                brand_to_update.name_variations.append(new_entry)
                updated = True
                
            # Add to normalized_name_variations
            if not brand_to_update.normalized_name_variations:
                brand_to_update.normalized_name_variations = []
            if new_variation_key not in brand_to_update.normalized_name_variations:
                brand_to_update.normalized_name_variations.append(new_variation_key)
                updated = True

            # Queue the update
            if updated:
                self.unit_of_work.add_for_update(brand_to_update)

    def reconcile_product_duplicates(self):
        """
        Reads the product reconciliation list from memory and merges any potential duplicates.
        """
        self.command.stdout.write(self.command.style.SQL_FIELD("--- Reconciling duplicate products from memory ---"))
        
        if not self.product_reconciliation_list:
            self.command.stdout.write("Product reconciliation list is empty. No duplicates to process.")
            return

        duplicates_to_merge = self._find_product_duplicates(self.product_reconciliation_list)
        
        if not duplicates_to_merge:
            self.command.stdout.write("No valid duplicate pairs found to merge.")
        else:
            self.command.stdout.write(f"Found {len(duplicates_to_merge)} duplicate products to merge.")
            for item in duplicates_to_merge:
                self._merge_products(item['canonical'], item['duplicate'])
        
        # Clear the in-memory list for the next file
        self.product_reconciliation_list.clear()

    def _find_product_duplicates(self, product_reconciliation_list):
        duplicates_to_merge = []
        for item in product_reconciliation_list:
            try:
                duplicate_product = Product.objects.get(normalized_name_brand_size=item['duplicate_normalized_string'])
                canonical_product = Product.objects.get(normalized_name_brand_size=item['canonical_normalized_string'])

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
            f.write(f"--- Mismatch Detected at {datetime.now().isoformat()} ---\n")
            f.write(f"  Canonical: {canonical_product.name} (Barcode: {canonical_product.barcode})\n")
            f.write(f"  Duplicate: {duplicate_product.name} (Barcode: {duplicate_product.barcode})\n")
            f.write("----------------------------------------------------\n")
