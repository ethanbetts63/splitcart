"""`run_cart_optimization` -- turning a saved cart into a shopping plan.

The solver itself is proven in `pipeline/tests/util_tests/`. This is the layer
between it and the database: which products go into a slot, whose prices are
allowed, what a caller is told when there is nothing to optimise. It is the
money-adjacent half, and until now the untested one.
"""

from decimal import Decimal

import pytest

from companies.tests.factories import CompanyFactory
from pipeline.models import SystemSetting
from products.tests.factories import PriceFactory, ProductFactory
from products.utils.default_companies import CACHE_KEY
from users.tests.factories import CartFactory, CartItemFactory, CartSubstitutionFactory
from users.utils.cart_optimization import run_cart_optimization


@pytest.fixture
def companies(db):
    """Two supermarkets, configured as the ones the optimiser may price against."""
    alpha = CompanyFactory(name='Alpha Grocer')
    beta = CompanyFactory(name='Beta Grocer')
    SystemSetting.objects.create(key=CACHE_KEY, value=[alpha.id, beta.id])
    return alpha, beta


def _priced(companies, **prices):
    """A product with a price at each named company."""
    alpha, beta = companies
    product = ProductFactory()
    for company, amount in ((alpha, prices.get('alpha')), (beta, prices.get('beta'))):
        if amount is not None:
            PriceFactory(product=product, company=company, price=Decimal(amount))
    return product


def _plan_product_names(result):
    return {
        item['product_name']
        for plan in result['best_single_company']['shopping_plan'].values()
        for item in plan['items']
    }


@pytest.mark.django_db
class TestNothingToOptimize:
    def test_no_configured_companies_is_a_bad_request(self, user):
        """`SystemSetting` drives which supermarkets are priced. With none set
        there is no question to answer, and answering 200 with an empty plan
        would read to the client as "your cart is free"."""
        cart = CartFactory(user=user)
        CartItemFactory(cart=cart)

        response = run_cart_optimization(cart, [2])

        assert response.status_code == 400
        assert response.data['error'] == 'No pricing companies configured.'

    def test_an_empty_cart_is_not_found(self, user, companies):
        cart = CartFactory(user=user)

        response = run_cart_optimization(cart, [2])

        assert response.status_code == 404
        assert 'Could not find prices' in response.data['error']

    def test_a_cart_of_unpriced_products_is_not_found(self, user, companies):
        cart = CartFactory(user=user)
        CartItemFactory(cart=cart, product=ProductFactory())

        response = run_cart_optimization(cart, [2])

        assert response.status_code == 404

    def test_prices_from_a_company_outside_the_configured_set_are_ignored(
        self, user, companies
    ):
        outsider = CompanyFactory(name='Gamma Grocer')
        product = ProductFactory()
        PriceFactory(product=product, company=outsider, price=Decimal('1.00'))
        cart = CartFactory(user=user)
        CartItemFactory(cart=cart, product=product)

        response = run_cart_optimization(cart, [2])

        assert response.status_code == 404


@pytest.mark.django_db
class TestBaselineCost:
    def test_the_baseline_is_the_average_of_the_available_prices(
        self, user, companies
    ):
        product = _priced(companies, alpha='4.00', beta='6.00')
        cart = CartFactory(user=user)
        CartItemFactory(cart=cart, product=product, quantity=1)

        response = run_cart_optimization(cart, [1])

        assert response.status_code == 200
        assert response.data['baseline_cost'] == pytest.approx(5.00)

    def test_the_quantity_on_the_line_multiplies_it(self, user, companies):
        product = _priced(companies, alpha='4.00', beta='6.00')
        cart = CartFactory(user=user)
        CartItemFactory(cart=cart, product=product, quantity=3)

        response = run_cart_optimization(cart, [1])

        assert response.data['baseline_cost'] == pytest.approx(15.00)

    def test_every_line_in_the_cart_counts(self, user, companies):
        cart = CartFactory(user=user)
        CartItemFactory(
            cart=cart, product=_priced(companies, alpha='4.00', beta='6.00'), quantity=1
        )
        CartItemFactory(
            cart=cart, product=_priced(companies, alpha='1.00', beta='3.00'), quantity=1
        )

        response = run_cart_optimization(cart, [1])

        assert response.data['baseline_cost'] == pytest.approx(7.00)


