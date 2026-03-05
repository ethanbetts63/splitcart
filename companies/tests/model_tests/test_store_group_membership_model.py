import pytest
from django.db import IntegrityError
from companies.models import StoreGroup, StoreGroupMembership
from companies.tests.factories import CompanyFactory, StoreFactory


@pytest.mark.django_db
class TestStoreGroupMembershipModel:
    def test_str_contains_store_name_and_group(self):
        company = CompanyFactory()
        store = StoreFactory(store_name='My Store', company=company)
        group = StoreGroup.objects.create(company=company)
        membership = StoreGroupMembership.objects.create(store=store, group=group)
        assert 'My Store' in str(membership)

    def test_store_can_only_belong_to_one_group(self):
        company = CompanyFactory()
        store = StoreFactory(company=company)
        group_a = StoreGroup.objects.create(company=company)
        group_b = StoreGroup.objects.create(company=company)
        StoreGroupMembership.objects.create(store=store, group=group_a)
        with pytest.raises(IntegrityError):
            StoreGroupMembership.objects.create(store=store, group=group_b)

    def test_group_can_have_multiple_stores(self):
        company = CompanyFactory()
        store_a = StoreFactory(company=company)
        store_b = StoreFactory(company=company)
        group = StoreGroup.objects.create(company=company)
        StoreGroupMembership.objects.create(store=store_a, group=group)
        StoreGroupMembership.objects.create(store=store_b, group=group)
        assert group.memberships.count() == 2
