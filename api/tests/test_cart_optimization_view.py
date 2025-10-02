
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from companies.tests.test_helpers.model_factories import StoreFactory
from products.tests.test_helpers.model_factories import ProductFactory, PriceFactory

class CartOptimizationViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_cart_optimization_view_multiple_options(self):
        # 1. Setup
        # Create stores
        store1 = StoreFactory()
        store2 = StoreFactory()
        store3 = StoreFactory()

        # Create products
        product1 = ProductFactory()
        product2 = ProductFactory()
        product3 = ProductFactory()

        # Create prices
        PriceFactory(price_record__product=product1, store=store1, price_record__price=10.00)
        PriceFactory(price_record__product=product1, store=store2, price_record__price=11.00)
        PriceFactory(price_record__product=product2, store=store2, price_record__price=20.00)
        PriceFactory(price_record__product=product2, store=store3, price_record__price=21.00)
        PriceFactory(price_record__product=product3, store=store1, price_record__price=30.00)
        PriceFactory(price_record__product=product3, store=store3, price_record__price=31.00)

        # Define cart and other request data
        cart = [
            [{'product_id': product1.id, 'quantity': 1}],
            [{'product_id': product2.id, 'quantity': 1}],
            [{'product_id': product3.id, 'quantity': 1}],
        ]
        store_ids = [store1.id, store2.id, store3.id]
        max_stores_options = [2, 3]

        # 2. Execute
        url = reverse('cart-optimization')
        response = self.client.post(url, {
            'cart': cart,
            'store_ids': store_ids,
            'max_stores_options': max_stores_options
        }, format='json')

        # 3. Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the overall structure of the response
        self.assertIn('baseline_cost', response.data)
        self.assertIn('optimization_results', response.data)

        # Check the optimization_results
        results = response.data['optimization_results']
        self.assertEqual(len(results), 2)

        # Check the result for max_stores = 2
        result_2_stores = next(r for r in results if r['max_stores'] == 2)
        self.assertIsNotNone(result_2_stores)
        self.assertEqual(result_2_stores['optimized_cost'], 10 + 20 + 31) # P1@S1, P2@S2, P3@S3 (forced trip)

        # Check the result for max_stores = 3
        result_3_stores = next(r for r in results if r['max_stores'] == 3)
        self.assertIsNotNone(result_3_stores)
        self.assertEqual(result_3_stores['optimized_cost'], 10 + 20 + 30) # P1@S1, P2@S2, P3@S1
