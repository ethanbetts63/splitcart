import json
import pulp
import random


def calculate_single_store_costs(shopping_list, all_store_data):
    store_costs = {}
    for store in all_store_data["stores"]:
        store_name = store["name"]

        price_map = {}
        for product in store["products"]:
            price_map[product["name"]] = product["price"]

        total_cost = 0
        all_items_found = True
        for item in shopping_list:
            if item in price_map:
                total_cost += price_map[item]
            else:
                all_items_found = False
                break

        if all_items_found:
            store_costs[store_name] = total_cost

    return store_costs


def find_cheapest_combination(shopping_list, max_stores, all_store_data):
    # --- 1. SETUP ---
    store_names = []
    for store in all_store_data["stores"]:
        store_names.append(store["name"])

    prices = {}
    for store in all_store_data["stores"]:
        for product in store["products"]:
            prices[(product["name"], store["name"])] = product["price"]

    prob = pulp.LpProblem("GroceryOptimization", pulp.LpMinimize)

    # --- 2. DEFINE VARIABLES ---
    # 'item_assignments' will be 1 if we buy a specific item from a specific store, and 0 otherwise.
    item_assignments = pulp.LpVariable.dicts(
        "Assignment", (shopping_list, store_names), cat="Binary"
    )

    # 'store_usage' will be 1 if we decide to shop at a specific store at all, and 0 otherwise.
    store_usage = pulp.LpVariable.dicts("UseStore", store_names, cat="Binary")

    # --- 3. OBJECTIVE FUNCTION ---
    total_cost = pulp.lpSum(
        prices[(item, store)] * item_assignments[item][store]
        for item in shopping_list
        for store in store_names
    )

    prob += total_cost, "Total Cost of Items"

    # --- 4. DEFINE THE CONSTRAINTS ---

    # Rule 1: Each item on the shopping list must be purchased exactly once.
    for item in shopping_list:
        prob += (
            pulp.lpSum(item_assignments[item][store] for store in store_names) == 1,
            f"Buy_{item}_once",
        )

    # Rule 2: The number of stores used must be less than or equal to the max allowed.
    prob += (
        pulp.lpSum(store_usage[store] for store in store_names) <= max_stores,
        "Max_stores_limit",
    )

    # Rule 3: If any item is bought from a store, that store must be marked as "used".
    # This connects the 'item_assignments' and 'store_usage' variables.
    for store in store_names:
        for item in shopping_list:
            prob += (
                item_assignments[item][store] <= store_usage[store]
            ), f"Link_{item}_to_{store}"

    # --- 5. SOLVE THE PROBLEM AND RETURN THE RESULTS ---
    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    if pulp.LpStatus[prob.status] == "Optimal":
        final_cost = pulp.value(prob.objective)

        shopping_plan = {}
        for s in store_names:
            shopping_plan[s] = []

        for item in shopping_list:
            for store in store_names:
                if item_assignments[item][store].varValue == 1:
                    item_price = prices[(item, store)]
                    shopping_plan[store].append((item, item_price))
                    break

        return final_cost, shopping_plan
    else:
        return None, None


def main():
    # User Variables
    user_max_stores = 5
    num_items_to_select = 30

    try:
        with open("store_data.json", "r") as f:
            all_store_data = json.load(f)
    except FileNotFoundError:
        print(
            "Error: 'store_data.json' not found. Make sure the file is in the same directory."
        )
        exit()

    all_product_set = set()
    for s in all_store_data["stores"]:
        for p in s["products"]:
            all_product_set.add(p["name"])
    all_products = sorted(list(all_product_set))

    if num_items_to_select > len(all_products):
        print(
            f"Error: Cannot select {num_items_to_select} items, only {len(all_products)} unique items are available."
        )
        exit()

    user_shopping_list = random.sample(all_products, num_items_to_select)

    print("--- Single-Store Cost Analysis ---")
    single_store_costs = calculate_single_store_costs(
        user_shopping_list, all_store_data
    )
    if single_store_costs:
        sorted_stores = sorted(single_store_costs.items(), key=lambda item: item[1])
        for store, cost in sorted_stores:
            print(f"Total cost if buying all items at {store}: ${cost:.2f}")
    print("-------------------------------------\n")

    print("Finding the cheapest combination for your shopping list...")
    print(f"Items: {user_shopping_list}")
    print(f"Willing to visit a maximum of {user_max_stores} stores.\n")

    final_cost, shopping_plan = find_cheapest_combination(
        user_shopping_list, user_max_stores, all_store_data
    )

    if final_cost is not None:
        print("--- Optimal Shopping Plan Found ---")
        print(f"Total Optimized Cost: ${final_cost:.2f}\n")

        for store, items in shopping_plan.items():
            if items:
                print(f"Go to {store}:")
                store_subtotal = 0
                for item, price in items:
                    print(f"  - Buy {item}: ${price:.2f}")
                    store_subtotal += price
                print(f"  Subtotal for {store}: ${store_subtotal:.2f}\n")
    else:
        print("Could not find an optimal solution with the given constraints.")


if __name__ == "__main__":
    main()
