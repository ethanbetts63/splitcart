import random
import statistics
from collections import deque

from data_management.config import (
    SUBSTITUTION_SEARCH_DEPTH, 
    SUBSTITUTION_PORTFOLIO_CAP, 
    SUBSTITUTION_SIZE_TOLERANCE, 
    PRICE_CULLING_THRESHOLD
)

from django.db.models import Count, Q
from companies.models import Company, Store
from products.models import Product, Price, ProductSubstitution
from data_management.utils.substitution_utils.size_comparer import SizeComparer
from data_management.utils.cart_optimization import calculate_optimized_cost, calculate_baseline_cost, build_price_slots

def get_substitution_group(anchor_product, depth_limit=SUBSTITUTION_SEARCH_DEPTH):
    """
    Performs an intelligent graph traversal to find a high-quality group of substitutes.
    """
    transitive_levels = ['LVL1', 'LVL3', 'LVL4']
    terminal_levels = ['LVL2']

    queue = deque([(anchor_product.id, 0)])
    visited_ids = {anchor_product.id}
    group_ids = {anchor_product.id}

    while queue:
        current_id, current_depth = queue.popleft()

        if current_depth >= depth_limit:
            continue

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

    terminal_relations = ProductSubstitution.objects.filter(
        (Q(product_a_id__in=group_ids) | Q(product_b_id__in=group_ids)) &
        Q(level__in=terminal_levels)
    )
    for rel in terminal_relations:
        group_ids.add(rel.product_a_id)
        group_ids.add(rel.product_b_id)

    return Product.objects.filter(id__in=group_ids)

def generate_random_cart(stores, num_products):
    """Generates a random shopping cart using the intelligent portfolio selection algorithm."""
    product_ids_in_stores = Price.objects.filter(store__in=stores).values_list('price_record__product_id', flat=True).distinct()
    
    if len(product_ids_in_stores) < num_products:
        return None, None

    random_product_ids = random.sample(list(product_ids_in_stores), num_products)
    anchor_products = Product.objects.filter(id__in=random_product_ids)

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
        full_sub_group = get_substitution_group(anchor_product)

        size_compatible_group = []
        for sub in full_sub_group:
            if sub.id == anchor_product.id:
                size_compatible_group.append(sub)
                continue
            if size_comparer.are_sizes_compatible(anchor_product, sub, tolerance=SUBSTITUTION_SIZE_TOLERANCE):
                size_compatible_group.append(sub)

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

        clones = []
        for sub, price_obj in candidate_subs:
            relation = get_relation(anchor_product, sub)
            if relation and relation.level in ['LVL1', 'LVL2']:
                clones.append((sub, price_obj))
        
        final_options.extend(clones)
        candidate_subs = [c for c in candidate_subs if c not in clones]

        if len(final_options) < portfolio_cap:
            ambassadors = {}
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

        if len(final_options) < portfolio_cap:
            candidate_subs.sort(key=lambda x: get_relation(anchor_product, x[0]).score if get_relation(anchor_product, x[0]) else 0, reverse=True)
            needed = portfolio_cap - len(final_options)
            for sub, price_obj in candidate_subs[:needed]:
                if (sub, price_obj) not in final_options:
                    final_options.append((sub, price_obj))

        current_slot = []
        anchor_price_obj = anchor_prices[0]
        final_options_products = [opt[0] for opt in final_options]
        if anchor_product not in final_options_products:
             final_options.append((anchor_product, anchor_price_obj))

        for product, price_obj in final_options:
            if not price_obj.price_record: continue
            address_parts = [
                price_obj.store.address_line_1,
                price_obj.store.suburb,
                price_obj.store.state,
                price_obj.store.postcode
            ]
            store_address = ", ".join(part for part in address_parts if part)

            company_name = price_obj.store.company.name
            image_urls_by_company = {k.lower(): v for k, v in product.image_url_pairs}
            image_url = image_urls_by_company.get(company_name.lower())

            current_slot.append({
                "product_id": product.id,
                "product_name": product.name,
                "brand": product.brand.name if product.brand else None,
                "size": product.size,
                "store_id": price_obj.store.id,
                "store_name": price_obj.store.store_name,
                "company_name": company_name,
                "store_address": store_address,
                "price": float(price_obj.price_record.price),
                "quantity": 1,
                "image_url": image_url,
            })

        if current_slot:
            all_slots.append(current_slot)
    
    return all_slots, anchor_products

