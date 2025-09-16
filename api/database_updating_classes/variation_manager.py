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

        # --- Handle Brand Variations ---
        incoming_brand_name = incoming_product_details.get('brand')
        incoming_normalized_brand_key = incoming_product_details.get('normalized_brand_name')

        existing_brand_instance = existing_product.brand
        if not existing_brand_instance:
            return

        updated = False

        # --- Check for raw name variation ---
        # If the incoming raw brand name is different from the existing canonical name, record it as a variation.
        cleaned_incoming_brand_name = str(incoming_brand_name).strip()
        if cleaned_incoming_brand_name and existing_brand_instance.name and cleaned_incoming_brand_name.lower() != existing_brand_instance.name.lower():
            if not existing_brand_instance.name_variations:
                existing_brand_instance.name_variations = []
            
            new_variation_entry = [cleaned_incoming_brand_name, company_name]
            if new_variation_entry not in existing_brand_instance.name_variations:
                existing_brand_instance.name_variations.append(new_variation_entry)
                updated = True

        # --- Check for normalized name variation ---
        # If the normalized keys are different, it's a potential brand duplicate. Record it for the reconciler.
        existing_normalized_brand_key = existing_brand_instance.normalized_name
        if incoming_normalized_brand_key and existing_normalized_brand_key and incoming_normalized_brand_key != existing_normalized_brand_key:
            if not existing_brand_instance.normalized_name_variations:
                existing_brand_instance.normalized_name_variations = []
            
            if incoming_normalized_brand_key not in existing_brand_instance.normalized_name_variations:
                existing_brand_instance.normalized_name_variations.append(incoming_normalized_brand_key)
                updated = True

        if updated:
            self.unit_of_work.add_for_update(existing_brand_instance)

