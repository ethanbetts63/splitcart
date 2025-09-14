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

        # --- New logic for selecting sensible, random substitutes ---

        # First, find the cheapest price for the anchor product across all stores to set a ceiling.
        anchor_prices = Price.objects.filter(product=anchor_product, store__in=stores).values_list('price', flat=True)
        min_anchor_price = min([float(p) for p in anchor_prices]) if anchor_prices else float('inf')

        # Set the price ceiling at 110% of the cheapest anchor price.
        price_ceiling = min_anchor_price * 1.10

        current_slot = []
        # For each store, find sensible substitutes and pick up to 3 at random.
        for store in stores:
            sensible_options = []
            # Check all products in the slot (anchor + all its substitutes)
            for product in products_in_slot:
                # Use .filter().first() to safely get the most recent price, handling duplicates.
                price_obj = Price.objects.filter(product=product, store=store).first()

                if price_obj:
                    price = float(price_obj.price)
                    # Only consider options under the price ceiling
                    if price <= price_ceiling:
                        sensible_options.append({
                            "product_id": product.id,
                            "product_name": product.name,
                            "brand": product.brand,
                            "store_id": store.id,
                            "store_name": store.store_name,
                            "price": price,
                        })
            
            # Shuffle the sensible options and select up to 3.
            random.shuffle(sensible_options)
            current_slot.extend(sensible_options[:3])

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
    
    NUM_RUNS = 50
    PRODUCTS_PER_RUN = 100

    report_lines.append(f"Starting benchmark with {NUM_RUNS} runs...\n")
    
    all_savings = []

    for i in range(NUM_RUNS):
        report_lines.append(f"--- Run {i + 1}/{NUM_RUNS} ---")
        
        # Select one viable store from each company for the run.
        selected_stores = []
        all_companies = Company.objects.all()

        for company in all_companies:
            viable_stores_for_company = Store.objects.filter(
                company=company
            ).annotate(
                num_prices=Count('prices')
            ).filter(
                num_prices__gte=PRODUCTS_PER_RUN
            )

            if viable_stores_for_company.exists():
                random_store = random.choice(list(viable_stores_for_company))
                selected_stores.append(random_store)

        if len(selected_stores) < 2:
            report_lines.append("Not enough companies with viable stores to run a comparison. Skipping run.")
            continue

        MAX_STORES_FOR_SOLVER = len(selected_stores)

        slots, anchor_products = generate_random_cart(selected_stores, PRODUCTS_PER_RUN)
        if not slots or not anchor_products:
            report_lines.append("Could not generate a valid cart for this run. Skipping.")
            continue

        # --- Run Analysis --- #
        num_slots = len(slots)
        total_options = sum(len(slot) for slot in slots)
        avg_options_per_slot = total_options / num_slots if num_slots > 0 else 0
        
        slots_with_brand_subs = 0
        total_price_range = 0
        
        for slot in slots:
            if not slot:
                continue
            
            brands = {option['brand'] for option in slot}
            if len(brands) > 1:
                slots_with_brand_subs += 1
            
            prices = [option['price'] for option in slot]
            if len(prices) > 1:
                total_price_range += max(prices) - min(prices)
            
        avg_price_range = total_price_range / num_slots if num_slots > 0 else 0

        cheapest_store_wins = {}
        for slot in slots:
            if not slot:
                continue
            cheapest_option = min(slot, key=lambda x: x['price'])
            winner_store = cheapest_option['store_name']
            cheapest_store_wins[winner_store] = cheapest_store_wins.get(winner_store, 0) + 1
        
        distribution_str = ", ".join(sorted([f"{store}: {count}" for store, count in cheapest_store_wins.items()]))

        avg_ideal_item_price = 0
        if num_slots > 0:
            ideal_cost = 0
            for slot in slots:
                if slot:
                    ideal_cost += min(option['price'] for option in slot)
            avg_ideal_item_price = ideal_cost / num_slots
        # --- End Analysis --- #

        optimized_cost, _ = calculate_optimized_cost(slots, MAX_STORES_FOR_SOLVER)
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

        # Final metrics calculations
        avg_baseline_item_price = baseline_cost / num_slots if num_slots > 0 else 0
        avg_optimized_item_price = optimized_cost / num_slots if num_slots > 0 else 0

        report_lines.append("  Run Characteristics:")
        report_lines.append(f"    - Avg Options per Item: {avg_options_per_slot:.2f}")
        report_lines.append(f"    - Items with Brand Subs: {slots_with_brand_subs} / {num_slots}")
        report_lines.append(f"    - Avg Price Range per Item: ${avg_price_range:.2f}")
        report_lines.append(f"    - Cheapest Store Dist: ({distribution_str})")
        report_lines.append(f"    - Avg Ideal Item Price: ${avg_ideal_item_price:.2f}")
        report_lines.append(f"    - Avg Baseline Item Price: ${avg_baseline_item_price:.2f}")
        report_lines.append(f"    - Avg Optimized Item Price: ${avg_optimized_item_price:.2f}")

    report_lines.append("\n--- Benchmark Complete ---")
    report_lines.append(f"Individual savings percentages: {[f'{s:.2f}%' for s in all_savings]}")
    if all_savings:
        average_savings = statistics.mean(all_savings)
        report_lines.append(f"\nAverage Savings: {average_savings:.2f}%")
    else:
        report_lines.append("\nNo valid runs were completed.")

    with open(file_path, 'w') as f:
        f.write("\n".join(report_lines))
