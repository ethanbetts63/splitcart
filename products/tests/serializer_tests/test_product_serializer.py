"""`ProductSerializer` -- the product payload every public screen renders.

It is the busiest serializer in the repository: five computed fields, four
supermarket-specific image rules, and a bargain badge whose text comes from a
map the view puts in the context. None of it was covered.
"""

from decimal import Decimal

import pytest
from django.utils.text import slugify

from companies.tests.factories import CompanyFactory
from products.models import SKU
from products.serializers.product_serializer import ProductSerializer
from products.tests.factories import PriceFactory, ProductBrandFactory, ProductFactory


@pytest.mark.django_db
class TestProductIdentity:
    def test_the_slug_is_the_name_and_the_id(self, db):
        """The frontend's `/product/[slug]` route parses the trailing id back
        out, so the two halves have to stay in this order."""
        product = ProductFactory(name='Full Cream Milk 2L')

        data = ProductSerializer(product).data

        assert data['slug'] == f'{slugify("Full Cream Milk 2L")}-{product.id}'

    def test_a_name_with_punctuation_still_makes_a_usable_slug(self, db):
        product = ProductFactory(name="Sam's Choice — Tea & Biscuits")

        assert ' ' not in ProductSerializer(product).data['slug']

    def test_the_brand_name_comes_from_the_first_scraped_pair(self, db):
        """`brand` is the canonical record; `brand_name_company_pairs` is what
        the supermarkets actually printed, and that is what gets shown."""
        product = ProductFactory(
            brand=ProductBrandFactory(name='Canonical Dairy'),
            brand_name_company_pairs=[['Farm Fresh', 'Coles'], ['FarmFresh', 'Aldi']],
        )

        assert ProductSerializer(product).data['brand_name'] == 'Farm Fresh'

    def test_a_product_with_no_scraped_brand_reports_none(self, db):
        product = ProductFactory(brand_name_company_pairs=[])

        assert ProductSerializer(product).data['brand_name'] is None


@pytest.mark.django_db
class TestPrices:
    def test_a_product_with_no_prices_reports_an_empty_list(self, db):
        assert ProductSerializer(ProductFactory()).data['prices'] == []

    def test_prices_are_listed_cheapest_first(self, db):
        product = ProductFactory()
        PriceFactory(
            product=product,
            company=CompanyFactory(name='Expensive Grocer'),
            price=Decimal('9.00'),
        )
        PriceFactory(
            product=product,
            company=CompanyFactory(name='Cheap Grocer'),
            price=Decimal('2.00'),
        )

        prices = ProductSerializer(product).data['prices']

        assert [row['company'] for row in prices] == ['Cheap Grocer', 'Expensive Grocer']

    def test_only_the_cheapest_is_flagged_lowest(self, db):
        product = ProductFactory()
        PriceFactory(product=product, company=CompanyFactory(name='A'), price=Decimal('9.00'))
        PriceFactory(product=product, company=CompanyFactory(name='B'), price=Decimal('2.00'))

        prices = ProductSerializer(product).data['prices']

        assert [row['is_lowest'] for row in prices] == [True, False]

    def test_a_tie_flags_both(self, db):
        """Two supermarkets at the same price are both the lowest; picking one
        arbitrarily would show a badge that moves between page loads."""
        product = ProductFactory()
        PriceFactory(product=product, company=CompanyFactory(name='A'), price=Decimal('2.00'))
        PriceFactory(product=product, company=CompanyFactory(name='B'), price=Decimal('2.00'))

        prices = ProductSerializer(product).data['prices']

        assert [row['is_lowest'] for row in prices] == [True, True]

    def test_the_price_is_rendered_to_two_decimals(self, db):
        product = ProductFactory()
        PriceFactory(product=product, company=CompanyFactory(name='A'), price=Decimal('2.5'))

        assert ProductSerializer(product).data['prices'][0]['price_display'] == '2.50'

    def test_a_missing_unit_price_string_is_null_not_empty(self, db):
        product = ProductFactory()
        PriceFactory(
            product=product,
            company=CompanyFactory(name='A'),
            price=Decimal('2.00'),
            per_unit_price_string='',
        )

        assert ProductSerializer(product).data['prices'][0]['per_unit_price_string'] is None


