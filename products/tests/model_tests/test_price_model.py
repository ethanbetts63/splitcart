import pytest
from decimal import Decimal
from products.models import Price
from products.tests.factories import ProductFactory, PriceFactory
from companies.tests.factories import CompanyFactory


@pytest.mark.django_db
class TestPriceModel:
    def test_str_format(self):
        product = ProductFactory(name='Weet-Bix', brand=None, size=None)
        company = CompanyFactory(name='Woolworths')
        price = PriceFactory(product=product, company=company, price=Decimal('5.50'))
        assert 'Weet-Bix' in str(price)
        assert 'Woolworths' in str(price)
        assert '5.50' in str(price)
