import pulp

def calculate_optimized_cost(slots, max_stores):
    """Calculates the optimized cost using the PuLP solver."""
    prob = pulp.LpProblem("GroceryOptimization", pulp.LpMinimize)
    all_store_ids = {option['store_id'] for slot in slots for option in slot}
    all_store_names = {option['store_name'] for slot in slots for option in slot}

    choice_vars = pulp.LpVariable.dicts("Choice", ((i, j) for i, slot in enumerate(slots) for j, option in enumerate(slot)), cat="Binary")
    store_usage = pulp.LpVariable.dicts("UseStore", all_store_ids, cat="Binary")

    total_cost = pulp.lpSum(option['price'] * choice_vars[(i, j)] for i, slot in enumerate(slots) for j, option in enumerate(slot))
    prob += total_cost, "Total Cost"

    for i, slot in enumerate(slots):
        prob += pulp.lpSum(choice_vars[(i, j)] for j, option in enumerate(slot)) == 1, f"Fulfill_Slot_{i}"

    for i, slot in enumerate(slots):
        for j, option in enumerate(slot):
            prob += choice_vars[(i, j)] <= store_usage[option['store_id']], f"Link_Choice_{i}_{j}_to_Store"

    prob += pulp.lpSum(store_usage[store_id] for store_id in all_store_ids) <= max_stores, "Max_Stores_Limit"

    # Group choices by product ID to enforce uniqueness
    choices_by_product = {}
    for i, slot in enumerate(slots):
        for j, option in enumerate(slot):
            pid = option['product_id']
            if pid not in choices_by_product:
                choices_by_product[pid] = []
            choices_by_product[pid].append(choice_vars[(i, j)])

    # Add constraint to ensure each product is used at most once across all slots
    for pid, var_list in choices_by_product.items():
        prob += pulp.lpSum(var_list) <= 1, f"Unique_Product_{pid}"

    store_to_company = {option['store_name']: option['company_name'] for slot in slots for option in slot}
    try:
        store_to_address = {option['store_name']: option['store_address'] for slot in slots for option in slot}
    except KeyError as e:
        print(f"KeyError: {e} not found in option:")
        for slot in slots:
            for option in slot:
                if 'store_address' not in option:
                    print(option)
                    break
        raise

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    if pulp.LpStatus[prob.status] == "Optimal":
        final_cost = pulp.value(prob.objective)

        shopping_plan = {name: {'items': [], 'company_name': store_to_company.get(name, ''), 'store_address': store_to_address.get(name, '')} for name in all_store_names}

        for i, slot in enumerate(slots):
            for j, option in enumerate(slot):
                if choice_vars[(i, j)].varValue == 1:
                    store_name = option['store_name']

                    product_name = option['product_name']
                    brand = option['brand']
                    price = option['price']

                    plan_item = {
                        "product_name": product_name,
                        "brand": brand,
                        "size": option['size'],
                        "price": option['unit_price'],
                        "quantity": option['quantity'],
                        "image_url": option['image_url']
                    }
                    shopping_plan[store_name]['items'].append(plan_item)
                    break

        return final_cost, shopping_plan, choice_vars
    else:
        return None, None, None
