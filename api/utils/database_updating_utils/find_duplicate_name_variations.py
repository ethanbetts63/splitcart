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

            # 2. Ensure they share the same barcode, which is our ground truth for a match
            if duplicate_product.barcode != canonical_product.barcode:
                print(f"Warning: Name variation match found for '{item['new_variation']}' and '{item['canonical_name']}', but barcodes do not match. Skipping merge.")
                continue

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
