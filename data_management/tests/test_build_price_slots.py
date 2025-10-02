from django.test import TestCase
from companies.tests.test_helpers.model_factories import StoreFactory
from data_management.utils.cart_optimization.build_price_slots import build_price_slots
from products.tests.test_helpers.model_factories import ProductFactory, PriceFactory

class BuildPriceSlotsTest(TestCase):
    def test_build_price_slots_with_substitutes(self):
        # 1. Setup
        # Create stores
        store1 = StoreFactory()
        store2 = StoreFactory()

        # Create products
        original_product = ProductFactory()
        substitute_product_1 = ProductFactory()
        substitute_product_2 = ProductFactory()

        # Create prices for each product at each store
        PriceFactory(price_record__product=original_product, store=store1, price_record__price=10.00)
        PriceFactory(price_record__product=original_product, store=store2, price_record__price=11.00)
        PriceFactory(price_record__product=substitute_product_1, store=store1, price_record__price=9.00)
        PriceFactory(price_record__product=substitute_product_1, store=store2, price_record__price=9.50)
        PriceFactory(price_record__product=substitute_product_2, store=store1, price_record__price=12.00)
        PriceFactory(price_record__product=substitute_product_2, store=store2, price_record__price=12.50)

        # Define the cart structure with substitutes in one slot
        cart = [
            [
                {"product_id": original_product.id, "quantity": 1},
                {"product_id": substitute_product_1.id, "quantity": 1},
                {"product_id": substitute_product_2.id, "quantity": 1},
            ]
        ]
        stores = [store1, store2]

        # 2. Execute
        price_slots = build_price_slots(cart, stores)

        # 3. Assert
        # There should be one slot for the one item group in the cart
        self.assertEqual(len(price_slots), 1)

        # The single slot should contain 6 options (3 products x 2 stores)
        slot = price_slots[0]
        self.assertEqual(len(slot), 6)

        # Check that all product-store combinations are present
        product_ids_in_slot = {item['product_id'] for item in slot}
        store_ids_in_slot = {item['store_id'] for item in slot}

        self.assertEqual(product_ids_in_slot, {original_product.id, substitute_product_1.id, substitute_product_2.id})
        self.assertEqual(store_ids_in_slot, {store1.id, store2.id})

        # Check a specific price to ensure data is correct
    def test_build_price_slots_multiple_slots(self):
        # 1. Setup
        # Create stores
        store1 = StoreFactory()
        store2 = StoreFactory()

        # Create products
        product1 = ProductFactory()
        product2 = ProductFactory()
        product3 = ProductFactory()
        product4 = ProductFactory()

        # Create prices for each product at each store
        PriceFactory(price_record__product=product1, store=store1, price_record__price=10.00)
        PriceFactory(price_record__product=product1, store=store2, price_record__price=11.00)
        PriceFactory(price_record__product=product2, store=store1, price_record__price=20.00)
        PriceFactory(price_record__product=product2, store=store2, price_record__price=21.00)
        PriceFactory(price_record__product=product3, store=store1, price_record__price=30.00)
        PriceFactory(price_record__product=product3, store=store2, price_record__price=31.00)
        PriceFactory(price_record__product=product4, store=store1, price_record__price=40.00)
        PriceFactory(price_record__product=product4, store=store2, price_record__price=41.00)

        # Define the cart structure with multiple slots
        cart = [
            [{"product_id": product1.id, "quantity": 1}],
            [{"product_id": product2.id, "quantity": 1}],
            [{"product_id": product3.id, "quantity": 1}],
            [{"product_id": product4.id, "quantity": 1}],
        ]
        stores = [store1, store2]

        # 2. Execute
        price_slots = build_price_slots(cart, stores)

        # 3. Assert
        # There should be four slots for the four item groups in the cart
        self.assertEqual(len(price_slots), 4)

        # Check the contents of each slot
        self.assertEqual(len(price_slots[0]), 2)
        self.assertEqual(price_slots[0][0]['product_id'], product1.id)
        self.assertEqual(len(price_slots[1]), 2)
        self.assertEqual(price_slots[1][0]['product_id'], product2.id)
        self.assertEqual(len(price_slots[2]), 2)
        self.assertEqual(price_slots[2][0]['product_id'], product3.id)
        self.assertEqual(len(price_slots[3]), 2)
        self.assertEqual(price_slots[3][0]['product_id'], product4.id)