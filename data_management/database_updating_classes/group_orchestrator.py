from products.models import Price
from companies.models import Store, StoreGroup, StoreGroupMembership
from data_management.database_updating_classes.unit_of_work import UnitOfWork
from data_management.utils.price_normalizer import PriceNormalizer


class GroupOrchestrator:
    """
    Orchestrates the process of verifying group integrity after new data has been scraped.
    It compares new 'Candidate' stores against the group's 'Ambassador' to detect any divergence.
    """
    def __init__(self, unit_of_work: UnitOfWork):
        self.uow = unit_of_work
        self.true_overlap_threshold = 95.0  # e.g., 95%

    def run(self):
        """Main entry point to run the group integrity check."""
        print("Starting group integrity check...")
        
        groups_with_candidates = StoreGroup.objects.filter(candidates__isnull=False).distinct()
        
        if not groups_with_candidates.exists():
            print("No groups with candidates found to check.")
            return

        for group in groups_with_candidates:
            # Note: Convert queryset to list to avoid issues with modification during iteration
            candidates_in_group = list(group.candidates.all())
            if not candidates_in_group:
                continue

            self._perform_health_check(group, candidates_in_group)
            
            # Stage the group for candidate cleanup
            self.uow.add_group_to_clear_candidates(group)

        print("Group integrity check complete.")

    def _perform_health_check(self, group, candidates):
        """
        Performs the Anchor vs. Candidate workflow for a single group, handling
        an arbitrary number of candidates.
        """
        anchor = group.anchor
        if not anchor:
            print(f"Warning: Group {group} has no Anchor. Promoting first candidate.")
            self._promote_new_anchor(group, candidates[0])
            # In a real run, we might want to re-run the check for the rest of the candidates
            return

        print(f"--- Health Check for Group: {group} ---")
        print(f"Current Anchor: {anchor.store_name}")

        confirmed_matches = []
        potential_rogues = []

        for candidate in candidates:
            print(f"  Testing Candidate: {candidate.store_name}...")
            if self._is_match(candidate, anchor):
                print(f"    -> Match")
                confirmed_matches.append(candidate)
            else:
                print(f"    -> NO MATCH")
                potential_rogues.append(candidate)

        if confirmed_matches:
            # The group is healthy. Promote a new anchor and outcast any rogues.
            new_anchor = confirmed_matches[0]
            print(f"Group is healthy. Promoting {new_anchor.store_name} to new Anchor.")
            self._promote_new_anchor(group, new_anchor)
            
            # Infer prices for the rest of the group based on the new anchor's data
            self._infer_prices_for_group(group, new_anchor, confirmed_matches)

            for rogue in potential_rogues:
                print(f"Outcasting rogue store: {rogue.store_name}")
                self._outcast_rogue(rogue)
        else:
            # All candidates failed to match the anchor. This is a major divergence.
            print(f"Major Divergence! All candidates failed to match Anchor {anchor.store_name}.")

            # Check if there are any other members in the group who were NOT part of this check.
            # We exclude the anchor and all the candidates we just tested.
            other_members_exist = group.memberships.exclude(
                store_id=group.anchor_id
            ).exclude(
                store_id__in=[c.id for c in candidates]
            ).exists()

            if other_members_exist:
                print(f"  Group {group} has other members. Marking as 'Divergence Detected'.")
                group.status = 'DIVERGENCE_DETECTED'
                self.uow.add_for_update(group)
                
                # Even in a divergence, the failed candidates are considered rogue and must be outcast.
                for rogue in candidates:
                    print(f"  Outcasting failed candidate: {rogue.store_name}")
                    self._outcast_rogue(rogue)
            else:
                print(f"  Group {group} has no other members left to test. Dissolving group.")
                self._dissolve_group(group)

    def _get_active_prices_for_store(self, store):
        """
        Fetches the most recent price for each product in a given store.
        Returns a dictionary mapping {product_id: price}.
        """
        all_prices = Price.objects.filter(store=store)
        return {price.product_id: price.price for price in all_prices}

    def _is_match(self, store_a, store_b):
        """
        Calculates the 'True Overlap' between two stores with a 'fail-fast' optimization.
        """
        print(f"    Comparing prices for {store_a.store_name} and {store_b.store_name}...")
        prices_a = self._get_active_prices_for_store(store_a)
        prices_b = self._get_active_prices_for_store(store_b)

        if not prices_a or not prices_b:
            print("    One or both stores have no active prices. Cannot compare.")
            return False

        common_product_ids = set(prices_a.keys()) & set(prices_b.keys())
        num_common = len(common_product_ids)

        if not common_product_ids:
            print("    No common products found between the stores.")
            return False

        # Calculate the minimum number of matches required to meet the threshold
        required_matches = num_common * (self.true_overlap_threshold / 100.0)

        matches_found = 0
        items_checked = 0
        
        for product_id in common_product_ids:
            items_checked += 1
            if prices_a[product_id] == prices_b[product_id]:
                matches_found += 1
            
            # Fail-fast check
            items_remaining = num_common - items_checked
            # If the best possible score we can get is less than what's required, fail now.
            if (matches_found + items_remaining) < required_matches:
                print(f"    Failing fast after checking {items_checked}/{num_common} items.")
                return False

        # If we finish the loop, calculate the final percentage
        overlap_percentage = (matches_found / num_common) * 100
        
        print(f"    Found {num_common} common products.")
        print(f"    Found {matches_found} identically priced products.")
        print(f"    True Overlap: {overlap_percentage:.2f}%")

        return overlap_percentage >= self.true_overlap_threshold

    def _promote_new_anchor(self, group, new_anchor_store):
        """Updates the group to set a new anchor."""
        group.anchor = new_anchor_store
        self.uow.add_for_update(group)

    def _outcast_rogue(self, rogue_store):
        """Removes a store from its group and attempts to re-home it."""
        # Store the group membership before deleting it, to exclude it from re-homing search
        membership = rogue_store.group_membership
        old_group_id = membership.group.id if membership else None
        
        if membership:
            self.uow.add_membership_to_delete(membership)

        print(f"  Store {rogue_store.store_name} outcast. Attempting to find a new home...")
        self._find_new_home_for_rogue(rogue_store, old_group_id)

    def _find_new_home_for_rogue(self, rogue_store, old_group_id=None):
        """
        Attempts to find a new group for a rogue store by comparing it directly
        against other group Anchors using the True Overlap metric.
        """
        print(f"  Attempting to re-home Rogue: {rogue_store.store_name}...")
        
        # Get all other active groups for the same company
        potential_groups = StoreGroup.objects.filter(
            company=rogue_store.company,
            is_active=True
        )
        if old_group_id:
            potential_groups = potential_groups.exclude(id=old_group_id) # Exclude its old group

        for group in potential_groups:
            anchor = group.anchor
            if not anchor:
                continue # Skip groups without an anchor

            print(f"    Checking against Group: {group} (Anchor: {anchor.store_name})...")
            
            # Directly use the _is_match (True Overlap) for simplicity
            if self._is_match(rogue_store, anchor):
                print(f"      Match found! Re-homing {rogue_store.store_name} to Group: {group}.")
                self.uow.add_membership_to_create(rogue_store, group)
                return # Found a home, exit

        print(f"  {rogue_store.store_name} could not be re-homed. It remains an outlier.")

    def _dissolve_group(self, group):
        """Deactivates a group and removes all its members."""
        print(f"  Dissolving group {group} due to major schism.")
        for membership in group.memberships.all():
            self.uow.add_membership_to_delete(membership)
        
        group.is_active = False
        self.uow.add_for_update(group)

    def _infer_prices_for_group(self, group, new_anchor, candidates):
        """
        Infers prices for all non-scraped members of a group based on the new anchor's data.
        """
        print(f"  Inferring prices for group {group} from anchor {new_anchor.store_name}.")

        # Get the most recent prices for the anchor store
        anchor_prices = Price.objects.filter(store=new_anchor)
        
        if not anchor_prices:
            print(f"  Warning: Anchor {new_anchor.store_name} has no prices to infer from.")
            return

        # Find the stores in the group that were NOT scraped in this run
        candidate_ids = {c.id for c in candidates}
        target_stores = Store.objects.filter(group_membership__group=group).exclude(id__in=candidate_ids)

        if not target_stores:
            print("  No other member stores in the group to infer prices for.")
            return
            
        print(f"  Found {len(target_stores)} member stores to infer prices for.")
        
        newly_inferred_prices = []
        for store in target_stores:
            for anchor_price in anchor_prices:
                newly_inferred_prices.append(
                    Price(
                        product=anchor_price.product,
                        store=store,
                        scraped_date=anchor_price.scraped_date,
                        price=anchor_price.price,
                        was_price=anchor_price.was_price,
                        unit_price=anchor_price.unit_price,
                        unit_of_measure=anchor_price.unit_of_measure,
                        per_unit_price_string=anchor_price.per_unit_price_string,
                        is_on_special=anchor_price.is_on_special,
                        source='inferred_group'
                    )
                )
        
        if newly_inferred_prices:
            print(f"  Staging {len(newly_inferred_prices)} new inferred prices for creation.")
            # Use ignore_conflicts=True to prevent errors if a price for that product/store already exists.
            # This can happen in complex scenarios and it's safer to just skip creating the duplicate.
            Price.objects.bulk_create(newly_inferred_prices, ignore_conflicts=True, batch_size=500)
