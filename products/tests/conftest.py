import pytest
from companies.models import StoreGroup, StoreGroupMembership
from companies.tests.factories import CompanyFactory, StoreFactory


@pytest.fixture
def make_anchored_store():
    """
    Returns a factory function that creates a store which is the anchor of its
    own single-store group. This matches the production assumption that every
    store has a StoreGroupMembership.
    """
    def _make(company=None, **store_kwargs):
        if company is None:
            company = CompanyFactory()
        store = StoreFactory(company=company, **store_kwargs)
        group = StoreGroup.objects.create(company=company, anchor=store)
        StoreGroupMembership.objects.create(store=store, group=group)
        return store
    return _make
