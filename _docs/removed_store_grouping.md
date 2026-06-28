# Removed: Store Grouping System

Removed because IGA (the only per-store pricer) was removed. Remaining companies
(Coles, Woolworths, Aldi) price nationally, so anchor deduplication provides no value.
The anchor resolution layer in views/utilities was also dead code once frontend
store selection was removed.

---

## companies/models/store_group.py
```python
from django.db import models

class StoreGroup(models.Model):
    """
    Represents a geographic or logical cluster of stores belonging to a single company.
    """

    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='store_groups')

    # The current source of truth for the group's pricing
    anchor = models.ForeignKey(
        'companies.Store',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='anchor_for_group'
    )

    def __str__(self):
        return f"{self.company.name} Group {self.id}"
```

---

## companies/models/store_group_membership.py
```python
from django.db import models

class StoreGroupMembership(models.Model):
    """
    A simple and pure linking table that connects a Store to a StoreGroup.
    Its existence signifies that a store is part of a group.
    """
    store = models.OneToOneField('companies.Store', on_delete=models.CASCADE, related_name='group_membership')
    group = models.ForeignKey('companies.StoreGroup', on_delete=models.CASCADE, related_name='memberships')

    class Meta:
        unique_together = ('store', 'group')

    def __str__(self):
        return f'{self.store.store_name} in {self.group}'
```

---

## products/utils/get_pricing_stores.py
```python
from django.core.cache import cache
from django.db.models import Count
from companies.models import Store, StoreGroup
from products.models import Price

def get_default_anchor_for_company(company_id):
    """
    Finds and caches the anchor of the largest store group for a given company.
    This is used as a fallback for nationally-priced companies.
    """
    cache_key = f'default_anchor_{company_id}'
    default_anchor_id = cache.get(cache_key)
    if default_anchor_id:
        return default_anchor_id

    biggest_group = StoreGroup.objects.filter(company_id=company_id) \
                                        .annotate(num_members=Count('memberships')) \
                                        .order_by('-num_members').first()
    if biggest_group and biggest_group.anchor:
        default_anchor_id = biggest_group.anchor.id
        cache.set(cache_key, default_anchor_id, timeout=3600)
        return default_anchor_id
    return None

def get_pricing_stores_map(requested_store_ids):
    """
    Determines the correct anchor store ID for each requested store ID based on
    business logic for price lookups.

    Returns a dictionary mapping {requested_store_id: final_anchor_id}.
    """
    if not requested_store_ids:
        return {}

    stores = Store.objects.filter(id__in=requested_store_ids).select_related(
        'company', 'group_membership__group__anchor'
    )
    store_map = {s.id: s for s in stores}

    translation_map = {}
    self_anchored_store_ids = set()
    for store in stores:
        if store.group_membership and store.group_membership.group and store.group_membership.group.anchor:
            anchor_id = store.group_membership.group.anchor.id
            translation_map[store.id] = anchor_id
            if store.id == anchor_id:
                self_anchored_store_ids.add(store.id)
        else:
            translation_map[store.id] = store.id
            self_anchored_store_ids.add(store.id)

    priced_self_anchored_ids = set(Price.objects.filter(store_id__in=self_anchored_store_ids).values_list('store_id', flat=True))
    unpriced_self_anchored_ids = self_anchored_store_ids - priced_self_anchored_ids

    for store_id in unpriced_self_anchored_ids:
        store = store_map.get(store_id)
        if not store:
            continue
        default_anchor_id = get_default_anchor_for_company(store.company.id)
        if default_anchor_id:
            translation_map[store.id] = default_anchor_id

    return translation_map
```

---

## data_management/database_updating_classes/product_updating/group_maintanance/group_maintenance_orchestrator.py
```python
from .internal_group_health_checker import InternalGroupHealthChecker
from .intergroup_comparer import IntergroupComparer

class GroupMaintenanceOrchestrator:
    def __init__(self, command, relaxed_staleness=False):
        self.command = command
        self.relaxed_staleness = relaxed_staleness

    def run(self):
        self.command.stdout.write(self.command.style.SQL_FIELD("--- Starting Group Maintenance Orchestration ---"))
        health_checker = InternalGroupHealthChecker(self.command, relaxed_staleness=self.relaxed_staleness)
        health_checker.run()
        merger = IntergroupComparer(self.command, relaxed_staleness=self.relaxed_staleness)
        merger.run()
        self.command.stdout.write(self.command.style.SUCCESS("--- Group Maintenance Orchestration Complete ---"))
```

---

