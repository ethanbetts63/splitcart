import pytest
from decimal import Decimal
from companies.tests.factories import CompanyFactory, StoreFactory
from products.tests.factories import ProductFactory, PriceFactory
from products.utils.bargain_utils import calculate_bargains


@pytest.mark.django_db
class TestCalculateBargains:
    def test_empty_product_ids_returns_empty(self):
        store = StoreFactory()
        assert calculate_bargains([], [store.id]) == []

    def test_empty_store_ids_returns_empty(self):
        product = ProductFactory()
        assert calculate_bargains([product.id], []) == []

    def test_single_price_is_not_a_bargain(self):
        product = ProductFactory()
        store = StoreFactory()
        PriceFactory(product=product, store=store, price=Decimal('10.00'))

        result = calculate_bargains([product.id], [store.id])

        assert result == []

    def test_same_company_two_stores_is_not_a_bargain(self):
        company = CompanyFactory(name='Woolworths')
        product = ProductFactory()
        store1 = StoreFactory(company=company)
        store2 = StoreFactory(company=company)
        PriceFactory(product=product, store=store1, price=Decimal('10.00'))
        PriceFactory(product=product, store=store2, price=Decimal('7.00'))

        result = calculate_bargains([product.id], [store1.id, store2.id])

        assert result == []

    def test_cross_company_valid_bargain_returned(self):
        product = ProductFactory()
        store1 = StoreFactory(company=CompanyFactory(name='Woolworths'))
        store2 = StoreFactory(company=CompanyFactory(name='Coles'))
        PriceFactory(product=product, store=store1, price=Decimal('10.00'))
        PriceFactory(product=product, store=store2, price=Decimal('7.00'))

        result = calculate_bargains([product.id], [store1.id, store2.id])

        assert len(result) == 1
        assert result[0]['product_id'] == product.id
        assert result[0]['discount'] == 30  # ((10 - 7) / 10) * 100

    def test_discount_below_5_percent_excluded(self):
        product = ProductFactory()
        store1 = StoreFactory(company=CompanyFactory(name='Woolworths'))
        store2 = StoreFactory(company=CompanyFactory(name='Coles'))
        # 4% discount
        PriceFactory(product=product, store=store1, price=Decimal('10.00'))
        PriceFactory(product=product, store=store2, price=Decimal('9.61'))

        result = calculate_bargains([product.id], [store1.id, store2.id])

        assert result == []

    def test_discount_above_70_percent_excluded(self):
        product = ProductFactory()
        store1 = StoreFactory(company=CompanyFactory(name='Woolworths'))
        store2 = StoreFactory(company=CompanyFactory(name='Coles'))
        # 80% discount
        PriceFactory(product=product, store=store1, price=Decimal('10.00'))
        PriceFactory(product=product, store=store2, price=Decimal('2.00'))

        result = calculate_bargains([product.id], [store1.id, store2.id])

        assert result == []

    def test_same_price_across_companies_is_not_a_bargain(self):
        product = ProductFactory()
        store1 = StoreFactory(company=CompanyFactory(name='Woolworths'))
        store2 = StoreFactory(company=CompanyFactory(name='Coles'))
        PriceFactory(product=product, store=store1, price=Decimal('5.00'))
        PriceFactory(product=product, store=store2, price=Decimal('5.00'))

        result = calculate_bargains([product.id], [store1.id, store2.id])

        assert result == []

    def test_two_iga_stores_with_different_prices_is_a_bargain(self):
        iga = CompanyFactory(name='IGA')
        product = ProductFactory()
        store1 = StoreFactory(company=iga)
        store2 = StoreFactory(company=iga)
        PriceFactory(product=product, store=store1, price=Decimal('10.00'))
        PriceFactory(product=product, store=store2, price=Decimal('7.00'))

        result = calculate_bargains([product.id], [store1.id, store2.id])

        assert len(result) == 1

    def test_returns_correct_cheaper_store_name_and_company(self):
        product = ProductFactory()
        woolworths = CompanyFactory(name='Woolworths')
        coles = CompanyFactory(name='Coles')
        store1 = StoreFactory(company=woolworths, store_name='Woolworths Southbank')
        store2 = StoreFactory(company=coles, store_name='Coles CBD')
        PriceFactory(product=product, store=store1, price=Decimal('10.00'))
        PriceFactory(product=product, store=store2, price=Decimal('7.00'))

        result = calculate_bargains([product.id], [store1.id, store2.id])

        assert result[0]['cheaper_store_name'] == 'Coles CBD'
        assert result[0]['cheaper_company_name'] == 'Coles'

    def test_only_products_in_product_ids_are_checked(self):
        product_included = ProductFactory()
        product_excluded = ProductFactory()
        store1 = StoreFactory(company=CompanyFactory(name='Woolworths'))
        store2 = StoreFactory(company=CompanyFactory(name='Coles'))
        PriceFactory(product=product_included, store=store1, price=Decimal('10.00'))
        PriceFactory(product=product_included, store=store2, price=Decimal('7.00'))
        PriceFactory(product=product_excluded, store=store1, price=Decimal('10.00'))
        PriceFactory(product=product_excluded, store=store2, price=Decimal('7.00'))

        result = calculate_bargains([product_included.id], [store1.id, store2.id])

        returned_ids = {r['product_id'] for r in result}
        assert product_included.id in returned_ids
        assert product_excluded.id not in returned_ids
