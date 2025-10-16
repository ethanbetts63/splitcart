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

    def _calculate_optimization(self, cart, stores, max_stores_options, original_cart):
        price_slots = build_price_slots(cart, stores)
        if not price_slots:
            return None, None, None

        optimization_results = []
        baseline_cost = calculate_baseline_cost(price_slots)

        # Calculate best single store option
        best_single_store_result = calculate_best_single_store(price_slots, original_cart)

        for max_stores in max_stores_options:
            optimized_cost, shopping_plan, _ = calculate_optimized_cost(price_slots, max_stores)
            if optimized_cost is not None:
                # Count stores that have items
                actual_stores_used = sum(1 for store_plan in shopping_plan.values() if store_plan['items'])

                # Only add the result if the number of stores used is what we asked for
                if actual_stores_used == max_stores:
                    savings = baseline_cost - optimized_cost if baseline_cost > 0 else 0
                    optimization_results.append({
                        'max_stores': max_stores,
                        'optimized_cost': optimized_cost,
                        'savings': savings,
                        'shopping_plan': shopping_plan,
                    })
        
        return baseline_cost, optimization_results, best_single_store_result

    def post(self, request, *args, **kwargs):

        cart = request.data.get('cart')
        store_ids = request.data.get('store_ids')
        original_items = request.data.get('original_items')
        max_stores_options = request.data.get('max_stores_options', [2, 3, 4])

        if not cart or not store_ids:
            return Response(
                {'error': 'Cart and store_ids data are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            stores = Store.objects.filter(id__in=store_ids)
            if not stores.exists():
                return Response(
                    {'error': 'Invalid store IDs provided.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Main calculation with substitutes
            baseline_cost, optimization_results, best_single_store = self._calculate_optimization(cart, stores, max_stores_options, cart)
            if baseline_cost is None:
                return Response(
                    {'error': 'Could not find prices for the items in your cart at the specified stores.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            response_data = {
                'baseline_cost': baseline_cost,
                'optimization_results': optimization_results,
                'best_single_store': best_single_store,
            }

            # "No subs" calculation
            if original_items:
                simple_cart = [[{'product_id': item['product']['id'], 'quantity': item['quantity']}] for item in original_items]
                no_subs_baseline, no_subs_results, no_subs_single_store = self._calculate_optimization(simple_cart, stores, max_stores_options, simple_cart)
                if no_subs_baseline is not None:
                    response_data['no_subs_results'] = {
                        'baseline_cost': no_subs_baseline,
                        'optimization_results': no_subs_results,
                        'best_single_store': no_subs_single_store,
                    }
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'An unexpected error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )