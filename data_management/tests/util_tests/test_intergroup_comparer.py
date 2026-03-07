import datetime
import pytest
from decimal import Decimal
from companies.models import StoreGroup, StoreGroupMembership
from companies.tests.factories import CompanyFactory, StoreFactory
from products.models import Price
from products.tests.factories import PriceFactory, ProductFactory
from data_management.database_updating_classes.product_updating.group_maintanance.intergroup_comparer import IntergroupComparer


def _make_group(company, anchor, members=None):
    group = StoreGroup.objects.create(company=company, anchor=anchor)
    StoreGroupMembership.objects.create(store=anchor, group=group)
    for member in (members or []):
        StoreGroupMembership.objects.create(store=member, group=group)
    return group


@pytest.mark.django_db
class TestMergeGroups:
    def test_smaller_group_is_deleted(self, mock_command):
        company = CompanyFactory()
        anchor_a = StoreFactory(company=company)
        anchor_b = StoreFactory(company=company)
        group_a = _make_group(company, anchor_a)
        group_b = _make_group(company, anchor_b)

        comparer = IntergroupComparer(mock_command)
        comparer._merge_groups(group_a, group_b)

        # One group must now be deleted
        surviving_ids = set(StoreGroup.objects.values_list('id', flat=True))
        assert group_a.id in surviving_ids or group_b.id in surviving_ids
        assert not (group_a.id in surviving_ids and group_b.id in surviving_ids)

    def test_memberships_moved_to_larger_group(self, mock_command):
        company = CompanyFactory()
        anchor_a = StoreFactory(company=company)
        extra_member = StoreFactory(company=company)
        anchor_b = StoreFactory(company=company)

        # group_a has 2 members (larger), group_b has 1
        group_a = _make_group(company, anchor_a, [extra_member])
        group_b = _make_group(company, anchor_b)

        comparer = IntergroupComparer(mock_command)
        comparer._merge_groups(group_a, group_b)

        # group_a is the larger group and should survive
        assert StoreGroup.objects.filter(pk=group_a.pk).exists()
        # anchor_b's membership should now be in group_a
        assert StoreGroupMembership.objects.filter(store=anchor_b, group=group_a).exists()

    def test_prices_deleted_for_stores_in_smaller_group(self, mock_command):
        company = CompanyFactory()
        anchor_a = StoreFactory(company=company)
        anchor_b = StoreFactory(company=company)
        group_a = _make_group(company, anchor_a)
        group_b = _make_group(company, anchor_b)

        product = ProductFactory()
        price_b = PriceFactory(product=product, store=anchor_b)

        comparer = IntergroupComparer(mock_command)
        # Force group_b to be the smaller group by merging a into b with a being larger
        # group_a has 1 member, group_b has 1 member → group_a (>=) is larger
        comparer._merge_groups(group_a, group_b)

        # group_b is smaller, its prices should be deleted
        assert not Price.objects.filter(pk=price_b.pk).exists()


@pytest.mark.django_db
class TestIntergroupComparerRun:
    def test_merges_groups_with_identical_prices(self, mock_command):
        company = CompanyFactory()
        anchor_a = StoreFactory(company=company)
        anchor_b = StoreFactory(company=company)
        group_a = _make_group(company, anchor_a)
        group_b = _make_group(company, anchor_b)

        product = ProductFactory()
        today = datetime.date.today()
        PriceFactory(product=product, store=anchor_a, price=Decimal('5.00'), scraped_date=today)
        PriceFactory(product=product, store=anchor_b, price=Decimal('5.00'), scraped_date=today)

        comparer = IntergroupComparer(mock_command)
        comparer.run()

        # One of the two groups should have been deleted
        remaining_groups = StoreGroup.objects.filter(pk__in=[group_a.pk, group_b.pk]).count()
        assert remaining_groups == 1

    def test_does_not_merge_groups_with_different_prices(self, mock_command):
        company = CompanyFactory()
        anchor_a = StoreFactory(company=company)
        anchor_b = StoreFactory(company=company)
        group_a = _make_group(company, anchor_a)
        group_b = _make_group(company, anchor_b)

        product = ProductFactory()
        today = datetime.date.today()
        PriceFactory(product=product, store=anchor_a, price=Decimal('5.00'), scraped_date=today)
        PriceFactory(product=product, store=anchor_b, price=Decimal('9.00'), scraped_date=today)

        comparer = IntergroupComparer(mock_command)
        comparer.run()

        assert StoreGroup.objects.filter(pk=group_a.pk).exists()
        assert StoreGroup.objects.filter(pk=group_b.pk).exists()

    def test_does_nothing_when_fewer_than_two_groups_have_pricing(self, mock_command):
        company = CompanyFactory()
        anchor_a = StoreFactory(company=company)
        group_a = _make_group(company, anchor_a)
        # Only one group has prices — nothing to compare

        product = ProductFactory()
        PriceFactory(product=product, store=anchor_a)

        comparer = IntergroupComparer(mock_command)
        comparer.run()  # Should not raise

        assert StoreGroup.objects.filter(pk=group_a.pk).exists()

    def test_does_not_merge_groups_from_different_companies(self, mock_command):
        company_a = CompanyFactory()
        company_b = CompanyFactory()
        anchor_a = StoreFactory(company=company_a)
        anchor_b = StoreFactory(company=company_b)
        group_a = _make_group(company_a, anchor_a)
        group_b = _make_group(company_b, anchor_b)

        product = ProductFactory()
        today = datetime.date.today()
        # Identical prices, but different companies
        PriceFactory(product=product, store=anchor_a, price=Decimal('5.00'), scraped_date=today)
        PriceFactory(product=product, store=anchor_b, price=Decimal('5.00'), scraped_date=today)

        comparer = IntergroupComparer(mock_command)
        comparer.run()

        # Both groups should survive — different companies are compared separately
        assert StoreGroup.objects.filter(pk=group_a.pk).exists()
        assert StoreGroup.objects.filter(pk=group_b.pk).exists()
