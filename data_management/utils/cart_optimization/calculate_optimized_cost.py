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

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    if pulp.LpStatus[prob.status] == "Optimal":
        final_cost = pulp.value(prob.objective)

        shopping_plan = {name: [] for name in all_store_names}

        for i, slot in enumerate(slots):
            for j, option in enumerate(slot):
                if choice_vars[(i, j)].varValue == 1:
                    store_name = option['store_name']
                    product_name = option['product_name']
                    brand = option['brand']
                    price = option['price']

                    sizes = option['sizes']

                    plan_item = {
                        "product_name": product_name,
                        "brand": brand,
                        "sizes": sizes,
                        "price": price
                    }
                    shopping_plan[store_name].append(plan_item)
                    break

        return final_cost, shopping_plan, choice_vars
    else:
        return None, None, None
