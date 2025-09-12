import random
import pulp
import statistics

from django.db.models import Count, Q
from companies.models import Company, Store
from products.models import Product, Price, ProductSubstitution


def generate_random_cart(stores, num_products):
    """Generates a random shopping cart (slots data structure)."""
    product_ids_in_stores = Price.objects.filter(store__in=stores).values_list('product_id', flat=True).distinct()
    
    if len(product_ids_in_stores) < num_products:
        return None, None

    random_product_ids = random.sample(list(product_ids_in_stores), num_products)
    anchor_products = Product.objects.filter(id__in=random_product_ids)

    all_slots = []
    for anchor_product in anchor_products:
        # Start with the anchor product itself
        products_in_slot = {anchor_product}

        # Find all substitution relationships for the anchor product
        sub_relations = ProductSubstitution.objects.filter(
            Q(product_a=anchor_product) | Q(product_b=anchor_product)
        )

        # Collect all unique product IDs from those relationships
        substitute_ids = set()
        for rel in sub_relations:
            if rel.product_a_id == anchor_product.id:
                substitute_ids.add(rel.product_b_id)
            else:
                substitute_ids.add(rel.product_a_id)

        # Fetch the actual Product objects for the substitutes
        if substitute_ids:
            substitute_products = Product.objects.filter(id__in=substitute_ids)
            for sub in substitute_products:
                products_in_slot.add(sub)

        current_slot = []
        for product in products_in_slot:
            prices_in_stores = Price.objects.filter(product=product, store__in=stores)
            for price_obj in prices_in_stores:
                option = {
                    "product_id": product.id,
                    "product_name": product.name,
                    "brand": product.brand,
                    "store_id": price_obj.store.id,
                    "store_name": price_obj.store.store_name,
                    "price": float(price_obj.price),
                }
                current_slot.append(option)
        
        if current_slot:
            all_slots.append(current_slot)
    
    return all_slots, anchor_products

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
                    
                    plan_item = {
                        "product": f"{brand} {product_name}",
                        "price": price
                    }
                    shopping_plan[store_name].append(plan_item)
                    break

        return final_cost, shopping_plan
    else:
        return None, None

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

def run_savings_benchmark(file_path):
    """Main function to run the benchmark and write results to a file."""
    report_lines = []
    
    NUM_RUNS = 10
    PRODUCTS_PER_RUN = 100
    STORES_PER_RUN = 3
    MAX_STORES_FOR_SOLVER = 3 # Increased to 3 for more reliable results

    report_lines.append(f"Starting benchmark with {NUM_RUNS} runs...\n")
    
    all_savings = []

    viable_stores = Store.objects.annotate(num_prices=Count('prices')).filter(num_prices__gte=PRODUCTS_PER_RUN)
    if len(viable_stores) < STORES_PER_RUN:
        report_lines.append("Not enough viable stores in the database to run the benchmark.")
        with open(file_path, 'w') as f:
            f.write("\n".join(report_lines))
        return

    for i in range(NUM_RUNS):
        report_lines.append(f"--- Run {i + 1}/{NUM_RUNS} ---")
        
        selected_stores = random.sample(list(viable_stores), STORES_PER_RUN)
        slots = generate_random_cart(selected_stores, PRODUCTS_PER_RUN)
        if not slots:
            report_lines.append("Could not generate a valid cart for this run. Skipping.")
            continue

        optimized_cost = calculate_optimized_cost(slots, MAX_STORES_FOR_SOLVER)
        if optimized_cost is None:
            report_lines.append("Solver could not find an optimal solution. Skipping run.")
            continue

        baseline_cost = calculate_baseline_cost(slots, selected_stores)

        if baseline_cost > 0 and baseline_cost > optimized_cost:
            savings = ((baseline_cost - optimized_cost) / baseline_cost) * 100
            all_savings.append(savings)
            report_lines.append(f"Baseline: ${baseline_cost:.2f}, Optimized: ${optimized_cost:.2f}, Savings: {savings:.2f}%")
        else:
            all_savings.append(0)
            report_lines.append(f"Baseline: ${baseline_cost:.2f}, Optimized: ${optimized_cost:.2f}, Savings: 0.00%")

    report_lines.append("\n--- Benchmark Complete ---")
    report_lines.append(f"Individual savings percentages: {[f'{s:.2f}%' for s in all_savings]}")
    if all_savings:
        average_savings = statistics.mean(all_savings)
        report_lines.append(f"\nAverage Savings: {average_savings:.2f}%")
    else:
        report_lines.append("\nNo valid runs were completed.")

    with open(file_path, 'w') as f:
        f.write("\n".join(report_lines))