## data_management/database_updating_classes/product_updating/group_maintanance/internal_group_health_checker.py
```python
from datetime import timedelta
from django.utils import timezone
from django.db import transaction, models
from companies.models import Store, StoreGroup, StoreGroupMembership
from products.models import Price
from data_management.utils.price_comparer import PriceComparer
from data_management.utils.health_check_cache_manager import HealthCheckCacheManager

class InternalGroupHealthChecker:
    def __init__(self, command, relaxed_staleness=False):
        self.command = command
        self.comparer = PriceComparer()
        self.relaxed_staleness = relaxed_staleness

        if self.relaxed_staleness:
            self.command.stdout.write(self.command.style.WARNING("Using relaxed staleness check for internal health checks."))
            try:
                latest_scrape_date = Price.objects.latest('scraped_date').scraped_date
                self.freshness_threshold = latest_scrape_date - timedelta(days=7)
            except Price.DoesNotExist:
                self.freshness_threshold = timezone.now() - timedelta(days=7)
        else:
            self.freshness_threshold = timezone.now() - timedelta(days=7)

        self.command.stdout.write(f"  - Using freshness threshold: {self.freshness_threshold}")

    def _store_has_current_pricing(self, store_id, all_prices_cache):
        return store_id in all_prices_cache and bool(all_prices_cache[store_id])

    def _eject_member(self, member_store, old_group):
        self.command.stdout.write(f"    - Ejecting member '{member_store.store_name}' from Group {old_group.id}.")
        StoreGroupMembership.objects.filter(store=member_store).delete()
        new_group = StoreGroup.objects.create(company=member_store.company, anchor=member_store)
        StoreGroupMembership.objects.create(store=member_store, group=new_group)
        self.command.stdout.write(f"    - Created new Group {new_group.id} for ejected member.")

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("--- Running Internal Group Health Checks ---"))
        cache_manager = HealthCheckCacheManager(self.command, cooldown_days=7)

        try:
            groups_to_check = StoreGroup.objects.annotate(num_members=models.Count('memberships')).filter(num_members__gt=1)
            self.command.stdout.write(f"  - Found {len(groups_to_check)} groups with more than one member to check.")

            for group in groups_to_check:
                anchor = group.anchor
                if not anchor:
                    self.command.stdout.write(self.command.style.WARNING(f"  - Skipping Group {group.id}: No anchor set."))
                    continue

                self.command.stdout.write(f"  - Checking Group {group.id} (Anchor: {anchor.store_name})...")

                all_store_ids_in_group = list(group.memberships.values_list('store_id', flat=True))

                price_queryset = Price.objects.filter(
                    store_id__in=all_store_ids_in_group,
                    scraped_date__gte=self.freshness_threshold
                ).values('store_id', 'product_id', 'price')

                group_prices_cache = {store_id: {} for store_id in all_store_ids_in_group}
                for price_data in price_queryset:
                    group_prices_cache[price_data['store_id']][price_data['product_id']] = price_data['price']

                anchor_is_current = self._store_has_current_pricing(anchor.id, group_prices_cache)

                if not anchor_is_current:
                    self.command.stdout.write(self.command.style.WARNING(f"    - Anchor data is stale. Flagging for re-scrape and skipping checks for this group."))
                    anchor.needs_rescraping = True
                    anchor.save(update_fields=['needs_rescraping'])
                    continue

                members_to_check = Store.objects.filter(group_membership__group=group).exclude(pk=anchor.pk)

                healthy_members_to_purge = []
                skipped_count = 0

                for member in members_to_check:
                    if cache_manager.should_skip(member.id):
                        skipped_count += 1
                        continue

                    if not self._store_has_current_pricing(member.id, group_prices_cache):
                        continue

                    self.command.stdout.write(f"    - Comparing member '{member.store_name}' against anchor...")

                    price_map_a = group_prices_cache.get(anchor.id, {})
                    price_map_b = group_prices_cache.get(member.id, {})
                    match = self.comparer.compare(price_map_a, price_map_b)

                    if not match:
                        self.command.stdout.write(self.command.style.ERROR(f"    - Mismatch confirmed. Ejecting member."))
                        with transaction.atomic():
                            self._eject_member(member, group)
                    else:
                        self.command.stdout.write(self.command.style.SUCCESS("    - Match confirmed. Member is healthy."))
                        healthy_members_to_purge.append(member)
                        cache_manager.record_healthy_member(member.id)

                if skipped_count > 0:
                    self.command.stdout.write(f"    - Skipped {skipped_count} members based on recent health check cache.")

                if healthy_members_to_purge:
                    store_ids_to_purge = [m.id for m in healthy_members_to_purge]
                    self.command.stdout.write(f"    - Deleting redundant prices for {len(healthy_members_to_purge)} healthy members in bulk.")
                    deleted_count, _ = Price.objects.filter(store_id__in=store_ids_to_purge).delete()
                    if deleted_count > 0:
                        self.command.stdout.write(f"    - Deleted {deleted_count:,} price objects.")
        finally:
            cache_manager.save()
```

---

