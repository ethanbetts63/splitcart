from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Count
from companies.models import Store, StoreGroup, StoreGroupMembership
from products.models import Price # Added missing import
from data_management.utils.price_comparer import PriceComparer
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
        active_groups = StoreGroup.objects.filter(is_active=True).prefetch_related('anchor')

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

        # Re-assign all members from the smaller group to the larger group
        StoreGroupMembership.objects.filter(group=smaller_group).update(group=larger_group)

        # Deactivate the smaller group
        smaller_group.is_active = False
        smaller_group.save()

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("--- Running Inter-Group Merging ---"))
        
        # 1. Get all anchors with current pricing
        anchors_to_compare = self._get_anchor_stores_with_current_pricing()
        self.command.stdout.write(f"  - Found {len(anchors_to_compare)} group anchors with current pricing to compare.")

        if len(anchors_to_compare) < 2:
            self.command.stdout.write("  - Not enough active anchors to compare. Skipping.")
            return

        # 2. Generate unique pairs of anchors to compare
        anchor_pairs = list(itertools.combinations(anchors_to_compare, 2))
        self.command.stdout.write(f"  - Generated {len(anchor_pairs)} unique pairs for comparison.")

        # Keep track of merged groups to avoid re-merging
        merged_group_ids = set()

        for anchor_a, anchor_b in anchor_pairs:
            group_a = anchor_a.group_membership.group
            group_b = anchor_b.group_membership.group

            # Skip if either group has already been merged in this run
            if group_a.id in merged_group_ids or group_b.id in merged_group_ids:
                continue

            # 3. Compare the pair
            self.command.stdout.write(f"  - Comparing Anchor '{anchor_a.store_name}' (Group {group_a.id}) vs. '{anchor_b.store_name}' (Group {group_b.id})...")
            if self.comparer.compare(anchor_a, anchor_b):
                self.command.stdout.write(self.command.style.SUCCESS("    - Match found!"))
                # 4. If they match, merge the groups
                with transaction.atomic():
                    self._merge_groups(group_a, group_b)
                # Add the merged group's ID to the set to prevent re-processing
                merged_group_ids.add(group_a.id)
                merged_group_ids.add(group_b.id)
            else:
                self.command.stdout.write("    - No match.")
