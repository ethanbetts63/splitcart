class ProductEnricher:
    @staticmethod
    def enrich_from_dict(existing_product, product_details, company_name):
        """
        Enriches a Product instance with data from a dictionary (from scraped data).
        Returns True if the instance was modified, False otherwise.
        """
        updated = False

        # Update company_skus
        sku = product_details.get('sku')
        if sku:
            if not existing_product.company_skus:
                existing_product.company_skus = {}
            if company_name not in existing_product.company_skus:
                existing_product.company_skus[company_name] = []
            
            if sku not in existing_product.company_skus[company_name]:
                existing_product.company_skus[company_name].append(sku)
                updated = True

        # Merge sizes lists
        incoming_sizes = set(product_details.get('sizes', []))
        if incoming_sizes:
            existing_sizes = set(existing_product.sizes)
            if not incoming_sizes.issubset(existing_sizes):
                combined_sizes = sorted(list(existing_sizes.union(incoming_sizes)))
                existing_product.sizes = combined_sizes
                updated = True

        # If a barcode is found for a product that didn't have one, add it.
        # Also, explicitly set has_no_coles_barcode to False, in case it was previously flagged.
        if not existing_product.barcode and product_details.get('barcode'):
            existing_product.barcode = product_details.get('barcode')
            if existing_product.has_no_coles_barcode:
                existing_product.has_no_coles_barcode = False
            updated = True
        if not existing_product.url and product_details.get('url'):
            existing_product.url = product_details.get('url')
            updated = True

        # Update aldi_image_url for Aldi products
        if company_name.lower() == 'aldi':
            incoming_aldi_image_url = product_details.get('aldi_image_url')
            if incoming_aldi_image_url and existing_product.aldi_image_url != incoming_aldi_image_url:
                existing_product.aldi_image_url = incoming_aldi_image_url
                updated = True
        
        # If the scraper explicitly flags that a Coles product has no barcode, update the field.
        if product_details.get('has_no_coles_barcode'):
            if not existing_product.has_no_coles_barcode:
                existing_product.has_no_coles_barcode = True
                updated = True




        # Update brand_name_company_pairs
        raw_brand_name = product_details.get('brand')
        new_pair = [raw_brand_name, company_name]
        
        found_existing_company_pair = False
        if existing_product.brand_name_company_pairs:
            for i, pair in enumerate(existing_product.brand_name_company_pairs):
                if pair[1] == company_name: # Check if company already exists in a pair
                    found_existing_company_pair = True
                    break
        
        if not found_existing_company_pair:
            if not existing_product.brand_name_company_pairs:
                existing_product.brand_name_company_pairs = []
            existing_product.brand_name_company_pairs.append(new_pair)
            updated = True

        return updated

    @staticmethod
    def enrich_from_product(canonical_product, duplicate_product):
        """
        Enriches a canonical Product instance with data from a duplicate Product instance.
        This method now modifies the canonical_product in memory and returns a boolean.
        """
        updated = False

        # Handle simple fields that can be overwritten if blank
        fields_to_check = ['url', 'aldi_image_url']
        for field_name in fields_to_check:
            if not getattr(canonical_product, field_name) and getattr(duplicate_product, field_name):
                setattr(canonical_product, field_name, getattr(duplicate_product, field_name))
                updated = True

        # Handle normalized_name_brand_size_variations by merging
        if duplicate_product.normalized_name_brand_size_variations or duplicate_product.normalized_name_brand_size:
            merged_variations = canonical_product.normalized_name_brand_size_variations or []
            if not isinstance(merged_variations, list):
                merged_variations = []

            # Use a set for efficient checking
            existing_variations_set = set(merged_variations)
            initial_set_size = len(existing_variations_set)

            # Add variations from the duplicate
            if duplicate_product.normalized_name_brand_size_variations:
                for variation in duplicate_product.normalized_name_brand_size_variations:
                    existing_variations_set.add(variation)
            
            # Also add the duplicate's own canonical name as a variation
            if duplicate_product.normalized_name_brand_size:
                existing_variations_set.add(duplicate_product.normalized_name_brand_size)

            if len(existing_variations_set) > initial_set_size:
                canonical_product.normalized_name_brand_size_variations = sorted(list(existing_variations_set))
                updated = True
        
        return updated