## data_management/database_updating_classes/product_updating/group_maintanance/intergroup_comparer.py
```python
from django.db import transaction
from django.db.models import Count
from companies.models import Store, StoreGroup, StoreGroupMembership
from products.models import Price
from data_management.utils.price_comparer import PriceComparer
from data_management.utils.group_comparison_cache_manager import ComparisonCacheManager
import itertools
import random

class IntergroupComparer:
    def __init__(self, command, **kwargs):
        self.command = command
        self.comparer = PriceComparer()

    def _get_groups_with_any_pricing(self):
        return StoreGroup.objects.filter(
            anchor__prices__isnull=False
        ).distinct().prefetch_related('anchor', 'company')

    def _merge_groups(self, group_a, group_b):
        if group_a.memberships.count() >= group_b.memberships.count():
            larger_group, smaller_group = group_a, group_b
        else:
            larger_group, smaller_group = group_b, group_a

        self.command.stdout.write(f"    - Merging Group {smaller_group.id} into Group {larger_group.id}.")
        stores_to_purge = Store.objects.filter(group_membership__group=smaller_group)
        store_ids_to_purge = list(stores_to_purge.values_list('id', flat=True))
        StoreGroupMembership.objects.filter(group=smaller_group).update(group=larger_group)

        if store_ids_to_purge:
            self.command.stdout.write(f"    - Deleting redundant prices for {len(store_ids_to_purge)} stores from dissolved group.")
            deleted_count, _ = Price.objects.filter(store_id__in=store_ids_to_purge).delete()
            self.command.stdout.write(f"    - Deleted {deleted_count:,} price objects.")

        smaller_group.delete()

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("--- Running Inter-Group Merging ---"))
        cache_manager = ComparisonCacheManager(self.command)
        merges_occurred_in_total = 0
        pass_count = 0

        try:
            while True:
                pass_count += 1
                self.command.stdout.write(f"  --- Pass {pass_count}: Re-evaluating for merges ---")
                merges_occurred_in_pass = False
                all_groups = self._get_groups_with_any_pricing()
                self.command.stdout.write(f"  - Found {len(all_groups)} total groups with any pricing.")

                if len(all_groups) < 2:
                    self.command.stdout.write("  - Not enough active groups to compare. Halting.")
                    break

                groups_by_company = {}
                for group in all_groups:
                    if group.company_id not in groups_by_company:
                        groups_by_company[group.company_id] = []
                    groups_by_company[group.company_id].append(group)

                for company_id, company_groups in groups_by_company.items():
                    company_name = company_groups[0].company.name
                    self.command.stdout.write(f"\n  -- Processing company: {company_name} ({len(company_groups)} groups) --")

                    if len(company_groups) < 2:
                        self.command.stdout.write("     - Not enough groups for this company to compare. Skipping.")
                        continue

                    groups_to_process = company_groups
                    if len(company_groups) > 100:
                        self.command.stdout.write("     - More than 100 groups found. Sampling 50 to reduce load.")
                        groups_to_process = random.sample(company_groups, 50)

                    potential_pairs = list(itertools.combinations(groups_to_process, 2))
                    self.command.stdout.write(f"     - Generated {len(potential_pairs)} potential pairs for comparison.")

                    pairs_to_compare = []
                    for group_a, group_b in potential_pairs:
                        if not cache_manager.should_skip(group_a.id, group_b.id):
                            pairs_to_compare.append((group_a, group_b))

                    skipped_count = len(potential_pairs) - len(pairs_to_compare)
                    if skipped_count > 0:
                        self.command.stdout.write(f"     - Skipping {skipped_count} pairs based on recent comparison cache.")

                    necessary_anchor_ids = set()
                    for group_a, group_b in pairs_to_compare:
                        if group_a.anchor:
                            necessary_anchor_ids.add(group_a.anchor.id)
                        if group_b.anchor:
                            necessary_anchor_ids.add(group_b.anchor.id)

                    all_prices_cache = {}
                    if necessary_anchor_ids:
                        self.command.stdout.write(f"     - Pre-fetching prices for {len(necessary_anchor_ids)} required anchors...")
                        price_queryset = Price.objects.filter(
                            store_id__in=list(necessary_anchor_ids)
                        ).values('store_id', 'product_id', 'price')
                        all_prices_cache = {anchor_id: {} for anchor_id in necessary_anchor_ids}
                        for price_data in price_queryset:
                            all_prices_cache[price_data['store_id']][price_data['product_id']] = price_data['price']
                        self.command.stdout.write("     - Price cache built.")
                    else:
                        self.command.stdout.write("     - No new comparisons needed for this company in this pass.")

                    merged_group_ids_this_pass = set()

                    for group_a, group_b in pairs_to_compare:
                        if group_a.id in merged_group_ids_this_pass or group_b.id in merged_group_ids_this_pass:
                            continue

                        anchor_a = group_a.anchor
                        anchor_b = group_b.anchor

                        if not anchor_a or not anchor_b:
                            continue

                        price_map_a = all_prices_cache.get(anchor_a.id, {})
                        price_map_b = all_prices_cache.get(anchor_b.id, {})

                        if self.comparer.compare(price_map_a, price_map_b):
                            self.command.stdout.write(self.command.style.SUCCESS("       - Match found!"))
                            with transaction.atomic():
                                self._merge_groups(group_a, group_b)
                            merges_occurred_in_pass = True
                            merges_occurred_in_total += 1
                            merged_group_ids_this_pass.add(group_a.id)
                            merged_group_ids_this_pass.add(group_b.id)
                        else:
                            cache_manager.record_comparison(group_a.id, group_b.id)

                if not merges_occurred_in_pass:
                    self.command.stdout.write("\n  - No merges occurred in this pass across all companies. Merging complete.")
                    break
                else:
                    self.command.stdout.write(f"\n  - Merges occurred in this pass. Re-evaluating for more merges.")

        finally:
            cache_manager.save()

        self.command.stdout.write(self.command.style.SUCCESS(f"--- Inter-Group Merging Complete. Total merges: {merges_occurred_in_total} ---"))
```

