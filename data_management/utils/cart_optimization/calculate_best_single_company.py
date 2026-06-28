def calculate_best_single_company(slots, original_cart):
    """
    Calculates the best single company to shop at based on the following criteria:
    1. The company with the maximum number of unique products found.
    2. Tie-break with the lowest total cost for the found products.
    """
    if not slots:
        print("No price slots provided.")
        return None

    # Create a set of all unique product IDs in the original cart
    original_product_ids = {item['product_id'] for slot in original_cart for item in slot}

    # Group all available product options by company
    options_by_company = {}
    for i, slot in enumerate(slots):
        for j, option in enumerate(slot):
            company_id = option['company_id']
            if company_id not in options_by_company:
                options_by_company[company_id] = {
                    'company_name': option['company_name'],
                    'options': []
                }
            options_by_company[company_id]['options'].append(option)

    company_results = []
    for company_id, company_data in options_by_company.items():
        # For each company, find the cheapest option for each product slot
        items_in_company = []
        slots_fulfilled_count = 0

        for slot in slots:
            cheapest_option_in_slot = None
            for option in slot:
                if option['company_id'] == company_id:
                    if not cheapest_option_in_slot or option['price'] < cheapest_option_in_slot['price']:
                        cheapest_option_in_slot = option
            
            if cheapest_option_in_slot:
                items_in_company.append(cheapest_option_in_slot)
                slots_fulfilled_count += 1

        total_cost = sum(item['price'] for item in items_in_company)
        
        company_results.append({
            'company_id': company_id,
            'company_name': company_data['company_name'],
            'items': items_in_company,
            'items_found_count': slots_fulfilled_count,
            'total_cost': total_cost
        })

    if not company_results:
        print("No companies found with any items from the cart.")
        return None

    # Sort to find the best company
    company_results.sort(key=lambda x: (-x['items_found_count'], x['total_cost']))
    best_company = company_results[0]

    # Identify missing products
    missing_product_ids = original_product_ids - {item['product_id'] for item in best_company['items']}

    shopping_plan_items = [
        {
            "product_name": item['product_name'],
            "brand": item['brand'],
            "size": item['size'],
            "price": item['unit_price'],
            "quantity": item['quantity'],
            "image_url": item['image_url']
        }
        for item in best_company['items']
    ]

    shopping_plan = {
        best_company['company_name']: {
            'items': shopping_plan_items,
            'company_name': best_company['company_name'],
        }
    }
    
    return {
        'max_companies': 1,
        'optimized_cost': best_company['total_cost'],
        'savings': 0,  # Savings calculation is complex here, maybe compare to baseline?
        'shopping_plan': shopping_plan,
        'items_found_count': best_company['items_found_count'],
        'total_items_in_cart': len(original_cart),
    }
