import pytest
from decimal import Decimal
from companies.tests.factories import CompanyFactory
from products.tests.factories import ProductFactory, PriceFactory
from products.utils.bargain_utils import calculate_bargains


@pytest.mark.django_db
class TestCalculateBargains:
    def test_empty_product_ids_returns_empty(self):
        company = CompanyFactory()
        assert calculate_bargains([], [company.id]) == []

    def test_empty_company_ids_returns_empty(self):
        product = ProductFactory()
        assert calculate_bargains([product.id], []) == []

    def test_single_price_is_not_a_bargain(self):
        product = ProductFactory()
        company = CompanyFactory()
        PriceFactory(product=product, company=company, price=Decimal('10.00'))

        result = calculate_bargains([product.id], [company.id])

        assert result == []

    def test_single_company_two_prices_is_not_a_bargain(self):
        company = CompanyFactory(name='Woolworths')
        product = ProductFactory()
        PriceFactory(product=product, company=company, price=Decimal('10.00'))

        result = calculate_bargains([product.id], [company.id])

        assert result == []

    def test_cross_company_valid_bargain_returned(self):
        product = ProductFactory()
        woolworths = CompanyFactory(name='Woolworths')
        coles = CompanyFactory(name='Coles')
        PriceFactory(product=product, company=woolworths, price=Decimal('10.00'))
        PriceFactory(product=product, company=coles, price=Decimal('7.00'))

        result = calculate_bargains([product.id], [woolworths.id, coles.id])

        assert len(result) == 1
        assert result[0]['product_id'] == product.id
        assert result[0]['discount'] == 30  # ((10 - 7) / 10) * 100

    def test_discount_below_5_percent_excluded(self):
        product = ProductFactory()
        woolworths = CompanyFactory(name='Woolworths')
        coles = CompanyFactory(name='Coles')
        # 4% discount
        PriceFactory(product=product, company=woolworths, price=Decimal('10.00'))
        PriceFactory(product=product, company=coles, price=Decimal('9.61'))

        result = calculate_bargains([product.id], [woolworths.id, coles.id])

        assert result == []

    def test_discount_above_70_percent_excluded(self):
        product = ProductFactory()
        woolworths = CompanyFactory(name='Woolworths')
        coles = CompanyFactory(name='Coles')
        # 80% discount
        PriceFactory(product=product, company=woolworths, price=Decimal('10.00'))
        PriceFactory(product=product, company=coles, price=Decimal('2.00'))

        result = calculate_bargains([product.id], [woolworths.id, coles.id])

        assert result == []

    def test_same_price_across_companies_is_not_a_bargain(self):
        product = ProductFactory()
        woolworths = CompanyFactory(name='Woolworths')
        coles = CompanyFactory(name='Coles')
        PriceFactory(product=product, company=woolworths, price=Decimal('5.00'))
        PriceFactory(product=product, company=coles, price=Decimal('5.00'))

        result = calculate_bargains([product.id], [woolworths.id, coles.id])

        assert result == []

    def test_returns_correct_cheaper_company(self):
        product = ProductFactory()
        woolworths = CompanyFactory(name='Woolworths')
        coles = CompanyFactory(name='Coles')
        PriceFactory(product=product, company=woolworths, price=Decimal('10.00'))
        PriceFactory(product=product, company=coles, price=Decimal('7.00'))

        result = calculate_bargains([product.id], [woolworths.id, coles.id])

        assert result[0]['cheaper_company_name'] == 'Coles'

    def test_only_products_in_product_ids_are_checked(self):
        product_included = ProductFactory()
        product_excluded = ProductFactory()
        woolworths = CompanyFactory(name='Woolworths')
        coles = CompanyFactory(name='Coles')
        PriceFactory(product=product_included, company=woolworths, price=Decimal('10.00'))
        PriceFactory(product=product_included, company=coles, price=Decimal('7.00'))
        PriceFactory(product=product_excluded, company=woolworths, price=Decimal('10.00'))
        PriceFactory(product=product_excluded, company=coles, price=Decimal('7.00'))

        result = calculate_bargains([product_included.id], [woolworths.id, coles.id])

        returned_ids = {r['product_id'] for r in result}
        assert product_included.id in returned_ids
        assert product_excluded.id not in returned_ids
