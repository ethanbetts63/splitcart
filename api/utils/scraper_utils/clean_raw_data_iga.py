from datetime import datetime

def clean_raw_data_iga(raw_product_list: list, company: str, store: str, category_slug: str, page_num: int, timestamp: datetime) -> dict:
    """
    Cleans a list of raw IGA product data from its API and wraps it in a 
    dictionary containing metadata about the scrape.
    """
    cleaned_products = []
    
    for product in raw_product_list:
        
        # --- Category Hierarchy Transformation ---
        # The 'categories' field appears to be a breadcrumb trail.
        category_hierarchy = product.get('categories', [])
        departments = []
        categories = []
        subcategories = []

        if category_hierarchy:
            # The structure seems to be a list of breadcrumb parts.
            # We will map them based on their position.
            if len(category_hierarchy) > 0:
                departments = [{'name': category_hierarchy[0].get('category'), 'id': None}]
            if len(category_hierarchy) > 1:
                categories = [{'name': category_hierarchy[1].get('category'), 'id': None}]
            if len(category_hierarchy) > 2:
                subcategories = [{'name': category_hierarchy[2].get('category'), 'id': None}]

        # --- Price and Special Transformation ---
        # The 'tprPrice' (Temporary Price Reduction) array indicates a special.
        is_on_special = bool(product.get('tprPrice'))
        was_price = None
        if is_on_special:
            # If on special, the regular price becomes the 'was_price'.
            was_price = product.get('priceNumeric')
            # The actual current price is inside the tprPrice array.
            current_price = product.get('tprPrice', [{}])[0].get('price')
        else:
            current_price = product.get('priceNumeric')

        # --- Unit Price Transformation ---
        # IGA API does not seem to provide a clear unit price field.
        # We will leave it null for now.
        unit_price = None
        unit_of_measure = product.get('unitOfMeasure', {}).get('label')

        clean_product = {
            'name': product.get('name'),
            'brand': product.get('brand'),
            'barcode': product.get('barcode'),
            'stockcode': product.get('sku'),
            'package_size': product.get('sellBy'), # 'sellBy' seems most appropriate
            'price': current_price,
            'was_price': was_price,
            'is_on_special': is_on_special,
            'is_available': product.get('available', False),
            'unit_price': unit_price,
            'unit_of_measure': unit_of_measure,
            'url': None, # No direct URL available in this API endpoint
            'departments': departments,
            'categories': categories,
            'subcategories': subcategories
        }
        cleaned_products.append(clean_product)
    
    return {
        "metadata": {
            "company": company.lower(),
            "store": store.lower(),
            "category": category_slug,
            "page_number": page_num,
            "scraped_at": timestamp.isoformat()
        },
        "products": cleaned_products
    }