---

## data_management/management/commands/inspect_store_groups.py
```python
from django.core.management.base import BaseCommand
from companies.models import Company

class Command(BaseCommand):
    help = 'Inspects the state of store groups by reporting store and store group counts for each company.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Store Group Inspection ---"))
        companies = Company.objects.all().prefetch_related('stores', 'store_groups')

        if not companies:
            self.stdout.write(self.style.WARNING("No companies found in the database."))
            return

        for company in companies:
            store_count = company.stores.count()
            stores_with_prices_count = company.stores.filter(prices__isnull=False).distinct().count()
            group_count = company.store_groups.count()
            groups_with_priced_anchor_count = company.store_groups.filter(anchor__prices__isnull=False).distinct().count()

            self.stdout.write(f"\nCompany: {company.name}")
            self.stdout.write(f"  - Total Stores: {store_count}")
            self.stdout.write(f"  - Stores with Prices: {stores_with_prices_count}")
            self.stdout.write(f"  - Total Store Groups: {group_count}")
            self.stdout.write(f"  - Groups with Priced Anchor: {groups_with_priced_anchor_count}")

            if store_count == group_count and store_count > 0:
                self.stdout.write(self.style.WARNING("  - Observation: The number of stores equals the number of groups. No grouping has occurred."))
            elif group_count > 0:
                self.stdout.write(self.style.SUCCESS(f"  - Observation: Grouping has occurred. {groups_with_priced_anchor_count} groups are usable for comparison."))
            else:
                self.stdout.write("  - Observation: No stores or groups to compare.")

        self.stdout.write(self.style.SUCCESS("\n--- Inspection Complete ---"))
```

---

## data_management/utils/generation_utils/store_groups_generator.py
```python
from django.db import transaction
from companies.models import Store, StoreGroup, StoreGroupMembership

class StoreGroupsGenerator:
    def __init__(self, command, dev=False):
        self.command = command

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("--- Generating Store Groups Directly in Database ---"))

        try:
            with transaction.atomic():
                self.command.stdout.write("  - Deleting all existing StoreGroup and StoreGroupMembership records...")
                StoreGroupMembership.objects.all().delete()
                StoreGroup.objects.all().delete()
                self.command.stdout.write("  - Existing records deleted.")

                all_stores = list(Store.objects.all())
                self.command.stdout.write(f"  - Found {len(all_stores)} stores to process.")

                for store in all_stores:
                    new_group = StoreGroup.objects.create(company=store.company, anchor=store)
                    StoreGroupMembership.objects.create(store=store, group=new_group)

                self.command.stdout.write(self.command.style.SUCCESS(f"  Successfully created {len(all_stores)} new store groups."))

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"An error occurred during store group generation: {e}"))
```

---

## data_management/analysers/store_grouping.py
```python
from data_management.utils.analysis_utils.store_grouping_utils.data_fetching import get_store_product_prices
from data_management.utils.analysis_utils.store_grouping_utils.graph_construction import build_correlation_graph
from data_management.utils.analysis_utils.store_grouping_utils.grouping import find_store_groups

def group_stores_by_price_correlation(company_name, threshold=99.5):
    store_map, store_price_data = get_store_product_prices(company_name)
    if not store_map or not store_price_data:
        return [], []
    graph = build_correlation_graph(store_map, store_price_data, threshold)
    final_groups, island_stores = find_store_groups(store_map, graph)
    return final_groups, island_stores
```

---

