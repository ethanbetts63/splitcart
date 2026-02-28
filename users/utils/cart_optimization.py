from rest_framework.response import Response
from rest_framework import status
from companies.models import Store
from data_management.utils.cart_optimization import calculate_optimized_cost, calculate_baseline_cost, build_price_slots, calculate_best_single_store
from products.utils.get_pricing_stores import get_pricing_stores_map
from users.models import Cart


def _translate_shopping_plan(shopping_plan, anchor_name_to_original):
    """
    Translates anchor store names/addresses in a shopping_plan back to the
    user's originally selected stores. Each plan entry gains a 'store_options'
    list of {store_name, store_address} dicts for user-facing display.

    When multiple selected stores share the same anchor (e.g. Coles prices
    nationally), all of them appear in store_options so the user knows they
    can shop at any of those locations.
    """
    translated = {}
    for anchor_name, plan_data in shopping_plan.items():
        originals = anchor_name_to_original.get(anchor_name, [])
        new_entry = dict(plan_data)
        if originals:
            store_options = []
            for s in originals:
                addr_parts = [s.address_line_1, s.suburb, s.state, s.postcode]
                store_options.append({
                    'store_name': s.store_name,
                    'store_address': ', '.join(part for part in addr_parts if part),
                })
            new_entry['store_options'] = store_options
            new_entry['store_address'] = store_options[0]['store_address']
            new_key = store_options[0]['store_name']
        else:
            new_entry['store_options'] = []
            new_key = anchor_name
        translated[new_key] = new_entry
    return translated


def run_cart_optimization(cart_obj, store_list, max_stores_options):
    """
    Performs optimization on a specific cart and returns a Response object.
    """
    if not store_list:
        return Response({'error': 'A store list is required for optimization.'}, status=status.HTTP_400_BAD_REQUEST)

    store_ids = list(store_list.stores.values_list('id', flat=True))
    if not store_ids:
        return Response({'error': 'No stores selected in the provided store list.'}, status=status.HTTP_400_BAD_REQUEST)

    # Get the correct stores for pricing, including fallbacks to national anchors
    pricing_map = get_pricing_stores_map(store_ids)
    pricing_store_ids = list(set(pricing_map.values()))
    stores = Store.objects.filter(id__in=pricing_store_ids)

    # Build reverse map: anchor_store_name -> [originally selected Store objects]
    # This lets us translate the shopping plan back to the stores the user actually selected.
    anchor_to_selected_ids = {}
    for selected_id, anchor_id in pricing_map.items():
        anchor_to_selected_ids.setdefault(anchor_id, []).append(selected_id)
    original_store_map = {s.id: s for s in Store.objects.filter(id__in=store_ids)}
    anchor_name_to_original = {
        anchor.store_name: [
            original_store_map[sid]
            for sid in anchor_to_selected_ids.get(anchor.id, [])
            if sid in original_store_map
        ]
        for anchor in stores
    }

    # Construct the data structures required by the optimization logic
    original_items = []
    cart_with_substitutes_slots = []
    for item in cart_obj.items.all():
        original_items.append({
            'product': {'id': item.product.id},
            'quantity': item.quantity
        })

        approved_subs = item.chosen_substitutions.filter(is_approved=True)
        slot = []
        if approved_subs.exists():
            # If substitutes are approved, the slot contains ONLY the substitutes
            for sub in approved_subs:
                slot.append({'product_id': sub.substituted_product.id, 'quantity': sub.quantity})
        else:
            # If no substitutes are approved, the slot contains the original item
            slot.append({'product_id': item.product.id, 'quantity': item.quantity})
        cart_with_substitutes_slots.append(slot)

    try:
        # 1. Calculate a single baseline cost based ONLY on original items
        simple_cart = [[{'product_id': item['product']['id'], 'quantity': item['quantity']}] for item in original_items]
        simple_price_slots = build_price_slots(simple_cart, stores)
        if not simple_price_slots:
            return Response(
                {'error': 'Could not find prices for the original items in your cart at the specified stores.'},
                status=status.HTTP_404_NOT_FOUND
            )
        baseline_cost = calculate_baseline_cost(simple_price_slots)

        # 2. "With Substitutes" calculation
        subs_price_slots = build_price_slots(cart_with_substitutes_slots, stores)
        subs_optimization_results = []
        if subs_price_slots:
            for max_stores in max_stores_options:
                optimized_cost, shopping_plan, _ = calculate_optimized_cost(subs_price_slots, max_stores)
                if optimized_cost is not None:
                    actual_stores_used = sum(1 for store_plan in shopping_plan.values() if store_plan['items'])
                    if actual_stores_used == max_stores:
                        savings = baseline_cost - optimized_cost if baseline_cost > 0 else 0
                        subs_optimization_results.append({
                            'max_stores': max_stores,
                            'optimized_cost': optimized_cost,
                            'savings': savings,
                            'shopping_plan': _translate_shopping_plan(shopping_plan, anchor_name_to_original),
                        })
            subs_best_single_store = calculate_best_single_store(subs_price_slots, cart_with_substitutes_slots)
            if subs_best_single_store:
                subs_best_single_store['shopping_plan'] = _translate_shopping_plan(
                    subs_best_single_store['shopping_plan'], anchor_name_to_original
                )
        else:
            subs_best_single_store = None

        response_data = {
            'baseline_cost': baseline_cost,
            'optimization_results': subs_optimization_results,
            'best_single_store': subs_best_single_store,
        }

        # 3. "No Substitutes" calculation
        no_subs_optimization_results = []
        for max_stores in max_stores_options:
            optimized_cost, shopping_plan, _ = calculate_optimized_cost(simple_price_slots, max_stores)
            if optimized_cost is not None:
                actual_stores_used = sum(1 for store_plan in shopping_plan.values() if store_plan['items'])
                if actual_stores_used == max_stores:
                    savings = baseline_cost - optimized_cost if baseline_cost > 0 else 0
                    no_subs_optimization_results.append({
                        'max_stores': max_stores,
                        'optimized_cost': optimized_cost,
                        'savings': savings,
                        'shopping_plan': _translate_shopping_plan(shopping_plan, anchor_name_to_original),
                    })

        no_subs_best_single_store = calculate_best_single_store(simple_price_slots, simple_cart)
        if no_subs_best_single_store:
            no_subs_best_single_store['shopping_plan'] = _translate_shopping_plan(
                no_subs_best_single_store['shopping_plan'], anchor_name_to_original
            )

        response_data['no_subs_results'] = {
            'baseline_cost': baseline_cost, # Use the same baseline
            'optimization_results': no_subs_optimization_results,
            'best_single_store': no_subs_best_single_store,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'An unexpected error occurred: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
