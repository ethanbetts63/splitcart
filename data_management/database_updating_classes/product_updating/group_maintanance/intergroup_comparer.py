from django.db import transaction
from django.db.models import Count
from companies.models import Store, StoreGroup, StoreGroupMembership
from products.models import Price
from data_management.utils.price_comparer import PriceComparer
from data_management.utils.group_comparison_cache_manager import ComparisonCacheManager
import itertools
import random

class IntergroupComparer:
    """
    Handles the logic for Phase 2: Inter-Group Merging.
    It compares the anchors of all groups with price data and merges any that are identical.
    """
    def __init__(self, command, **kwargs):
        self.command = command
        self.comparer = PriceComparer()

    def _get_groups_with_any_pricing(self):
        """Get all active groups whose anchor has any price data."""
        return StoreGroup.objects.filter(
            anchor__prices__isnull=False
        ).distinct().prefetch_related('anchor', 'company')

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
                
                all_groups = self._get_groups_with_any_pricing()
                self.command.stdout.write(f"  - Found {len(all_groups)} total groups with any pricing.")

                if len(all_groups) < 2:
                    self.command.stdout.write("  - Not enough active groups to compare. Halting.")
                    break

                # Group anchors by company
                groups_by_company = {}
                for group in all_groups:
                    if group.company_id not in groups_by_company:
                        groups_by_company[group.company_id] = []
                    groups_by_company[group.company_id].append(group)

                # Process each company's anchors separately
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

                    # Step 1: Generate all potential pairs for the selected groups
                    potential_pairs = list(itertools.combinations(groups_to_process, 2))
                    self.command.stdout.write(f"     - Generated {len(potential_pairs)} potential pairs for comparison.")

                    # Step 2: Filter out pairs that should be skipped
                    pairs_to_compare = []
                    for group_a, group_b in potential_pairs:
                        if not cache_manager.should_skip(group_a.id, group_b.id):
                            pairs_to_compare.append((group_a, group_b))
                    
                    skipped_count = len(potential_pairs) - len(pairs_to_compare)
                    if skipped_count > 0:
                        self.command.stdout.write(f"     - Skipping {skipped_count} pairs based on recent comparison cache.")
                    
                    # Step 3: Identify the unique set of anchors that actually need their prices fetched
                    necessary_anchor_ids = set()
                    for group_a, group_b in pairs_to_compare:
                        if group_a.anchor:
                            necessary_anchor_ids.add(group_a.anchor.id)
                        if group_b.anchor:
                            necessary_anchor_ids.add(group_b.anchor.id)
                    
                    # Step 4: Pre-fetch prices only for the necessary anchors
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

                    # Step 5: Perform the comparisons on the pre-filtered list
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