## data_management/utils/analysis_utils/store_grouping_utils/data_fetching.py
```python
from collections import defaultdict
from companies.models import Store, Company
from products.models import Price
from django.db.models import Count

def get_store_product_prices(company_name):
    try:
        company = Company.objects.get(name__iexact=company_name)
    except Company.DoesNotExist:
        print(f"Company '{company_name}' not found.")
        return None, None

    stores = Store.objects.filter(company=company).annotate(product_count=Count('prices')).filter(product_count__gt=100)
    store_count = stores.count()
    if store_count < 2:
        print("Need at least 2 stores to compare.")
        return None, None

    store_map = {store.id: store for store in stores}
    prices = Price.objects.filter(store__in=stores).values('store_id', 'product_id', 'price')

    store_price_data = defaultdict(dict)
    for price in prices:
        if price['price'] is not None:
            store_price_data[price['store_id']][price['product_id']] = price['price']

    return store_map, store_price_data
```

---

## data_management/utils/analysis_utils/store_grouping_utils/graph_construction.py
```python
from itertools import combinations

def build_correlation_graph(store_map, store_price_data, threshold):
    store_ids = list(store_map.keys())
    graph = {store_id: [] for store_id in store_ids}
    total_comparisons = len(store_ids) * (len(store_ids) - 1) // 2
    current_comparison = 0

    for store1_id, store2_id in combinations(store_ids, 2):
        current_comparison += 1
        print(f"Comparing stores ({current_comparison}/{total_comparisons}): {store_map[store1_id].store_name} and {store_map[store2_id].store_name}")

        products1 = store_price_data[store1_id]
        products2 = store_price_data[store2_id]
        common_product_ids = set(products1.keys()).intersection(set(products2.keys()))

        if not common_product_ids:
            correlation = 0.0
        else:
            identical_price_count = sum(1 for pid in common_product_ids if products1[pid] == products2[pid])
            correlation = (identical_price_count / len(common_product_ids)) * 100

        if correlation >= threshold:
            graph[store1_id].append(store2_id)
            graph[store2_id].append(store1_id)

    return graph
```

---

## data_management/utils/analysis_utils/store_grouping_utils/grouping.py
```python
def find_store_groups(store_map, graph):
    groups = []
    visited = set()
    store_ids = list(store_map.keys())

    for store_id in store_ids:
        if store_id not in visited:
            group = []
            stack = [store_id]
            visited.add(store_id)
            while stack:
                node = stack.pop()
                group.append(node)
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        stack.append(neighbor)
            if len(group) > 1:
                groups.append(group)

    grouped_store_ids = {store_id for group in groups for store_id in group}
    island_store_ids = set(store_ids) - grouped_store_ids

    final_groups = [[store_map[store_id] for store_id in group] for group in groups]
    island_stores = [store_map[store_id] for store_id in island_store_ids]

    return final_groups, island_stores
```

---

## companies/views/export_anchor_stores_view.py
```python
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from companies.models import StoreGroup
from splitcart.permissions import IsInternalAPIRequest

class ExportAnchorStoresView(ListAPIView):
    permission_classes = [IsInternalAPIRequest]

    def get(self, request, *args, **kwargs):
        anchor_ids = StoreGroup.objects.filter(anchor__isnull=False, anchor__prices__isnull=False).values_list('anchor_id', flat=True).distinct()
        return Response(list(anchor_ids))
```

---

## companies/tests/factories/store_group_factory.py
```python
import factory
from factory.django import DjangoModelFactory
from companies.models import StoreGroup
from .company_factory import CompanyFactory

class StoreGroupFactory(DjangoModelFactory):
    class Meta:
        model = StoreGroup

    company = factory.SubFactory(CompanyFactory)
    anchor = None
```

---

## companies/tests/factories/store_group_membership_factory.py
```python
import factory
from factory.django import DjangoModelFactory
from companies.models import StoreGroupMembership
from .store_factory import StoreFactory
from .store_group_factory import StoreGroupFactory

class StoreGroupMembershipFactory(DjangoModelFactory):
    class Meta:
        model = StoreGroupMembership

    store = factory.SubFactory(StoreFactory)
    group = factory.SubFactory(StoreGroupFactory, company=factory.SelfAttribute('..store.company'))
```

---

## products/tests/factories/store_group_factory.py
```python
import factory
from factory.django import DjangoModelFactory
from companies.models import StoreGroup, StoreGroupMembership
from companies.tests.factories import CompanyFactory, StoreFactory

class StoreGroupFactory(DjangoModelFactory):
    class Meta:
        model = StoreGroup

    company = factory.SubFactory(CompanyFactory)
    anchor = None

class StoreGroupMembershipFactory(DjangoModelFactory):
    class Meta:
        model = StoreGroupMembership

    store = factory.SubFactory(StoreFactory)
    group = factory.SubFactory(StoreGroupFactory)
```

---

## products/tests/conftest.py
```python
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
```

---