@pytest.mark.django_db
class TestImageUrls:
    """Four supermarkets, four rules. Each is a string the browser either loads
    or shows as a broken tile, so each is worth stating."""

    def test_aldi_images_hang_off_the_product_and_are_asked_for_smaller(self, db):
        aldi = CompanyFactory(name='Aldi')
        product = ProductFactory(
            aldi_image_url='https://cdn.aldi.example/scaleWidth/500/img.jpg'
        )
        PriceFactory(product=product, company=aldi, price=Decimal('2.00'))

        url = ProductSerializer(product).data['prices'][0]['image_url']

        assert url == 'https://cdn.aldi.example/scaleWidth/280/img.jpg'

    def test_coles_images_are_built_from_the_sku(self, db):
        coles = CompanyFactory(name='Coles')
        product = ProductFactory()
        SKU.objects.create(company=coles, product=product, sku='456789')
        PriceFactory(product=product, company=coles, price=Decimal('2.00'))

        url = ProductSerializer(product).data['prices'][0]['image_url']

        assert url == (
            'https://productimages.coles.com.au/productimages/4/456789.jpg'
        )

    def test_woolworths_images_are_asked_for_the_medium_size(self, db):
        woolworths = CompanyFactory(
            name='Woolworths',
            image_url_template='https://cdn.woolworths.example/large/{sku}.jpg',
        )
        product = ProductFactory()
        SKU.objects.create(company=woolworths, product=product, sku='123')
        PriceFactory(product=product, company=woolworths, price=Decimal('2.00'))

        url = ProductSerializer(product).data['prices'][0]['image_url']

        assert url == 'https://cdn.woolworths.example/medium/123.jpg'

    def test_any_other_company_uses_its_template_as_written(self, db):
        other = CompanyFactory(
            name='Other Grocer',
            image_url_template='https://cdn.other.example/{sku}.png',
        )
        product = ProductFactory()
        SKU.objects.create(company=other, product=product, sku='777')
        PriceFactory(product=product, company=other, price=Decimal('2.00'))

        url = ProductSerializer(product).data['prices'][0]['image_url']

        assert url == 'https://cdn.other.example/777.png'

    def test_a_product_with_no_sku_at_that_company_has_no_image(self, db):
        company = CompanyFactory(
            name='Other Grocer',
            image_url_template='https://cdn.other.example/{sku}.png',
        )
        product = ProductFactory()
        PriceFactory(product=product, company=company, price=Decimal('2.00'))

        assert ProductSerializer(product).data['prices'][0]['image_url'] is None

    def test_the_tile_image_is_the_first_one_that_resolves(self, db):
        """`image_url` is the single picture the product tile shows. A company
        with no SKU must not leave the tile blank when another has one."""
        no_sku = CompanyFactory(name='No Images', image_url_template='')
        with_sku = CompanyFactory(
            name='Other Grocer',
            image_url_template='https://cdn.other.example/{sku}.png',
        )
        product = ProductFactory()
        SKU.objects.create(company=with_sku, product=product, sku='777')
        PriceFactory(product=product, company=no_sku, price=Decimal('1.00'))
        PriceFactory(product=product, company=with_sku, price=Decimal('2.00'))

        assert ProductSerializer(product).data['image_url'] == (
            'https://cdn.other.example/777.png'
        )

    def test_a_product_nobody_has_a_picture_of_reports_none(self, db):
        product = ProductFactory()
        PriceFactory(
            product=product,
            company=CompanyFactory(name='No Images', image_url_template=''),
            price=Decimal('2.00'),
        )

        assert ProductSerializer(product).data['image_url'] is None


@pytest.mark.django_db
class TestBargainBadge:
    def test_without_a_bargain_map_there_is_no_badge(self, db):
        """The map is built by the view. Every other caller -- the cart, the
        product page -- gets no badge rather than a wrong one."""
        assert ProductSerializer(ProductFactory()).data['bargain_info'] is None

    def test_a_product_absent_from_the_map_gets_no_badge(self, db):
        product = ProductFactory()

        data = ProductSerializer(
            product, context={'bargain_info_map': {product.id + 1: {'discount': 20}}}
        ).data

        assert data['bargain_info'] is None

    def test_the_badge_states_the_discount_and_the_supermarket(self, db):
        product = ProductFactory()
        context = {
            'bargain_info_map': {
                product.id: {'discount': 25, 'cheaper_company_name': 'Coles'}
            }
        }

        badge = ProductSerializer(product, context=context).data['bargain_info']

        assert badge == {
            'discount_percentage': 25,
            'cheapest_company_name': 'Coles',
            'message': '-25% at Coles',
        }

    def test_woolworths_is_shortened_in_the_badge_only(self, db):
        """The badge is a narrow strip on a tile; the full name does not fit.
        The machine-readable field keeps the real name."""
        product = ProductFactory()
        context = {
            'bargain_info_map': {
                product.id: {'discount': 10, 'cheaper_company_name': 'Woolworths'}
            }
        }

        badge = ProductSerializer(product, context=context).data['bargain_info']

        assert badge['message'] == '-10% at Woolies'
        assert badge['cheapest_company_name'] == 'Woolworths'

    def test_the_tile_image_prefers_the_supermarket_with_the_bargain(self, db):
        """Badge and picture have to agree, or the tile advertises a discount on
        a product photographed somewhere else."""
        cheap = CompanyFactory(
            name='Cheap Grocer',
            image_url_template='https://cdn.cheap.example/{sku}.png',
        )
        other = CompanyFactory(
            name='Other Grocer',
            image_url_template='https://cdn.other.example/{sku}.png',
        )
        product = ProductFactory()
        SKU.objects.create(company=cheap, product=product, sku='111')
        SKU.objects.create(company=other, product=product, sku='222')
        PriceFactory(product=product, company=other, price=Decimal('5.00'))
        PriceFactory(product=product, company=cheap, price=Decimal('2.00'))
        context = {
            'bargain_info_map': {
                product.id: {'discount': 60, 'cheaper_company_name': 'Cheap Grocer'}
            }
        }

        data = ProductSerializer(product, context=context).data

        assert data['image_url'] == 'https://cdn.cheap.example/111.png'
