from datetime import timedelta
from django.utils import timezone
from django.db import transaction, models
from companies.models import Store, StoreGroup, StoreGroupMembership
from products.models import Price
from data_management.utils.price_comparer import PriceComparer
from data_management.utils.health_check_cache_manager import HealthCheckCacheManager

class InternalGroupHealthChecker:
    """
    Handles the logic for Phase 1: Internal Group Maintenance (Health Checks).
    It compares members to their anchor to find and eject stores that no longer match.
    """
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
                # If there are no prices, fall back to the default
                self.freshness_threshold = timezone.now() - timedelta(days=7)
        else:
            self.freshness_threshold = timezone.now() - timedelta(days=7)
        
        self.command.stdout.write(f"  - Using freshness threshold: {self.freshness_threshold.date()}")

    def _store_has_current_pricing(self, store_id, all_prices_cache):
        """Helper method to check if a store has any price data in the pre-fetched cache."""
        return store_id in all_prices_cache and bool(all_prices_cache[store_id])

    def _eject_member(self, member_store, old_group):
        """Ejects a member from its group and places it into a new group of one."""
        self.command.stdout.write(f"    - Ejecting member '{member_store.store_name}' from Group {old_group.id}.")
        
        # Delete the old membership
        StoreGroupMembership.objects.filter(store=member_store).delete()

        # Create a new group for the ejected member
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
                
                # Pre-fetch prices for the anchor and all its members at once
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

