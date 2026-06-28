import pulp

def calculate_optimized_cost(slots, max_companies):
    """Calculates the optimized cost using the PuLP solver."""
    prob = pulp.LpProblem("GroceryOptimization", pulp.LpMinimize)
    all_company_ids = {option['company_id'] for slot in slots for option in slot}
    all_company_names = {option['company_name'] for slot in slots for option in slot}

    choice_vars = pulp.LpVariable.dicts("Choice", ((i, j) for i, slot in enumerate(slots) for j, option in enumerate(slot)), cat="Binary")
    company_usage = pulp.LpVariable.dicts("UseCompany", all_company_ids, cat="Binary")

    total_cost = pulp.lpSum(option['price'] * option['quantity'] * choice_vars[(i, j)] for i, slot in enumerate(slots) for j, option in enumerate(slot))
    prob += total_cost, "Total Cost"

    for i, slot in enumerate(slots):
        prob += pulp.lpSum(choice_vars[(i, j)] for j, option in enumerate(slot)) == 1, f"Fulfill_Slot_{i}"

    for i, slot in enumerate(slots):
        for j, option in enumerate(slot):
            prob += choice_vars[(i, j)] <= company_usage[option['company_id']], f"Link_Choice_{i}_{j}_to_Company"

    prob += pulp.lpSum(company_usage[company_id] for company_id in all_company_ids) <= max_companies, "Max_Companies_Limit"

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

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    if pulp.LpStatus[prob.status] == "Optimal":
        final_cost = pulp.value(prob.objective)

        shopping_plan = {name: {'items': [], 'company_name': name} for name in all_company_names}

        for i, slot in enumerate(slots):
            for j, option in enumerate(slot):
                if choice_vars[(i, j)].varValue == 1:
                    company_name = option['company_name']

                    plan_item = {
                        "product_name": option['product_name'],
                        "brand": option['brand'],
                        "size": option['size'],
                        "price": option['price'],
                        "quantity": option['quantity'],
                        "image_url": option['image_url']
                    }
                    shopping_plan[company_name]['items'].append(plan_item)
                    break

        return final_cost, shopping_plan, choice_vars
    else:
        return None, None, None
