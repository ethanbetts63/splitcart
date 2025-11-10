from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Count
from companies.models import Store, StoreGroup, StoreGroupMembership
from products.models import Price # Added missing import
from data_management.utils.price_comparer import PriceComparer
from data_management.utils.group_comparison_cache_manager import ComparisonCacheManager
import itertools

class IntergroupComparer:
    """
    Handles the logic for Phase 2: Inter-Group Merging.
    It compares the anchors of all groups with recent data and merges any that are identical.
    """
    def __init__(self, command):
        self.command = command
        self.comparer = PriceComparer(freshness_days=3)
        self.freshness_threshold = timezone.now() - timedelta(days=3)

    def _get_anchor_stores_with_current_pricing(self):
        """Get all active group anchors that have recent price data."""
        # Get IDs of stores that have recent prices
        stores_with_recent_prices = Price.objects.filter(
            scraped_date__gte=self.freshness_threshold
        ).values_list('store_id', flat=True).distinct()

        # Get active groups and their anchors
        active_groups = StoreGroup.objects.prefetch_related('anchor')

        # Filter to get only anchors that have recent prices
        anchors_to_compare = [
            g.anchor for g in active_groups 
            if g.anchor and g.anchor.id in stores_with_recent_prices
        ]
        return anchors_to_compare

    def _merge_groups(self, group_a, group_b):
        """Merges the smaller group into the larger group."""
        # Determine which is the larger group and which is the smaller
        if group_a.memberships.count() >= group_b.memberships.count():
            larger_group, smaller_group = group_a, group_b
        else:
            larger_group, smaller_group = group_b, group_a

        self.command.stdout.write(f"    - Merging Group {smaller_group.id} into Group {larger_group.id}.")

        # Get all stores from the smaller group whose prices will be deleted.
        stores_to_purge = Store.objects.filter(group_membership__group=smaller_group)
        store_ids_to_purge = list(stores_to_purge.values_list('id', flat=True))

        # Re-assign all members from the smaller group to the larger group
        StoreGroupMembership.objects.filter(group=smaller_group).update(group=larger_group)

        # Delete the prices for the stores from the now-merged smaller group
        if store_ids_to_purge:
            self.command.stdout.write(f"    - Deleting redundant prices for {len(store_ids_to_purge)} stores from dissolved group.")
            deleted_count, _ = Price.objects.filter(store_id__in=store_ids_to_purge).delete()
            self.command.stdout.write(f"    - Deleted {deleted_count:,} price objects.")

        # Delete the now-empty smaller group
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
                
                anchors_to_compare = self._get_anchor_stores_with_current_pricing()
                self.command.stdout.write(f"  - Found {len(anchors_to_compare)} group anchors with current pricing to compare in this pass.")

                if len(anchors_to_compare) < 2:
                    self.command.stdout.write("  - Not enough active anchors to compare. Skipping pass.")
                    break

                anchor_pairs = list(itertools.combinations(anchors_to_compare, 2))
                self.command.stdout.write(f"  - Generated {len(anchor_pairs)} unique pairs for comparison in this pass.")

                merged_group_ids_this_pass = set()
                skipped_count = 0

                for anchor_a, anchor_b in anchor_pairs:
                    group_a = anchor_a.group_membership.group
                    group_b = anchor_b.group_membership.group

                    if group_a.id in merged_group_ids_this_pass or group_b.id in merged_group_ids_this_pass:
                        continue
                    
                    # Use the cache to skip recent non-matches
                    if cache_manager.should_skip(group_a.id, group_b.id):
                        skipped_count += 1
                        continue

                    self.command.stdout.write(f"  - Comparing Anchor '{anchor_a.store_name}' (Group {group_a.id}) vs. '{anchor_b.store_name}' (Group {group_b.id})...")
                    if self.comparer.compare(anchor_a, anchor_b):
                        self.command.stdout.write(self.command.style.SUCCESS("    - Match found!"))
                        with transaction.atomic():
                            self._merge_groups(group_a, group_b)
                        
                        merges_occurred_in_pass = True
                        merges_occurred_in_total += 1
                        merged_group_ids_this_pass.add(group_a.id)
                        merged_group_ids_this_pass.add(group_b.id) 
                    else:
                        self.command.stdout.write("    - No match.")
                        # Record the non-match in the cache
                        cache_manager.record_comparison(group_a.id, group_b.id)
                
                if skipped_count > 0:
                    self.command.stdout.write(f"  - Skipped {skipped_count} pairs based on recent comparison cache.")

                if not merges_occurred_in_pass:
                    self.command.stdout.write("  - No merges occurred in this pass. Merging complete.")
                    break
                else:
                    self.command.stdout.write(f"  - {merges_occurred_in_pass} merges occurred in this pass. Re-evaluating for more merges.")

        finally:
            # Ensure the cache is always saved, even if an error occurs
            cache_manager.save()

        self.command.stdout.write(self.command.style.SUCCESS(f"--- Inter-Group Merging Complete. Total merges: {merges_occurred_in_total} ---"))
