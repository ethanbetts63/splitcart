class ProductEnricher:
    """
    A self-contained utility to enrich one Product object with data from another.
    This is used during the reconciliation process to merge a duplicate product
    into a canonical one.
    """
    @staticmethod
    def enrich_canonical_product(canonical_product, duplicate_product):
        """
        Merges data from a duplicate product into a canonical product,
        modifying the canonical product in-place.

        Args:
            canonical_product (Product): The product to merge data into.
            duplicate_product (Product): The product to merge data from.

        Returns:
            bool: True if the canonical_product was modified, False otherwise.
        """
        updated = False

        # --- Simple fields (update if blank on canonical) ---
        if not canonical_product.barcode and duplicate_product.barcode:
            canonical_product.barcode = duplicate_product.barcode
            updated = True
        if not canonical_product.url and duplicate_product.url:
            canonical_product.url = duplicate_product.url
            updated = True
        if not canonical_product.aldi_image_url and duplicate_product.aldi_image_url:
            canonical_product.aldi_image_url = duplicate_product.aldi_image_url
            updated = True

        # --- Boolean field (true wins) ---
        if duplicate_product.has_no_coles_barcode and not canonical_product.has_no_coles_barcode:
            canonical_product.has_no_coles_barcode = True
            updated = True

        # --- JSON list fields (merge unique values) ---
        
        # Merge 'sizes'
        canonical_sizes = set(canonical_product.sizes or [])
        initial_size_count = len(canonical_sizes)
        if duplicate_product.sizes:
            for s in duplicate_product.sizes:
                canonical_sizes.add(s)
        if len(canonical_sizes) > initial_size_count:
            canonical_product.sizes = sorted(list(canonical_sizes))
            updated = True

        # Merge 'normalized_name_brand_size_variations'
        canonical_variations = set(canonical_product.normalized_name_brand_size_variations or [])
        initial_variation_count = len(canonical_variations)
        
        # Add the duplicate's own canonical name as a variation, ONLY if it's different
        incoming_variation = duplicate_product.normalized_name_brand_size
        if incoming_variation and incoming_variation != canonical_product.normalized_name_brand_size:
            canonical_variations.add(incoming_variation)

        # Add the duplicate's existing variations
        if duplicate_product.normalized_name_brand_size_variations:
            for v in duplicate_product.normalized_name_brand_size_variations:
                # Also check here to be safe
                if v != canonical_product.normalized_name_brand_size:
                    canonical_variations.add(v)

        if len(canonical_variations) > initial_variation_count:
            canonical_product.normalized_name_brand_size_variations = sorted(list(canonical_variations))
            updated = True

        # Merge 'brand_name_company_pairs'
        # Use a dictionary to enforce one entry per company, keeping the first one seen.
        existing_pairs_map = {pair[1]: pair[0] for pair in (canonical_product.brand_name_company_pairs or []) if len(pair) == 2 and pair[0]}
        initial_pair_count = len(existing_pairs_map)

        # Now, iterate through the incoming pairs and only add them if the company is not already in our map.
        if duplicate_product.brand_name_company_pairs:
            for p in duplicate_product.brand_name_company_pairs:
                # Ensure the pair is valid and the brand string is not empty
                if len(p) == 2 and p[0]: 
                    incoming_brand, incoming_company = p
                    if incoming_company and incoming_company not in existing_pairs_map:
                        existing_pairs_map[incoming_company] = incoming_brand

        if len(existing_pairs_map) > initial_pair_count:
            # Convert the map back to a list of lists and sort it by company name for canonical storage.
            new_pairs_list = sorted([[brand, company] for company, brand in existing_pairs_map.items()], key=lambda p: p[1])
            canonical_product.brand_name_company_pairs = new_pairs_list
            updated = True
            
        return updated
