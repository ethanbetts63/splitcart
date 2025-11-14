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
        canonical_pairs = {tuple(p) for p in (canonical_product.brand_name_company_pairs or [])}
        initial_pair_count = len(canonical_pairs)
        if duplicate_product.brand_name_company_pairs:
            for p in duplicate_product.brand_name_company_pairs:
                canonical_pairs.add(tuple(p))
        if len(canonical_pairs) > initial_pair_count:
            canonical_product.brand_name_company_pairs = sorted([list(p) for p in canonical_pairs])
            updated = True
            
        return updated