@pytest.mark.django_db
class TestTheShoppingPlan:
    def test_the_cheapest_single_supermarket_is_named(self, user, companies):
        """Two items, both cheaper at Alpha, so one trip to Alpha wins."""
        cart = CartFactory(user=user)
        CartItemFactory(
            cart=cart, product=_priced(companies, alpha='2.00', beta='9.00')
        )
        CartItemFactory(
            cart=cart, product=_priced(companies, alpha='3.00', beta='8.00')
        )

        response = run_cart_optimization(cart, [1])

        best = response.data['best_single_company']
        assert set(best['shopping_plan']) == {'Alpha Grocer'}
        assert best['optimized_cost'] == pytest.approx(5.00)

    def test_splitting_the_cart_beats_one_supermarket(self, user, companies):
        """One item is cheap at each, which is the whole premise of the product."""
        cart = CartFactory(user=user)
        CartItemFactory(
            cart=cart, product=_priced(companies, alpha='1.00', beta='9.00')
        )
        CartItemFactory(
            cart=cart, product=_priced(companies, alpha='9.00', beta='2.00')
        )

        response = run_cart_optimization(cart, [2])

        (split,) = response.data['optimization_results']
        assert split['max_companies'] == 2
        assert split['optimized_cost'] == pytest.approx(3.00)
        assert set(split['shopping_plan']) == {'Alpha Grocer', 'Beta Grocer'}

    def test_savings_are_measured_against_the_baseline(self, user, companies):
        cart = CartFactory(user=user)
        CartItemFactory(
            cart=cart, product=_priced(companies, alpha='1.00', beta='9.00')
        )
        CartItemFactory(
            cart=cart, product=_priced(companies, alpha='9.00', beta='2.00')
        )

        response = run_cart_optimization(cart, [2])

        (split,) = response.data['optimization_results']
        assert split['savings'] == pytest.approx(
            response.data['baseline_cost'] - split['optimized_cost']
        )

    def test_an_option_needing_more_shops_than_it_uses_is_dropped(
        self, user, companies
    ):
        """Asking for a two-shop split of a one-item cart has no honest answer:
        the solve succeeds using one shop, which is not the option that was
        asked for, so it is left out rather than mislabelled."""
        cart = CartFactory(user=user)
        CartItemFactory(
            cart=cart, product=_priced(companies, alpha='2.00', beta='3.00')
        )

        response = run_cart_optimization(cart, [2])

        assert response.data['optimization_results'] == []
        assert response.data['best_single_company'] is not None

    def test_each_requested_option_is_answered_in_turn(self, user, companies):
        cart = CartFactory(user=user)
        CartItemFactory(
            cart=cart, product=_priced(companies, alpha='1.00', beta='9.00')
        )
        CartItemFactory(
            cart=cart, product=_priced(companies, alpha='9.00', beta='2.00')
        )

        response = run_cart_optimization(cart, [1, 2])

        assert [r['max_companies'] for r in response.data['optimization_results']] == [
            1,
            2,
        ]


@pytest.mark.django_db
class TestSubstitutes:
    def test_an_approved_substitute_replaces_the_original(self, user, companies):
        """This is what the `no_subs_results` block exists to contrast with: the
        headline plan is allowed to buy the substitute the shopper ticked."""
        original = _priced(companies, alpha='10.00', beta='10.00')
        cheaper = _priced(companies, alpha='1.00', beta='1.00')
        cart = CartFactory(user=user)
        item = CartItemFactory(cart=cart, product=original, quantity=1)
        CartSubstitutionFactory(
            original_cart_item=item,
            substituted_product=cheaper,
            quantity=1,
            is_approved=True,
        )

        response = run_cart_optimization(cart, [1])

        assert _plan_product_names(response.data) == {cheaper.name}
        assert response.data['best_single_company']['optimized_cost'] == pytest.approx(
            1.00
        )

    def test_a_substitute_the_shopper_has_not_approved_is_not_bought(
        self, user, companies
    ):
        original = _priced(companies, alpha='10.00', beta='10.00')
        cheaper = _priced(companies, alpha='1.00', beta='1.00')
        cart = CartFactory(user=user)
        item = CartItemFactory(cart=cart, product=original, quantity=1)
        CartSubstitutionFactory(
            original_cart_item=item,
            substituted_product=cheaper,
            quantity=1,
            is_approved=False,
        )

        response = run_cart_optimization(cart, [1])

        assert _plan_product_names(response.data) == {original.name}

    def test_the_no_subs_block_always_prices_the_original(self, user, companies):
        """The frontend shows both so the shopper can see what the swap bought
        them. The comparison is meaningless if substitutes leak into it."""
        original = _priced(companies, alpha='10.00', beta='10.00')
        cheaper = _priced(companies, alpha='1.00', beta='1.00')
        cart = CartFactory(user=user)
        item = CartItemFactory(cart=cart, product=original, quantity=1)
        CartSubstitutionFactory(
            original_cart_item=item,
            substituted_product=cheaper,
            quantity=1,
            is_approved=True,
        )

        response = run_cart_optimization(cart, [1])

        no_subs = response.data['no_subs_results']['best_single_company']
        names = {
            item['product_name']
            for plan in no_subs['shopping_plan'].values()
            for item in plan['items']
        }
        assert names == {original.name}
        assert no_subs['optimized_cost'] == pytest.approx(10.00)

    def test_the_baseline_ignores_substitutes(self, user, companies):
        """Savings are quoted against what the shopper actually asked for."""
        original = _priced(companies, alpha='10.00', beta='10.00')
        cheaper = _priced(companies, alpha='1.00', beta='1.00')
        cart = CartFactory(user=user)
        item = CartItemFactory(cart=cart, product=original, quantity=1)
        CartSubstitutionFactory(
            original_cart_item=item,
            substituted_product=cheaper,
            quantity=1,
            is_approved=True,
        )

        response = run_cart_optimization(cart, [1])

        assert response.data['baseline_cost'] == pytest.approx(10.00)

    def test_an_approved_substitute_may_have_its_own_quantity(self, user, companies):
        """Two of the smaller pack stands in for one of the larger."""
        original = _priced(companies, alpha='10.00', beta='10.00')
        smaller = _priced(companies, alpha='3.00', beta='3.00')
        cart = CartFactory(user=user)
        item = CartItemFactory(cart=cart, product=original, quantity=1)
        CartSubstitutionFactory(
            original_cart_item=item,
            substituted_product=smaller,
            quantity=2,
            is_approved=True,
        )

        response = run_cart_optimization(cart, [1])

        assert response.data['best_single_company']['optimized_cost'] == pytest.approx(
            6.00
        )
