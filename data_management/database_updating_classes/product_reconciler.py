from products.models import Product, Price, PriceRecord
from data_management.data.product_translation_table import PRODUCT_NAME_TRANSLATIONS
from data_management.utils.price_normalizer import PriceNormalizer

class ProductReconciler:
    def __init__(self, command):
        self.command = command

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("Product Reconciler run started."))
        
        if not PRODUCT_NAME_TRANSLATIONS:
            self.command.stdout.write("Translation table is empty. Nothing to reconcile.")
            return

        variation_strings = list(PRODUCT_NAME_TRANSLATIONS.keys())
        batch_size = 500  # Keep well below SQLite's default limit of 999
        
        total_processed = 0

        for i in range(0, len(variation_strings), batch_size):
            batch = variation_strings[i:i + batch_size]
            potential_duplicates = Product.objects.filter(normalized_name_brand_size__in=batch)

            if not potential_duplicates.exists():
                continue

            self.command.stdout.write(f"Processing batch of {len(potential_duplicates)} potential duplicates...")
            total_processed += len(potential_duplicates)

            for duplicate_product in potential_duplicates:
                # Find the canonical string from the table
                canonical_string = PRODUCT_NAME_TRANSLATIONS.get(duplicate_product.normalized_name_brand_size)
                if not canonical_string:
                    continue

                try:
                    # Use .get() which is safe because normalized_name_brand_size is unique
                    canonical_product = Product.objects.get(normalized_name_brand_size=canonical_string)
                    
                    if canonical_product.id == duplicate_product.id:
                        continue

                    self._merge_products(canonical_product, duplicate_product)

                except Product.DoesNotExist:
                    self.command.stderr.write(self.command.style.ERROR(f"Could not find canonical product for {canonical_string}. Skipping."))
                    continue
                except Exception as e:
                    self.command.stderr.write(self.command.style.ERROR(f"An unexpected error occurred for {duplicate_product.normalized_name_brand_size}: {e}"))
                    continue
        
        self.command.stdout.write(f"Processed a total of {total_processed} potential duplicate products.")
        self.command.stdout.write(self.command.style.SUCCESS("Product Reconciler run finished."))

    def _merge_products(self, canonical, duplicate):
        """
        Merges the duplicate product into the canonical product.
        """

        self.command.stdout.write(f"  - Merging '{duplicate.name}' into '{canonical.name}'")
        
        # --- Enrich Fields ---
        update_fields = {}

        # Handle simple fields that can be overwritten if blank
        fields_to_check = ['url', 'image_url_pairs']
        for field_name in fields_to_check:
            if not getattr(canonical, field_name) and getattr(duplicate, field_name):
                update_fields[field_name] = getattr(duplicate, field_name)

        # Handle name variations by merging
        if duplicate.name_variations:
            merged_variations = canonical.name_variations or []
            added_new_variation = False
            for variation in duplicate.name_variations:
                if variation not in merged_variations:
                    merged_variations.append(variation)
                    added_new_variation = True
            
            if added_new_variation:
                update_fields['name_variations'] = merged_variations
        
        # Perform a single, direct database update if any fields have changed
        if update_fields:
            Product.objects.filter(pk=canonical.pk).update(**update_fields)

        # --- De-duplicate and Move Prices ---
        # Get all prices associated with the duplicate product
        prices_to_move = Price.objects.filter(price_record__product=duplicate).select_related('price_record', 'store')

        # Get existing price keys for the canonical product to avoid creating duplicates
        canonical_price_keys = set(
            (p.store_id, p.price_record.scraped_date) for p in Price.objects.filter(price_record__product=canonical)
        )

        moved_count = 0
        deleted_count = 0

        for price in prices_to_move:
            price_key = (price.store_id, price.price_record.scraped_date)
            if price_key not in canonical_price_keys:
                # This price can be moved.
                old_price_record = price.price_record
                
                # Find or create a new PriceRecord for the canonical product with the same details.
                new_price_record, created = PriceRecord.objects.get_or_create(
                    product=canonical,
                    scraped_date=old_price_record.scraped_date,
                    price=old_price_record.price,
                    was_price=old_price_record.was_price,
                    unit_price=old_price_record.unit_price,
                    unit_of_measure=old_price_record.unit_of_measure,
                    per_unit_price_string=old_price_record.per_unit_price_string,
                    is_on_special=old_price_record.is_on_special
                )
                
                # Update the Price object to point to the new record.
                price.price_record = new_price_record

                # Recalculate the normalized_key
                price_data = {
                    'product_id': canonical.id,
                    'store_id': price.store_id,
                    'price': new_price_record.price,
                    'date': new_price_record.scraped_date.isoformat()
                }
                normalizer = PriceNormalizer(price_data=price_data, company=price.store.company.name)
                price.normalized_key = normalizer.get_normalized_key()
                
                price.save()
                moved_count += 1
            else:
                # A price for this store and date already exists for the canonical product.
                # This is a true duplicate price entry, so we can delete it.
                price.delete()
                deleted_count += 1

        # --- Delete Duplicate Product ---
        duplicate.delete()
