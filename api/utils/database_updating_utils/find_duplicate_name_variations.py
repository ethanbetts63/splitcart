from products.models import Product

def find_duplicates_from_hotlist(hotlist):
    """
    Takes the hotlist and finds pairs of (canonical, duplicate) products to be merged.

    Args:
        hotlist (list): A list of dicts, e.g., 
                        [{'new_variation': '...', 'canonical_name': '...', 'barcode': '...'}].

    Returns:
        list: A list of dicts, each containing a 'canonical' and 'duplicate' Product object.
    """
    duplicates_to_merge = []
    for item in hotlist:
        try:
            # The duplicate product is the one that slipped through with the new name variation
            duplicate_product = Product.objects.get(name=item['new_variation'])
            
            # The canonical product is the one that should have absorbed the new price
            canonical_product = Product.objects.get(name=item['canonical_name'])

            # --- Sanity Checks ---
            # 1. Ensure they are not the same product record
            if duplicate_product.id == canonical_product.id:
                continue

            # 2. Barcode Sanity Check
            # The goal is to merge duplicates, but we need to be careful about conflicts.
            # A conflict is when BOTH products have a barcode, but they are DIFFERENT.
            # If one is missing a barcode, we assume it's a data quality issue and proceed
            # with the merge, trusting the barcode that exists.
            
            c_barcode = canonical_product.barcode
            d_barcode = duplicate_product.barcode
            
            # A true conflict is when both barcodes exist and they don't match.
            is_conflict = bool(c_barcode and d_barcode and c_barcode != d_barcode)

            if is_conflict:
                # This is a real mismatch that requires manual review. Log it and skip merging.
                with open('barcode_mismatch_log.txt', 'a', encoding='utf-8') as f:
                    from datetime import datetime
                    f.write(f"--- Mismatch Detected at {datetime.now().isoformat()} ---")

                    # Get details for both products to compare
                    canonical_prices = canonical_product.prices.all()
                    canonical_stores = {price.store.store_name for price in canonical_prices if price.store}
                    canonical_store_str = ', '.join(sorted(list(canonical_stores))) if canonical_stores else 'N/A'
                    canonical_sku = 'N/A'
                    if canonical_prices:
                        canonical_sku = canonical_prices[0].store_product_id

                    duplicate_prices = duplicate_product.prices.all()
                    duplicate_stores = {price.store.store_name for price in duplicate_prices if price.store}
                    duplicate_store_str = ', '.join(sorted(list(duplicate_stores))) if duplicate_stores else 'N/A'
                    duplicate_sku = 'N/A'
                    if duplicate_prices:
                        duplicate_sku = duplicate_prices[0].store_product_id
                    
                    # --- MISMATCH DETAILS ---
                    mismatch_details = []
                    if canonical_product.name != duplicate_product.name:
                        mismatch_details.append("Name")
                    if canonical_product.brand != duplicate_product.brand:
                        mismatch_details.append("Brand")
                    if canonical_product.sizes != duplicate_product.sizes:
                        mismatch_details.append("Sizes")
                    if c_barcode != d_barcode:
                        mismatch_details.append("Barcode")
                    if canonical_sku != duplicate_sku:
                        mismatch_details.append("SKU")
                    if canonical_stores != duplicate_stores:
                        mismatch_details.append("Stores")

                    if mismatch_details:
                        f.write(f"--- MISMATCH DETAILS: {', '.join(mismatch_details)} ---")
                    else:
                        f.write("--- MISMATCH DETAILS: No obvious field differences, requires manual check. ---")
                        
                    f.write("--- CANONICAL (Original Product) ---")

                    f.write(f"  Name: {canonical_product.name}\n")
                    f.write(f"  Brand: {canonical_product.brand}\n")
                    f.write(f"  Sizes: {canonical_product.sizes}\n")
                    f.write(f"  Normalized: {canonical_product.normalized_name_brand_size}\n")
                    f.write(f"  Barcode: {c_barcode}\n")
                    f.write(f"  SKU (one of): {canonical_sku}\n")
                    f.write(f"  Stores: {canonical_store_str}\n")

                    f.write("--- DUPLICATE (New Variation Product) ---")

                    f.write(f"  Name: {duplicate_product.name}\n")
                    f.write(f"  Brand: {duplicate_product.brand}\n")
                    f.write(f"  Sizes: {duplicate_product.sizes}\n")
                    f.write(f"  Normalized: {duplicate_product.normalized_name_brand_size}\n")
                    f.write(f"  Barcode: {d_barcode}\n")
                    f.write(f"  SKU (one of): {duplicate_sku}\n")
                    f.write(f"  Stores: {duplicate_store_str}\n")
                    f.write("----------------------------------------------------")

                continue

            # If there's no conflict, we can merge.
            duplicates_to_merge.append({
                'canonical': canonical_product,
                'duplicate': duplicate_product
            })

        except Product.DoesNotExist:
            continue
        
        except Product.MultipleObjectsReturned:
            print(f"Found multiple products for variation: {item}. This indicates a deeper data issue. Skipping.")
            continue
            
    return duplicates_to_merge
