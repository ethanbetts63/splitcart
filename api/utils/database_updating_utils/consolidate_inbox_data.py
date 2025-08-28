import json

def process_product_data(data, consolidated_data, barcode_to_key_map, command, filename):
    product_details = data.get('product', {})
    metadata = data.get('metadata', {})
    
    key = product_details.get('normalized_name_brand_size')
    if not key:
        return True 

    company_name = metadata.get('company')
    if not company_name:
        return True

    price_info = {
        'store_id': metadata.get('store_id'),
        'price': product_details.get('price_current'),
        'is_on_special': product_details.get('is_on_special', False),
        'is_available': product_details.get('is_available', True),
        'sku': product_details.get('product_id_store')
    }

    barcode = product_details.get('barcode')

    # If barcode exists and we've seen it before, merge this product's data
    if barcode and barcode in barcode_to_key_map:
        canonical_key = barcode_to_key_map[barcode]
        
        # If the canonical key is the same as the current key, it's just a price update
        if canonical_key == key:
            consolidated_data[canonical_key]['price_history'].append(price_info)
            return False

        # If keys are different, it's a name variation. Merge into the canonical entry.
        canonical_entry = consolidated_data[canonical_key]
        canonical_entry['price_history'].append(price_info)
        
        category_path = tuple(product_details.get('category_path', []))
        if category_path:
            canonical_entry['category_paths'].add(category_path)

        # Handle the name variation
        incoming_name = product_details.get('name', '').strip()
        canonical_name = canonical_entry['product_details'].get('name', '').strip()

        if incoming_name and incoming_name.lower() != canonical_name.lower():
            if 'name_variations_to_process' not in canonical_entry:
                canonical_entry['name_variations_to_process'] = []
            
            new_variation_tuple = (incoming_name, company_name)
            
            # Avoid adding duplicate variation tuples
            if new_variation_tuple not in canonical_entry['name_variations_to_process']:
                canonical_entry['name_variations_to_process'].append(new_variation_tuple)
        
        return False

    # If the key (normalized_name_brand_size) is already in consolidated_data (but barcode wasn't a match)
    if key in consolidated_data:
        consolidated_data[key]['price_history'].append(price_info)
        category_path = tuple(product_details.get('category_path', []))
        if category_path:
            consolidated_data[key]['category_paths'].add(category_path)
    else:
        # This is a new product entry
        category_paths = set()
        raw_path = product_details.get('category_path', [])
        if raw_path:
            category_paths.add(tuple(raw_path))

        consolidated_data[key] = {
            'product_details': product_details,
            'price_history': [price_info],
            'category_paths': category_paths,
            'company_name': company_name
        }
        # If this new product has a barcode, map it to its primary key
        if barcode:
            barcode_to_key_map[barcode] = key
            
    return False