## companies/tests/model_tests/test_store_group_model.py
```python
import pytest
from companies.models import StoreGroup
from companies.tests.factories import CompanyFactory, StoreFactory

@pytest.mark.django_db
class TestStoreGroupModel:
    def test_str_includes_company_name_and_id(self):
        company = CompanyFactory(name='Coles')
        group = StoreGroup.objects.create(company=company)
        assert str(group) == f'Coles Group {group.id}'

    def test_anchor_defaults_to_none(self):
        company = CompanyFactory()
        group = StoreGroup.objects.create(company=company)
        assert group.anchor is None

    def test_anchor_can_be_assigned(self):
        company = CompanyFactory()
        store = StoreFactory(company=company)
        group = StoreGroup.objects.create(company=company, anchor=store)
        assert group.anchor == store

    def test_anchor_set_null_on_store_delete(self):
        company = CompanyFactory()
        store = StoreFactory(company=company)
        group = StoreGroup.objects.create(company=company, anchor=store)
        store.delete()
        group.refresh_from_db()
        assert group.anchor is None
```

---

## companies/tests/model_tests/test_store_group_membership_model.py
```python
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
```

---

## companies/tests/view_tests/test_export_anchor_stores_view.py
```python
import pytest
from django.urls import reverse
from companies.models import StoreGroup
from companies.tests.factories import CompanyFactory, StoreFactory

@pytest.mark.django_db
class TestExportAnchorStoresView:
    def test_returns_401_without_api_key(self, client):
        response = client.get(reverse('export-anchor-stores'))
        assert response.status_code == 401

    def test_returns_200_with_valid_api_key(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        response = client.get(reverse('export-anchor-stores'), HTTP_X_INTERNAL_API_KEY='test-key')
        assert response.status_code == 200

    def test_returns_empty_list_when_no_groups(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        response = client.get(reverse('export-anchor-stores'), HTTP_X_INTERNAL_API_KEY='test-key')
        assert response.json() == []

    def test_queryset_includes_anchor_stores_with_prices(self):
        from products.tests.factories import PriceFactory, ProductFactory
        company = CompanyFactory()
        anchor_store = StoreFactory(company=company)
        StoreGroup.objects.create(company=company, anchor=anchor_store)
        PriceFactory(store=anchor_store, product=ProductFactory())
        anchor_ids = list(
            StoreGroup.objects.filter(anchor__isnull=False, anchor__prices__isnull=False)
            .values_list('anchor_id', flat=True).distinct()
        )
        assert anchor_store.id in anchor_ids

    def test_queryset_excludes_anchor_stores_without_prices(self):
        company = CompanyFactory()
        anchor_store = StoreFactory(company=company)
        StoreGroup.objects.create(company=company, anchor=anchor_store)
        anchor_ids = list(
            StoreGroup.objects.filter(anchor__isnull=False, anchor__prices__isnull=False)
            .values_list('anchor_id', flat=True).distinct()
        )
        assert anchor_store.id not in anchor_ids

    def test_queryset_excludes_groups_with_no_anchor(self):
        company = CompanyFactory()
        StoreGroup.objects.create(company=company, anchor=None)
        anchor_ids = list(
            StoreGroup.objects.filter(anchor__isnull=False, anchor__prices__isnull=False)
            .values_list('anchor_id', flat=True).distinct()
        )
        assert anchor_ids == []
```

---

## data_management/tests/util_tests/test_intergroup_comparer.py
```python
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
        surviving_ids = set(StoreGroup.objects.values_list('id', flat=True))
        assert group_a.id in surviving_ids or group_b.id in surviving_ids
        assert not (group_a.id in surviving_ids and group_b.id in surviving_ids)

    def test_memberships_moved_to_larger_group(self, mock_command):
        company = CompanyFactory()
        anchor_a = StoreFactory(company=company)
        extra_member = StoreFactory(company=company)
        anchor_b = StoreFactory(company=company)
        group_a = _make_group(company, anchor_a, [extra_member])
        group_b = _make_group(company, anchor_b)
        comparer = IntergroupComparer(mock_command)
        comparer._merge_groups(group_a, group_b)
        assert StoreGroup.objects.filter(pk=group_a.pk).exists()
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
        comparer._merge_groups(group_a, group_b)
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
        product = ProductFactory()
        PriceFactory(product=product, store=anchor_a)
        comparer = IntergroupComparer(mock_command)
        comparer.run()
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
        PriceFactory(product=product, store=anchor_a, price=Decimal('5.00'), scraped_date=today)
        PriceFactory(product=product, store=anchor_b, price=Decimal('5.00'), scraped_date=today)
        comparer = IntergroupComparer(mock_command)
        comparer.run()
        assert StoreGroup.objects.filter(pk=group_a.pk).exists()
        assert StoreGroup.objects.filter(pk=group_b.pk).exists()
```

---

