def calculate_baseline_cost_for_main_store(main_store_id, slots, all_stores):
    """Helper function to calculate the baseline cost for one potential main store."""
    main_shop_cost = 0
    forced_trips_cost = 0

    for slot in slots:
        options_at_main_store = [opt for opt in slot if opt['store_id'] == main_store_id]
        
        if options_at_main_store:
            main_shop_cost += min(opt['price'] for opt in options_at_main_store)
        else:
            forced_trips_cost += min(opt['price'] for opt in slot)
            
    return main_shop_cost + forced_trips_cost

def calculate_baseline_cost(slots, stores):
    """Calculates the baseline cost using the 'Best Single Shop + Forced Trips' method."""
    if not slots:
        return 0

    slots_filled_by_store = {store.id: 0 for store in stores}
    for store in stores:
        for slot in slots:
            if any(opt['store_id'] == store.id for opt in slot):
                slots_filled_by_store[store.id] += 1

    max_slots_filled = 0
    best_main_stores = []
    if slots_filled_by_store:
        max_slots_filled = max(slots_filled_by_store.values())
        best_main_stores = [store_id for store_id, count in slots_filled_by_store.items() if count == max_slots_filled]

    if not best_main_stores:
        return 0

    min_baseline_cost = float('inf')
    for store_id in best_main_stores:
        current_baseline = calculate_baseline_cost_for_main_store(store_id, slots, stores)
        if current_baseline < min_baseline_cost:
            min_baseline_cost = current_baseline
            
    return min_baseline_cost
