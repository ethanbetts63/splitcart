from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from companies.models import Store
from data_management.utils.cart_optimization import calculate_optimized_cost, calculate_baseline_cost, build_price_slots

class CartOptimizationView(APIView):
    """
    API view to handle cart optimization requests.
    Accepts a list of product slots and a list of store IDs.
    """
    def post(self, request, *args, **kwargs):
        cart = request.data.get('cart')
        store_ids = request.data.get('store_ids')
        max_stores = request.data.get('max_stores', 3)

        if not cart or not store_ids:
            return Response(
                {'error': 'Cart and store_ids data are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Step 1: Get Store objects from the provided IDs
            stores = Store.objects.filter(id__in=store_ids)
            if not stores.exists():
                return Response(
                    {'error': 'Invalid store IDs provided.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Step 2: Build the detailed price slots for the optimizer
            price_slots = build_price_slots(cart, stores)
            if not price_slots:
                return Response(
                    {'error': 'Could not find prices for the items in your cart at the specified stores.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Step 3: Run the optimization and baseline calculation
            optimized_cost, shopping_plan, _ = calculate_optimized_cost(price_slots, max_stores)
            baseline_cost = calculate_baseline_cost(price_slots, stores)

            if optimized_cost is None:
                return Response(
                    {'error': 'Could not find an optimal shopping plan. Try increasing the number of stores or adding substitutes.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Step 4: Format and return the response
            savings = baseline_cost - optimized_cost if baseline_cost > 0 else 0

            response_data = {
                'optimized_cost': optimized_cost,
                'baseline_cost': baseline_cost,
                'savings': savings,
                'shopping_plan': shopping_plan,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            # Generic error handler for unexpected issues
            return Response(
                {'error': f'An unexpected error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
