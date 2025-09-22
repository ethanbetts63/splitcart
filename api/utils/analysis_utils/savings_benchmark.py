import random
import pulp
import statistics
from collections import deque

from api.config import (
    SUBSTITUTION_SEARCH_DEPTH, 
    SUBSTITUTION_PORTFOLIO_CAP, 
    SUBSTITUTION_SIZE_TOLERANCE, 
    PRICE_CULLING_THRESHOLD
)

from django.db.models import Count, Q
from companies.models import Company, Store
from products.models import Product, Price, ProductSubstitution


def get_substitution_group(anchor_product, depth_limit=SUBSTITUTION_SEARCH_DEPTH):
    """
    Performs an intelligent graph traversal to find a high-quality group of substitutes.
    - Traverses only size-agnostic links (LVL1, 4, 5, 6).
    - Obeys a depth limit to prevent semantic drift.
    - Includes terminal size-constrained links (LVL2, 3) connected to any visited product.
    """
    transitive_levels = ['LVL1', 'LVL3', 'LVL4']
    terminal_levels = ['LVL2']

    # Use a queue for Breadth-First Search (BFS)
    queue = deque([(anchor_product.id, 0)])  # (product_id, depth)
    visited_ids = {anchor_product.id}
    group_ids = {anchor_product.id}

    # --- Step 1: Traverse the graph for the main group --- #
    while queue:
        current_id, current_depth = queue.popleft()

        if current_depth >= depth_limit:
            continue

        # Find neighbors through transitive links
        next_sub_relations = ProductSubstitution.objects.filter(
            (Q(product_a_id=current_id) | Q(product_b_id=current_id)) &
            Q(level__in=transitive_levels)
        ).select_related('product_a', 'product_b')

        for rel in next_sub_relations:
            neighbor_id = rel.product_b_id if rel.product_a_id == current_id else rel.product_a_id
            if neighbor_id not in visited_ids:
                visited_ids.add(neighbor_id)
                group_ids.add(neighbor_id)
                queue.append((neighbor_id, current_depth + 1))

    # --- Step 2: Add terminal substitutes for all products found in the main group --- #
    terminal_relations = ProductSubstitution.objects.filter(
        (Q(product_a_id__in=group_ids) | Q(product_b_id__in=group_ids)) &
        Q(level__in=terminal_levels)
    )
    for rel in terminal_relations:
        group_ids.add(rel.product_a_id)
        group_ids.add(rel.product_b_id)

    # Fetch all unique Product objects
    return Product.objects.filter(id__in=group_ids)


from api.utils.substitution_utils.size_comparer import SizeComparer

