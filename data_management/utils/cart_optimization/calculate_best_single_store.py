def calculate_best_single_store(slots, original_cart):
    """
    Calculates the best single store to shop at based on the following criteria:
    1. The store with the maximum number of unique products found.
    2. Tie-break with the lowest total cost for the found products.
    """
    if not slots:
        return None

    # Create a set of all unique product IDs in the original cart
    original_product_ids = {item['product_id'] for slot in original_cart for item in slot}

    # Group all available product options by store
    options_by_store = {}
    for i, slot in enumerate(slots):
        for j, option in enumerate(slot):
            store_id = option['store_id']
            if store_id not in options_by_store:
                options_by_store[store_id] = {
                    'store_name': option['store_name'],
                    'company_name': option['company_name'],
                    'options': []
                }
            options_by_store[store_id]['options'].append(option)

    store_results = []
    for store_id, store_data in options_by_store.items():
        # For each store, find the cheapest option for each product slot
        items_in_store = []
        found_product_ids = set()

        for slot in slots:
            cheapest_option_in_slot = None
            for option in slot:
                if option['store_id'] == store_id:
                    if not cheapest_option_in_slot or option['price'] < cheapest_option_in_slot['price']:
                        cheapest_option_in_slot = option
            
            if cheapest_option_in_slot:
                items_in_store.append(cheapest_option_in_slot)
                found_product_ids.add(cheapest_option_in_slot['product_id'])

        total_cost = sum(item['price'] for item in items_in_store)
        
        store_results.append({
            'store_id': store_id,
            'store_name': store_data['store_name'],
            'company_name': store_data['company_name'],
            'items': items_in_store,
            'items_found_count': len(found_product_ids),
            'total_cost': total_cost
        })

    if not store_results:
        return None

    # Sort to find the best store
    store_results.sort(key=lambda x: (-x['items_found_count'], x['total_cost']))
    best_store = store_results[0]

    # Identify missing products
    missing_product_ids = original_product_ids - {item['product_id'] for item in best_store['items']}

    shopping_plan = {
        best_store['store_name']: {
            'items': best_store['items'],
            'company_name': best_store['company_name']
        }
    }
    
    return {
        'max_stores': 1,
        'optimized_cost': best_store['total_cost'],
        'savings': 0,  # Savings calculation is complex here, maybe compare to baseline?
        'shopping_plan': shopping_plan,
        'items_found_count': best_store['items_found_count'],
        'total_items_in_cart': len(original_cart),
    }