## data_management/tests/util_tests/test_internal_group_health_checker.py
```python
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
    group = StoreGroup.objects.create(company=company, anchor=anchor)
    StoreGroupMembership.objects.create(store=anchor, group=group)
    for member in (members or []):
        StoreGroupMembership.objects.create(store=member, group=group)
    return group


class TestStoreHasCurrentPricing:
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
        checker = InternalGroupHealthChecker(mock_command)
        checker.run()

    def test_flags_stale_anchor_for_rescraping(self, mock_command):
        company = CompanyFactory()
        anchor = StoreFactory(company=company)
        member = StoreFactory(company=company)
        group = _make_group(company, anchor, [member])
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
        PriceFactory(product=product, store=anchor, price=Decimal('5.00'), scraped_date=today)
        PriceFactory(product=product, store=member, price=Decimal('9.00'), scraped_date=today)
        checker = InternalGroupHealthChecker(mock_command)
        checker.run()
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
        PriceFactory(product=product, store=anchor, price=Decimal('5.00'), scraped_date=today)
        PriceFactory(product=product, store=member, price=Decimal('5.00'), scraped_date=today)
        checker = InternalGroupHealthChecker(mock_command)
        checker.run()
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
        assert not Price.objects.filter(pk=member_price.pk).exists()

    def test_solo_groups_are_not_checked(self, mock_command):
        company = CompanyFactory()
        anchor = StoreFactory(company=company, needs_rescraping=False)
        _make_group(company, anchor)
        checker = InternalGroupHealthChecker(mock_command)
        checker.run()
        anchor.refresh_from_db()
        assert anchor.needs_rescraping is False
```

---

## data_management/tests/util_tests/test_grouping.py
```python
from unittest.mock import MagicMock
from data_management.utils.analysis_utils.store_grouping_utils.grouping import find_store_groups

def _store(name):
    s = MagicMock()
    s.store_name = name
    return s

class TestFindStoreGroups:
    def test_single_store_is_an_island(self):
        store = _store('A')
        store_map = {1: store}
        graph = {1: []}
        groups, islands = find_store_groups(store_map, graph)
        assert groups == []
        assert store in islands

    def test_two_connected_stores_form_one_group(self):
        a, b = _store('A'), _store('B')
        store_map = {1: a, 2: b}
        graph = {1: [2], 2: [1]}
        groups, islands = find_store_groups(store_map, graph)
        assert len(groups) == 1
        assert set(groups[0]) == {a, b}
        assert islands == []

    def test_two_disconnected_stores_are_both_islands(self):
        a, b = _store('A'), _store('B')
        store_map = {1: a, 2: b}
        graph = {1: [], 2: []}
        groups, islands = find_store_groups(store_map, graph)
        assert groups == []
        assert set(islands) == {a, b}

    def test_two_separate_groups(self):
        a, b, c, d = _store('A'), _store('B'), _store('C'), _store('D')
        store_map = {1: a, 2: b, 3: c, 4: d}
        graph = {1: [2], 2: [1], 3: [4], 4: [3]}
        groups, islands = find_store_groups(store_map, graph)
        assert len(groups) == 2
        assert islands == []

    def test_three_stores_fully_connected(self):
        a, b, c = _store('A'), _store('B'), _store('C')
        store_map = {1: a, 2: b, 3: c}
        graph = {1: [2, 3], 2: [1, 3], 3: [1, 2]}
        groups, islands = find_store_groups(store_map, graph)
        assert len(groups) == 1
        assert set(groups[0]) == {a, b, c}
        assert islands == []

    def test_mixed_group_and_island(self):
        a, b, c = _store('A'), _store('B'), _store('C')
        store_map = {1: a, 2: b, 3: c}
        graph = {1: [2], 2: [1], 3: []}
        groups, islands = find_store_groups(store_map, graph)
        assert len(groups) == 1
        assert set(groups[0]) == {a, b}
        assert c in islands

    def test_empty_store_map(self):
        groups, islands = find_store_groups({}, {})
        assert groups == []
        assert islands == []
```

---

