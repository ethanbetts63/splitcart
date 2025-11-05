import os
from products.models import Product, Price, PriceRecord
from data_management.utils.price_normalizer import PriceNormalizer
from .base_reconciler import BaseReconciler

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
        update_fields = {}

        # Handle simple fields that can be overwritten if blank
        fields_to_check = ['url', 'image_url_pairs']
        for field_name in fields_to_check:
            if not getattr(canonical_item, field_name) and getattr(duplicate_item, field_name):
                update_fields[field_name] = getattr(duplicate_item, field_name)

        # Handle name variations by merging
        if duplicate_item.name_variations:
            merged_variations = canonical_item.name_variations or []
            added_new_variation = False
            for variation in duplicate_item.name_variations:
                if variation not in merged_variations:
                    merged_variations.append(variation)
                    added_new_variation = True
            
            if added_new_variation:
                update_fields['name_variations'] = merged_variations
        
        # Perform a single, direct database update if any fields have changed
        if update_fields:
            Product.objects.filter(pk=canonical_item.pk).update(**update_fields)

        # --- De-duplicate and Move Prices ---
        # Get all prices associated with the duplicate product
        prices_to_move = Price.objects.filter(price_record__product=duplicate_item).select_related('price_record', 'store')

        # Get existing price keys for the canonical product to avoid creating duplicates
        canonical_price_keys = set(
            (p.store_id, p.price_record.scraped_date) for p in Price.objects.filter(price_record__product=canonical_item)
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
                    product=canonical_item,
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
                    'product_id': canonical_item.id,
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