def generate_random_cart(stores, num_products):
    """Generates a random shopping cart using the intelligent portfolio selection algorithm."""
    # Get a pool of potential products that exist in the selected stores
    product_ids_in_stores = Price.objects.filter(store__in=stores).values_list('price_record__product_id', flat=True).distinct()
    
    if len(product_ids_in_stores) < num_products:
        return None, None

    random_product_ids = random.sample(list(product_ids_in_stores), num_products)
    anchor_products = Product.objects.filter(id__in=random_product_ids)

    # Pre-fetch all prices for all anchor products in the selected stores to avoid N+1 queries
    all_anchor_prices = Price.objects.filter(
        price_record__product__in=anchor_products,
        store__in=stores
    ).select_related('store', 'price_record')

    prices_by_product = {}
    for price in all_anchor_prices:
        product_id = price.price_record.product_id
        if product_id not in prices_by_product:
            prices_by_product[product_id] = []
        prices_by_product[product_id].append(price)

    all_slots = []
    size_comparer = SizeComparer()

    for anchor_product in anchor_products:
        # --- Step 0: Intelligent Graph Traversal ---
        full_sub_group = get_substitution_group(anchor_product)

        # --- New Step: Filter by Size Similarity ---
        size_compatible_group = []
        for sub in full_sub_group:
            # The anchor product is always considered compatible with itself
            if sub.id == anchor_product.id:
                size_compatible_group.append(sub)
                continue
            # Use a 30% tolerance for finding substitutes
            if size_comparer.are_sizes_compatible(anchor_product, sub, tolerance=SUBSTITUTION_SIZE_TOLERANCE):
                size_compatible_group.append(sub)

        # --- Step 1: Conditional Culling by Price ---
        anchor_prices = prices_by_product.get(anchor_product.id, [])
        if not anchor_prices:
            continue
        
        price_ceiling = min([p.price_record.price for p in anchor_prices if p.price_record])
        
        candidate_subs = []
        sub_prices = Price.objects.filter(price_record__product__in=size_compatible_group, store__in=stores).select_related('store', 'price_record')
        sub_prices_map = { (p.price_record.product_id, p.store_id): p for p in sub_prices }

        if len(size_compatible_group) > PRICE_CULLING_THRESHOLD:
            for sub in size_compatible_group:
                for store in stores:
                    price_obj = sub_prices_map.get((sub.id, store.id))
                    if price_obj and price_obj.price_record and price_obj.price_record.price <= price_ceiling:
                        candidate_subs.append((sub, price_obj))
        else:
            for sub in size_compatible_group:
                 for store in stores:
                    price_obj = sub_prices_map.get((sub.id, store.id))
                    if price_obj:
                        candidate_subs.append((sub, price_obj))

        if not candidate_subs:
            continue

        # --- Tiered Portfolio Selection ---
        final_options = []
        portfolio_cap = SUBSTITUTION_PORTFOLIO_CAP

        candidate_ids = {sub.id for sub, price in candidate_subs}
        sub_relations = ProductSubstitution.objects.filter(
            (Q(product_a__in=candidate_ids) & Q(product_b__in=candidate_ids))
        ).distinct()
        sub_relations_map = {}
        for rel in sub_relations:
            sub_relations_map[tuple(sorted((rel.product_a_id, rel.product_b_id)))] = rel

        def get_relation(prod_a, prod_b):
            return sub_relations_map.get(tuple(sorted((prod_a.id, prod_b.id))))

        # --- Step 2: Tier 1 Selection - The "Clones" ---
        clones = []
        for sub, price_obj in candidate_subs:
            relation = get_relation(anchor_product, sub)
            if relation and relation.level in ['LVL1', 'LVL2']:
                clones.append((sub, price_obj))
        
        final_options.extend(clones)
        candidate_subs = [c for c in candidate_subs if c not in clones]

        # --- Step 3: Tier 2 Selection - The "Ambassadors" ---
        if len(final_options) < portfolio_cap:
            ambassadors = {}
            # Find the store of the anchor product to correctly identify "other" stores
            anchor_store_id = anchor_prices[0].store.id
            other_stores = [s for s in stores if s.id != anchor_store_id]
            for store in other_stores:
                store_candidates = [(s, p) for s, p in candidate_subs if p.store_id == store.id]
                if not store_candidates:
                    continue
                
                best_ambassador = max(store_candidates, key=lambda x: get_relation(anchor_product, x[0]).score if get_relation(anchor_product, x[0]) else 0)
                ambassadors[store.id] = best_ambassador

            for amb in ambassadors.values():
                if amb not in final_options and len(final_options) < portfolio_cap:
                    final_options.append(amb)
            
            candidate_subs = [c for c in candidate_subs if c not in ambassadors.values()]

        # --- Step 4: Tier 3 Selection - The "Best of the Rest" ---
        if len(final_options) < portfolio_cap:
            candidate_subs.sort(key=lambda x: get_relation(anchor_product, x[0]).score if get_relation(anchor_product, x[0]) else 0, reverse=True)
            needed = portfolio_cap - len(final_options)
            for sub, price_obj in candidate_subs[:needed]:
                if (sub, price_obj) not in final_options:
                    final_options.append((sub, price_obj))

        # Format the final selected options for the solver
        current_slot = []
        # Ensure the anchor product itself is always an option, if priced
        anchor_price_obj = anchor_prices[0]
        final_options_products = [opt[0] for opt in final_options]
        if anchor_product not in final_options_products:
             final_options.append((anchor_product, anchor_price_obj))

        for product, price_obj in final_options:
            if not price_obj.price_record: continue
            current_slot.append({
                "product_id": product.id,
                "product_name": product.name,
                "brand": product.brand.name if product.brand else None,
                "sizes": product.sizes,
                "store_id": price_obj.store.id,
                "store_name": price_obj.store.store_name,
                "price": float(price_obj.price_record.price),
            })

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

        return final_cost, shopping_plan, choice_vars
    else:
        return None, None, None

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

        optimized_cost, _, _ = calculate_optimized_cost(slots, MAX_STORES_FOR_SOLVER)
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