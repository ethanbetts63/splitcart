import json
import pulp

def solve_shopping_cart(slots, max_stores=3):
    """
    Solves the shopping cart optimization problem.

    Args:
        slots (list): The list of lists of dicts representing the shopping cart.
        max_stores (int): The maximum number of stores the user is willing to visit.

    Returns:
        tuple: A tuple containing the final cost and the shopping plan, or (None, None) if no solution is found.
    """
    prob = pulp.LpProblem("GroceryOptimization", pulp.LpMinimize)

    # --- 1. Data Preparation ---
    # Get a set of all unique store IDs involved in this cart
    all_store_ids = set()
    for i, slot in enumerate(slots):
        for j, option in enumerate(slot):
            all_store_ids.add(option['store_id'])

    # --- 2. Define Variables ---
    # choice_vars[i][j] is 1 if we choose option j for slot i, 0 otherwise
    choice_vars = pulp.LpVariable.dicts(
        "Choice", 
        ((i, j) for i, slot in enumerate(slots) for j, option in enumerate(slot)),
        cat="Binary"
    )

    # store_usage[store_id] is 1 if we use this store, 0 otherwise
    store_usage = pulp.LpVariable.dicts("UseStore", all_store_ids, cat="Binary")

    # --- 3. Objective Function (Minimize total cost) ---
    total_cost = pulp.lpSum(
        option['price'] * choice_vars[(i, j)]
        for i, slot in enumerate(slots)
        for j, option in enumerate(slot)
    )
    prob += total_cost, "Total Cost"

    # --- 4. Define Constraints ---
    # Constraint 1: We must buy exactly one product for each slot.
    for i, slot in enumerate(slots):
        prob += pulp.lpSum(choice_vars[(i, j)] for j, option in enumerate(slot)) == 1, f"Fulfill_Slot_{i}"

    # Constraint 2: If we choose an option, its store must be marked as used.
    for i, slot in enumerate(slots):
        for j, option in enumerate(slot):
            prob += choice_vars[(i, j)] <= store_usage[option['store_id']], f"Link_Choice_{i}_{j}_to_Store"

    # Constraint 3: Limit the number of stores used.
    prob += pulp.lpSum(store_usage[store_id] for store_id in all_store_ids) <= max_stores, "Max_Stores_Limit"

    # --- 5. Solve the Problem ---
    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    # --- 6. Process and Return Results ---
    if pulp.LpStatus[prob.status] == "Optimal":
        final_cost = pulp.value(prob.objective)
        
        # Reconstruct the shopping plan from the results
        shopping_plan = {store_id: [] for store_id in all_store_ids}
        store_name_map = {}

        for i, slot in enumerate(slots):
            for j, option in enumerate(slot):
                if choice_vars[(i, j)].varValue == 1:
                    store_id = option['store_id']
                    shopping_plan[store_id].append(option)
                    store_name_map[store_id] = option['store_name']
                    break
        
        # Add store names to the final plan for readability
        final_plan = {
            'total_cost': final_cost,
            'stores': []
        }
        for store_id, items in shopping_plan.items():
            if items: # Only include stores we actually buy from
                final_plan['stores'].append({
                    'store_id': store_id,
                    'store_name': store_name_map[store_id],
                    'items': items
                })

        return final_plan
    else:
        return None

def main():
    """ Main function to run the solver. """
    try:
        with open('test_cart.json', 'r') as f:
            test_cart_data = json.load(f)
    except FileNotFoundError:
        print("Error: 'test_cart.json' not found.")
        print("Please generate it first by running: python manage.py generate_test_cart > test_cart.json")
        return
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from 'test_cart.json'. The file might be empty or malformed.")
        return

    # You can change the max_stores value here
    max_stores_to_visit = 3

    print(f"Attempting to solve cart with a maximum of {max_stores_to_visit} stores...\n")

    solution = solve_shopping_cart(test_cart_data, max_stores=max_stores_to_visit)

    if solution:
        print("--- Optimal Shopping Plan Found ---")
        print(f"Total Optimized Cost: ${solution['total_cost']:.2f}\n")

        for store in solution['stores']:
            print(f"Go to {store['store_name']} (ID: {store['store_id']}):")
            store_subtotal = 0
            for item in store['items']:
                print(f"  - Buy {item['product_name']} ({item['brand']}): ${item['price']:.2f}")
                store_subtotal += item['price']
            print(f"  Subtotal for {store['store_name']}: ${store_subtotal:.2f}\n")
    else:
        print("Could not find an optimal solution with the given constraints.")
        print("Try increasing the 'max_stores_to_visit' value in the script.")

if __name__ == "__main__":
    main()
