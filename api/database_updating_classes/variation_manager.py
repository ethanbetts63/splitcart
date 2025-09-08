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
        incoming_brand = incoming_product_details.get('brand')
        canonical_brand_name = existing_product.brand

        if incoming_brand and canonical_brand_name and incoming_brand.lower() != canonical_brand_name.lower():
            brand_reconciliation_entry = {
                'canonical_brand_name': canonical_brand_name,
                'duplicate_brand_name': incoming_brand
            }
            if brand_reconciliation_entry not in self.brand_reconciliation_list:
                self.brand_reconciliation_list.append(brand_reconciliation_entry)

    def reconcile_product_duplicates(self):
        """
        Reads the product reconciliation list from memory and merges any potential duplicates.
        """
        self.command.stdout.write(self.command.style.SQL_FIELD("--- Reconciling duplicate products from memory ---"))
        
        product_reconciliation_list = self.product_reconciliation_list
        if not product_reconciliation_list:
            self.command.stdout.write("Product reconciliation list is empty. No duplicates to process.")
            return

        duplicates_to_merge = self._find_product_duplicates(product_reconciliation_list)
        
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
            f.write(f"--- Mismatch Detected at {datetime.now().isoformat()} ---")
            f.write(f"  Canonical: {canonical_product.name} (Barcode: {canonical_product.barcode})")
            f.write(f"  Duplicate: {duplicate_product.name} (Barcode: {duplicate_product.barcode})")
            f.write("----------------------------------------------------")

    def reconcile_brand_duplicates(self):
        """
        Reads the brand reconciliation list from memory and merges any potential duplicates.
        """
        self.command.stdout.write(self.command.style.SQL_FIELD("--- Reconciling duplicate brands from memory ---"))
        
        if not self.brand_reconciliation_list:
            self.command.stdout.write("Brand reconciliation list is empty. No duplicates to process.")
            return

        self.command.stdout.write(f"Found {len(self.brand_reconciliation_list)} potential brand duplicates to merge.")
        
        for item in self.brand_reconciliation_list:
            canonical_name = item['canonical_brand_name']
            duplicate_name = item['duplicate_brand_name']

            try:
                with transaction.atomic():
                    canonical_brand = ProductBrand.objects.get(name=canonical_name)
                    duplicate_brand = ProductBrand.objects.get(name=duplicate_name)

                    if canonical_brand.id == duplicate_brand.id:
                        continue

                    # Update all products pointing to the duplicate brand
                    Product.objects.filter(brand=duplicate_brand.name).update(brand=canonical_brand.name)

                    # Merge name variations
                    if duplicate_brand.name_variations:
                        if not canonical_brand.name_variations:
                            canonical_brand.name_variations = []
                        for variation in duplicate_brand.name_variations:
                            if variation not in canonical_brand.name_variations:
                                canonical_brand.name_variations.append(variation)
                    
                    # Ensure the duplicate name itself is in the variations list
                    if duplicate_brand.name not in canonical_brand.name_variations:
                        canonical_brand.name_variations.append(duplicate_brand.name)
                        
                    canonical_brand.save()
                    
                    # Delete the duplicate brand
                    duplicate_brand.delete()
                    
                    self.command.stdout.write(f"  - Merged brand '{duplicate_name}' into '{canonical_name}'.")

            except ProductBrand.DoesNotExist:
                # This can happen if a brand is both a canonical and a duplicate in the same run,
                # and the duplicate gets deleted before its own merge operation runs.
                # We check if the duplicate brand still exists. If not, we can safely skip.
                if not ProductBrand.objects.filter(name=duplicate_name).exists():
                    self.command.stdout.write(f"  - Skipping merge for '{duplicate_name}' as it has already been merged in this run.")
                else:
                    self.command.stderr.write(f"Could not find canonical brand '{canonical_name}' for merge. Skipping.")
                continue
            except Exception as e:
                self.command.stderr.write(f"Error merging brand '{duplicate_name}': {e}")
                continue
        
        # Clear the in-memory list
        self.brand_reconciliation_list.clear()