## data_management/tests/util_tests/test_graph_construction.py
```python
from unittest.mock import MagicMock
from data_management.utils.analysis_utils.store_grouping_utils.graph_construction import build_correlation_graph

def _store(name):
    s = MagicMock()
    s.store_name = name
    return s

class TestBuildCorrelationGraph:
    def test_single_store_graph_has_no_edges(self):
        store_map = {1: _store('A')}
        price_data = {1: {101: 5.00}}
        graph = build_correlation_graph(store_map, price_data, threshold=98)
        assert graph == {1: []}

    def test_identical_prices_above_threshold_creates_edge(self):
        store_map = {1: _store('A'), 2: _store('B')}
        prices = {i: 5.00 for i in range(10)}
        price_data = {1: prices.copy(), 2: prices.copy()}
        graph = build_correlation_graph(store_map, price_data, threshold=98)
        assert 2 in graph[1]
        assert 1 in graph[2]

    def test_no_common_products_creates_no_edge(self):
        store_map = {1: _store('A'), 2: _store('B')}
        price_data = {1: {1: 5.00}, 2: {2: 5.00}}
        graph = build_correlation_graph(store_map, price_data, threshold=50)
        assert graph[1] == []
        assert graph[2] == []

    def test_low_correlation_below_threshold_no_edge(self):
        store_map = {1: _store('A'), 2: _store('B')}
        shared = {i: 5.00 for i in range(5)}
        a_only = {i + 5: 3.00 for i in range(5)}
        b_only = {i + 5: 9.00 for i in range(5)}
        price_data = {1: {**shared, **a_only}, 2: {**shared, **b_only}}
        graph = build_correlation_graph(store_map, price_data, threshold=98)
        assert graph[1] == []
        assert graph[2] == []

    def test_exactly_at_threshold_creates_edge(self):
        store_map = {1: _store('A'), 2: _store('B')}
        prices_a = {i: 5.00 for i in range(100)}
        prices_b = prices_a.copy()
        prices_b[0] = 9.00
        prices_b[1] = 9.00
        price_data = {1: prices_a, 2: prices_b}
        graph = build_correlation_graph(store_map, price_data, threshold=98)
        assert 2 in graph[1]

    def test_graph_has_all_store_ids_as_keys(self):
        store_map = {1: _store('A'), 2: _store('B'), 3: _store('C')}
        price_data = {1: {1: 1.00}, 2: {2: 2.00}, 3: {3: 3.00}}
        graph = build_correlation_graph(store_map, price_data, threshold=98)
        assert set(graph.keys()) == {1, 2, 3}

    def test_edges_are_bidirectional(self):
        store_map = {1: _store('A'), 2: _store('B')}
        prices = {i: 5.00 for i in range(10)}
        price_data = {1: prices.copy(), 2: prices.copy()}
        graph = build_correlation_graph(store_map, price_data, threshold=98)
        assert 2 in graph[1]
        assert 1 in graph[2]
```

---

## products/tests/util_tests/test_get_pricing_stores.py
Full file — see git history. Tests covered: `test_store_is_its_own_anchor`, `test_unpriced_store_falls_back_to_company_default_anchor`, `test_store_with_no_group_membership_maps_to_itself`, `test_multiple_stores_all_get_translated`.

---

## Partial excerpts from edited files

### products/models/price.py — removed PriceQuerySet / for_stores()
```python
# Removed: entire PriceQuerySet class and objects = PriceQuerySet.as_manager()
class PriceQuerySet(models.QuerySet):
    def for_stores(self, store_ids):
        from products.utils.get_pricing_stores import get_pricing_stores_map
        pricing_map = get_pricing_stores_map(store_ids)
        anchor_ids = list(set(pricing_map.values()))
        return self.filter(store_id__in=anchor_ids)
# Price.objects = PriceQuerySet.as_manager()  ← also removed
```

### data_management/utils/cart_optimization/substitute_manager.py — lines 50-51
```python
# Was:
store_prices = Price.objects.for_stores(self.store_ids)
# Replaced with:
store_prices = Price.objects.filter(store_id__in=self.store_ids)
```

### data_management/utils/generation_utils/default_stores_generator.py — full rewrite
```python
# Old version used get_pricing_stores_map() to resolve anchor IDs from nearby stores.
# New version simply saves all store IDs that have any Price rows.
```

### data_management/utils/generation_utils/store_stats_generator.py
```python
# Removed: anchor_ids resolution via group_membership__group__anchor_id
# Removed: stores_with_prices_count and stores_with_fresh_prices_count via anchor
# Simplified to: direct Price.objects.filter(store__company=company) queries only
```

### data_management/database_updating_classes/product_updating/update_orchestrator.py — lines 19, 279-280
```python
from .group_maintanance.group_maintenance_orchestrator import GroupMaintenanceOrchestrator
# ...
GroupMaintenanceOrchestrator(self.command, relaxed_staleness=self.relaxed_staleness).run()
```

### data_management/management/commands/generate.py — lines 13, 62-66
```python
parser.add_argument('--store-groups', action='store_true', help='Generate store groups.')
# ...
if options['store_groups']:
    from data_management.utils.generation_utils.store_groups_generator import StoreGroupsGenerator
    self.stdout.write(self.style.SUCCESS("Generating store groups..."))
    generator = StoreGroupsGenerator(self, dev=dev)
    generator.run()
```

### data_management/tests/command_tests/test_generate_command.py — lines 45-48
```python
@patch(f'{GEN}.store_groups_generator.StoreGroupsGenerator')
def test_store_groups_flag(self, MockGen):
    call_command('generate', store_groups=True)
    MockGen.return_value.run.assert_called_once()
```
