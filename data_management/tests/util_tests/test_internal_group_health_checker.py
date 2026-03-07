import datetime
import pytest
from decimal import Decimal
from django.utils import timezone
from companies.models import StoreGroup, StoreGroupMembership
from companies.tests.factories import CompanyFactory, StoreFactory
from products.models import Price
from products.tests.factories import PriceFactory, ProductFactory
from data_management.database_updating_classes.product_updating.group_maintanance.internal_group_health_checker import InternalGroupHealthChecker


def _make_group(company, anchor, members=None):
    """Creates a StoreGroup with an anchor and optional additional members."""
    group = StoreGroup.objects.create(company=company, anchor=anchor)
    StoreGroupMembership.objects.create(store=anchor, group=group)
    for member in (members or []):
        StoreGroupMembership.objects.create(store=member, group=group)
    return group


class TestStoreHasCurrentPricing:
    """Tests for the pure helper method — no DB needed."""

    def test_returns_true_when_store_has_prices(self, mock_command):
        checker = InternalGroupHealthChecker(mock_command)
        cache = {1: {101: Decimal('2.00')}}
        assert checker._store_has_current_pricing(1, cache) is True

    def test_returns_false_when_store_not_in_cache(self, mock_command):
        checker = InternalGroupHealthChecker(mock_command)
        assert checker._store_has_current_pricing(99, {}) is False

    def test_returns_false_when_store_has_empty_price_dict(self, mock_command):
        checker = InternalGroupHealthChecker(mock_command)
        cache = {1: {}}
        assert checker._store_has_current_pricing(1, cache) is False


@pytest.mark.django_db
class TestEjectMember:
    def test_removes_membership_from_original_group(self, mock_command):
        company = CompanyFactory()
        anchor = StoreFactory(company=company)
        member = StoreFactory(company=company)
        group = _make_group(company, anchor, [member])

        checker = InternalGroupHealthChecker(mock_command)
        checker._eject_member(member, group)

        assert not StoreGroupMembership.objects.filter(store=member, group=group).exists()

    def test_creates_new_solo_group_for_ejected_member(self, mock_command):
        company = CompanyFactory()
        anchor = StoreFactory(company=company)
        member = StoreFactory(company=company)
        group = _make_group(company, anchor, [member])

        checker = InternalGroupHealthChecker(mock_command)
        checker._eject_member(member, group)

        new_group = StoreGroup.objects.filter(anchor=member).exclude(pk=group.pk).first()
        assert new_group is not None
        assert StoreGroupMembership.objects.filter(store=member, group=new_group).exists()

    def test_new_group_has_correct_company(self, mock_command):
        company = CompanyFactory()
        anchor = StoreFactory(company=company)
        member = StoreFactory(company=company)
        group = _make_group(company, anchor, [member])

        checker = InternalGroupHealthChecker(mock_command)
        checker._eject_member(member, group)

        new_group = StoreGroup.objects.filter(anchor=member).exclude(pk=group.pk).first()
        assert new_group.company == company


@pytest.mark.django_db
class TestInternalGroupHealthCheckerRun:
    def test_skips_group_with_no_anchor(self, mock_command):
        company = CompanyFactory()
        anchor = StoreFactory(company=company)
        member = StoreFactory(company=company)
        group = _make_group(company, anchor, [member])
        group.anchor = None
        group.save()

        # Should not raise
        checker = InternalGroupHealthChecker(mock_command)
        checker.run()

    def test_flags_stale_anchor_for_rescraping(self, mock_command):
        company = CompanyFactory()
        anchor = StoreFactory(company=company)
        member = StoreFactory(company=company)
        group = _make_group(company, anchor, [member])
        # No prices added → anchor is stale

        checker = InternalGroupHealthChecker(mock_command)
        checker.run()

        anchor.refresh_from_db()
        assert anchor.needs_rescraping is True

    def test_ejcts_member_with_mismatched_prices(self, mock_command):
        company = CompanyFactory()
        anchor = StoreFactory(company=company)
        member = StoreFactory(company=company)
        group = _make_group(company, anchor, [member])

        product = ProductFactory()
        today = datetime.date.today()
        # Anchor and member have different prices for same product
        PriceFactory(product=product, store=anchor, price=Decimal('5.00'), scraped_date=today)
        PriceFactory(product=product, store=member, price=Decimal('9.00'), scraped_date=today)

        checker = InternalGroupHealthChecker(mock_command)
        checker.run()

        # Member should have been ejected into its own group
        assert not StoreGroupMembership.objects.filter(store=member, group=group).exists()
        new_group = StoreGroup.objects.filter(anchor=member).exclude(pk=group.pk).first()
        assert new_group is not None

    def test_keeps_matching_member_in_group(self, mock_command):
        company = CompanyFactory()
        anchor = StoreFactory(company=company)
        member = StoreFactory(company=company)
        group = _make_group(company, anchor, [member])

        product = ProductFactory()
        today = datetime.date.today()
        # Both have identical prices
        PriceFactory(product=product, store=anchor, price=Decimal('5.00'), scraped_date=today)
        PriceFactory(product=product, store=member, price=Decimal('5.00'), scraped_date=today)

        checker = InternalGroupHealthChecker(mock_command)
        checker.run()

        # Member remains in the original group
        assert StoreGroupMembership.objects.filter(store=member, group=group).exists()

    def test_deletes_prices_for_healthy_member(self, mock_command):
        company = CompanyFactory()
        anchor = StoreFactory(company=company)
        member = StoreFactory(company=company)
        group = _make_group(company, anchor, [member])

        product = ProductFactory()
        today = datetime.date.today()
        PriceFactory(product=product, store=anchor, price=Decimal('5.00'), scraped_date=today)
        member_price = PriceFactory(product=product, store=member, price=Decimal('5.00'), scraped_date=today)

        checker = InternalGroupHealthChecker(mock_command)
        checker.run()

        # Member's prices are purged after being confirmed healthy
        assert not Price.objects.filter(pk=member_price.pk).exists()

    def test_solo_groups_are_not_checked(self, mock_command):
        """Groups with only one member (anchor only) are skipped entirely."""
        company = CompanyFactory()
        anchor = StoreFactory(company=company, needs_rescraping=False)
        _make_group(company, anchor)  # No members other than anchor

        checker = InternalGroupHealthChecker(mock_command)
        checker.run()

        anchor.refresh_from_db()
        assert anchor.needs_rescraping is False
