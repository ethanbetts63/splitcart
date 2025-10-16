from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from companies.models import Store
from data_management.utils.cart_optimization import calculate_optimized_cost, calculate_baseline_cost, build_price_slots, calculate_best_single_store

class CartOptimizationView(APIView):
    """
    API view to handle cart optimization requests.
    Accepts a list of product slots and a list of store IDs.
    """

    def post(self, request, *args, **kwargs):
        cart = request.data.get('cart')
        store_ids = request.data.get('store_ids')
        original_items = request.data.get('original_items')
        max_stores_options = request.data.get('max_stores_options', [2, 3, 4])

        if not cart or not store_ids or not original_items:
            return Response(
                {'error': 'Cart, store_ids, and original_items data are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            stores = Store.objects.filter(id__in=store_ids)
            if not stores.exists():
                return Response(
                    {'error': 'Invalid store IDs provided.'},
                    status=status.HTTP_404_NOT_FOUND
                )

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
            subs_price_slots = build_price_slots(cart, stores)
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
                subs_best_single_store = calculate_best_single_store(subs_price_slots, cart)
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