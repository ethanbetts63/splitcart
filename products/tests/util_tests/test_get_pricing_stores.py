import pytest
from django.core.cache import cache
from companies.models import StoreGroup, StoreGroupMembership
from companies.tests.factories import CompanyFactory, StoreFactory
from products.tests.factories import ProductFactory, PriceFactory
from products.utils.get_pricing_stores import get_pricing_stores_map


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestGetPricingStoresMap:
    def test_empty_input_returns_empty_dict(self):
        result = get_pricing_stores_map([])
        assert result == {}

    def test_self_anchored_store_maps_to_itself(self, make_anchored_store):
        store = make_anchored_store()

        result = get_pricing_stores_map([store.id])

        assert result == {store.id: store.id}

    def test_member_store_maps_to_group_anchor(self):
        company = CompanyFactory()
        anchor = StoreFactory(company=company)
        member = StoreFactory(company=company)
        group = StoreGroup.objects.create(company=company, anchor=anchor)
        StoreGroupMembership.objects.create(store=anchor, group=group)
        StoreGroupMembership.objects.create(store=member, group=group)

        result = get_pricing_stores_map([member.id])

        assert result == {member.id: anchor.id}

    def test_anchor_store_with_prices_maps_to_itself(self, make_anchored_store):
        anchor = make_anchored_store()
        product = ProductFactory()
        PriceFactory(product=product, store=anchor)

        result = get_pricing_stores_map([anchor.id])

        assert result == {anchor.id: anchor.id}

    def test_unpriced_non_iga_store_falls_back_to_company_default_anchor(self, make_anchored_store):
        # Use a unique name to avoid cross-test company cache collisions
        company = CompanyFactory(name='Woolworths-fallback-test')

        # This store has no prices — it is self-anchored but unpriced
        unpriced_store = make_anchored_store(company=company)

        # This store is the anchor of a bigger group (2 members) — becomes the default anchor
        bigger_anchor = StoreFactory(company=company)
        extra_member = StoreFactory(company=company)
        big_group = StoreGroup.objects.create(company=company, anchor=bigger_anchor)
        StoreGroupMembership.objects.create(store=bigger_anchor, group=big_group)
        StoreGroupMembership.objects.create(store=extra_member, group=big_group)

        result = get_pricing_stores_map([unpriced_store.id])

        assert result[unpriced_store.id] == bigger_anchor.id

    def test_unpriced_iga_store_stays_as_itself(self, make_anchored_store):
        iga = CompanyFactory(name='IGA')
        unpriced_iga_store = make_anchored_store(company=iga)

        # Even with a default anchor available, IGA stores are exempt from fallback
        other_anchor = StoreFactory(company=iga)
        extra_member = StoreFactory(company=iga)
        group = StoreGroup.objects.create(company=iga, anchor=other_anchor)
        StoreGroupMembership.objects.create(store=other_anchor, group=group)
        StoreGroupMembership.objects.create(store=extra_member, group=group)

        result = get_pricing_stores_map([unpriced_iga_store.id])

        assert result[unpriced_iga_store.id] == unpriced_iga_store.id

    def test_multiple_stores_resolved_independently(self):
        company = CompanyFactory()
        anchor = StoreFactory(company=company)
        member = StoreFactory(company=company)
        self_anchored = StoreFactory(company=company)

        group = StoreGroup.objects.create(company=company, anchor=anchor)
        StoreGroupMembership.objects.create(store=anchor, group=group)
        StoreGroupMembership.objects.create(store=member, group=group)

        solo_group = StoreGroup.objects.create(company=company, anchor=self_anchored)
        StoreGroupMembership.objects.create(store=self_anchored, group=solo_group)

        result = get_pricing_stores_map([member.id, self_anchored.id])

        assert result[member.id] == anchor.id
        assert result[self_anchored.id] == self_anchored.id
