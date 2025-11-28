from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from companies.models import Store
from data_management.utils.cart_optimization import calculate_optimized_cost, calculate_baseline_cost, build_price_slots, calculate_best_single_store
from api.utils.get_pricing_stores import get_pricing_stores

from users.models import Cart

class CartOptimizationView(APIView):
    """
    API view to handle cart optimization requests.
    Accepts a cart_id and performs optimization based on the cart's contents and selected store list.
    """

    def post(self, request, *args, **kwargs):
        cart_id = request.data.get('cart_id')
        if not cart_id:
            return Response({'error': 'cart_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_obj = Cart.objects.prefetch_related(
                'items__product',
                'items__chosen_substitutions__substituted_product',
                'selected_store_list__stores'
            ).get(id=cart_id)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not cart_obj.selected_store_list:
            return Response({'error': 'Cart has no associated store list.'}, status=status.HTTP_400_BAD_REQUEST)

        store_ids = list(cart_obj.selected_store_list.stores.values_list('id', flat=True))
        if not store_ids:
            return Response({'error': 'No stores selected in the cart\'s store list.'}, status=status.HTTP_400_BAD_REQUEST)

        # Get the correct stores for pricing, including fallbacks to national anchors
        pricing_store_ids = get_pricing_stores(store_ids)
        stores = Store.objects.filter(id__in=pricing_store_ids)

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

        max_stores_options = request.data.get('max_stores_options', [2, 3, 4])

        # The original logic starts here, using the variables we just built
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
                                'shopping_plan': shopping_plan,
                            })
                subs_best_single_store = calculate_best_single_store(subs_price_slots, cart_with_substitutes_slots)
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
                            'shopping_plan': shopping_plan,
                        })
            
            no_subs_best_single_store = calculate_best_single_store(simple_price_slots, simple_cart)

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