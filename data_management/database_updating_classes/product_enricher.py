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

        if not existing_product.barcode and product_details.get('barcode'):
            existing_product.barcode = product_details.get('barcode')
            updated = True
        if not existing_product.url and product_details.get('url'):
            existing_product.url = product_details.get('url')
            updated = True

        # Update image_url_pairs
        incoming_image_pairs = product_details.get('image_url_pairs', [])
        if incoming_image_pairs:
            existing_pairs_dict = {pair[0]: pair[1] for pair in existing_product.image_url_pairs} if existing_product.image_url_pairs else {}
            
            for company, url in incoming_image_pairs:
                if company not in existing_pairs_dict:
                    if not existing_product.image_url_pairs:
                        existing_product.image_url_pairs = []
                    existing_product.image_url_pairs.append([company, url])
                    updated = True
                elif existing_pairs_dict[company] != url:
                    for pair in existing_product.image_url_pairs:
                        if pair[0] == company:
                            pair[1] = url
                            updated = True
                            break

        if company_name.lower() == 'coles' and not product_details.get('barcode') and not existing_product.has_no_coles_barcode:
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
        This method performs a direct database update and does not return a flag.
        """
        update_fields = {}

        # Handle simple fields that can be overwritten if blank
        fields_to_check = ['url', 'image_url_pairs']
        for field_name in fields_to_check:
            if not getattr(canonical_product, field_name) and getattr(duplicate_product, field_name):
                update_fields[field_name] = getattr(duplicate_product, field_name)

        # Handle name variations by merging
        if duplicate_product.name_variations:
            merged_variations = canonical_product.name_variations or []
            added_new_variation = False
            for variation in duplicate_product.name_variations:
                if variation not in merged_variations:
                    merged_variations.append(variation)
                    added_new_variation = True
            
            if added_new_variation:
                update_fields['name_variations'] = merged_variations
        
        # Perform a single, direct database update if any fields have changed
        if update_fields:
            from products.models import Product
            Product.objects.filter(pk=canonical_product.pk).update(**update_fields)