def run_savings_benchmark(file_path):
    """Main function to run the benchmark and write results to a file."""
    report_lines = []
    
    NUM_RUNS = 10
    PRODUCTS_PER_RUN = 20

    report_lines.append(f"Starting benchmark with {NUM_RUNS} runs of {PRODUCTS_PER_RUN} products each...\n")
    
    all_savings_with_subs = []
    all_savings_no_subs = []

    for i in range(NUM_RUNS):
        report_lines.append(f"--- Run {i + 1}/{NUM_RUNS} ---")
        
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

        slots_with_subs, anchor_products = generate_random_cart(selected_stores, PRODUCTS_PER_RUN)
        if not slots_with_subs or not anchor_products:
            report_lines.append("Could not generate a valid cart for this run. Skipping.")
            continue

        # --- Calculation with subs ---
        baseline_cost_with_subs = calculate_baseline_cost(slots_with_subs)
        optimized_cost_with_subs, _, _ = calculate_optimized_cost(slots_with_subs, MAX_STORES_FOR_SOLVER)
        
        if baseline_cost_with_subs > 0 and optimized_cost_with_subs is not None:
            savings_with_subs = ((baseline_cost_with_subs - optimized_cost_with_subs) / baseline_cost_with_subs) * 100
            all_savings_with_subs.append(savings_with_subs)
            report_lines.append(f"With Subs -> Baseline: ${baseline_cost_with_subs:.2f}, Optimized: ${optimized_cost_with_subs:.2f}, Savings: {savings_with_subs:.2f}%")
        else:
            all_savings_with_subs.append(0)
            report_lines.append(f"With Subs -> Baseline: ${baseline_cost_with_subs:.2f}, Optimized: ${optimized_cost_with_subs if optimized_cost_with_subs is not None else 'N/A'}, Savings: 0.00%")

        # --- Calculation without subs ---
        simple_cart = [[{'product_id': p.id, 'quantity': 1}] for p in anchor_products]
        slots_no_subs = build_price_slots(simple_cart, selected_stores)

        if slots_no_subs:
            baseline_cost_no_subs = calculate_baseline_cost(slots_no_subs)
            optimized_cost_no_subs, _, _ = calculate_optimized_cost(slots_no_subs, MAX_STORES_FOR_SOLVER)

            if baseline_cost_no_subs > 0 and optimized_cost_no_subs is not None:
                savings_no_subs = ((baseline_cost_no_subs - optimized_cost_no_subs) / baseline_cost_no_subs) * 100
                all_savings_no_subs.append(savings_no_subs)
                report_lines.append(f"No Subs   -> Baseline: ${baseline_cost_no_subs:.2f}, Optimized: ${optimized_cost_no_subs:.2f}, Savings: {savings_no_subs:.2f}%")
            else:
                all_savings_no_subs.append(0)
                report_lines.append(f"No Subs   -> Baseline: ${baseline_cost_no_subs:.2f}, Optimized: ${optimized_cost_no_subs if optimized_cost_no_subs is not None else 'N/A'}, Savings: 0.00%")
        else:
            all_savings_no_subs.append(0)
            report_lines.append("No Subs   -> Could not find prices for original items.")

    report_lines.append("\n--- Benchmark Complete ---")
    if all_savings_with_subs:
        average_savings_with_subs = statistics.mean(all_savings_with_subs)
        report_lines.append(f"Average Savings with Substitutes: {average_savings_with_subs:.2f}%")
    if all_savings_no_subs:
        average_savings_no_subs = statistics.mean(all_savings_no_subs)
        report_lines.append(f"Average Savings on Original Items Only: {average_savings_no_subs:.2f}%")

    with open(file_path, 'w') as f:
        f.write("\n".join(report_lines))