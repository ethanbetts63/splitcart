from products.models import Price
from companies.models import StoreGroup, StoreGroupMembership

class GroupOrchestrator:
    """
    Orchestrates the process of verifying group integrity after new data has been scraped.
    It compares new 'Candidate' stores against the group's 'Ambassador' to detect any divergence.
    """
    def __init__(self, recently_scraped_stores):
        self.candidates = recently_scraped_stores
        self.true_overlap_threshold = 95.0  # e.g., 95%

    def run(self):
        """Main entry point to run the group integrity check."""
        print("Starting group integrity check...")
        groups_to_check = self._group_candidates()

        for group, candidates_in_group in groups_to_check.items():
            self._perform_health_check(group, candidates_in_group)
        
        print("Group integrity check complete.")

    def _group_candidates(self):
        """Groups candidate stores by their parent StoreGroup."""
        grouped = {}
        for store in self.candidates:
            if store.group_membership:
                group = store.group_membership.group
                if group not in grouped:
                    grouped[group] = []
                grouped[group].append(store)
        return grouped

    def _perform_health_check(self, group, candidates):
        """
        Performs the Ambassador vs. Candidate workflow for a single group, handling
        an arbitrary number of candidates.
        """
        ambassador = group.ambassador
        if not ambassador:
            print(f"Warning: Group {group.name} has no Ambassador. Promoting first candidate.")
            self._promote_new_ambassador(group, candidates[0])
            # In a real run, we might want to re-run the check for the rest of the candidates
            return

        print(f"--- Health Check for Group: {group.name} ---")
        print(f"Current Ambassador: {ambassador.store_name}")

        confirmed_matches = []
        potential_rogues = []

        for candidate in candidates:
            print(f"  Testing Candidate: {candidate.store_name}...")
            if self._is_match(candidate, ambassador):
                print(f"    -> Match")
                confirmed_matches.append(candidate)
            else:
                print(f"    -> NO MATCH")
                potential_rogues.append(candidate)

        if confirmed_matches:
            # The group is healthy. Promote a new ambassador and outcast any rogues.
            new_ambassador = confirmed_matches[0]
            print(f"Group is healthy. Promoting {new_ambassador.store_name} to new Ambassador.")
            self._promote_new_ambassador(group, new_ambassador)
            # Prices for the group would be inferred from new_ambassador here

            for rogue in potential_rogues:
                print(f"Outcasting rogue store: {rogue.store_name}")
                self._outcast_rogue(rogue)
        else:
            # All candidates failed to match the ambassador. This is a major divergence.
            print(f"Major Divergence! All candidates failed to match Ambassador {ambassador.store_name}.")
            self._dissolve_group(group)

    def _get_active_prices_for_store(self, store):
        """
        Fetches the current, active prices for all products in a given store.
        Returns a dictionary mapping {product_id: price}.
        """
        active_prices = Price.objects.filter(store=store, is_active=True).select_related('price_record', 'price_record__product')
        return {price.price_record.product_id: price.price_record.price for price in active_prices}

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

    def _promote_new_ambassador(self, group, new_ambassador_store):
        """Updates the group to set a new ambassador."""
        group.ambassador = new_ambassador_store
        group.save()

    def _outcast_rogue(self, rogue_store):
        """Removes a store from its group and attempts to re-home it."""
        # Store the group membership before deleting it, to exclude it from re-homing search
        old_group_id = rogue_store.group_membership.group.id if rogue_store.group_membership else None
        rogue_store.group_membership.delete()
        print(f"  Store {rogue_store.store_name} outcast. Attempting to find a new home...")
        self._find_new_home_for_rogue(rogue_store, old_group_id)

    def _find_new_home_for_rogue(self, rogue_store, old_group_id=None):
        """
        Attempts to find a new group for a rogue store by comparing it directly
        against other group Ambassadors using the True Overlap metric.
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
            ambassador = group.ambassador
            if not ambassador:
                continue # Skip groups without an ambassador

            print(f"    Checking against Group: {group.name} (Ambassador: {ambassador.store_name})...")
            
            # Directly use the _is_match (True Overlap) for simplicity
            if self._is_match(rogue_store, ambassador):
                print(f"      Match found! Re-homing {rogue_store.store_name} to Group: {group.name}.")
                StoreGroupMembership.objects.create(store=rogue_store, group=group)
                return # Found a home, exit

        print(f"  {rogue_store.store_name} could not be re-homed. It remains an outlier.")

    def _dissolve_group(self, group):
        """Deactivates a group and removes all its members."""
        print(f"  Dissolving group {group.name} due to major schism.")
        group.memberships.all().delete()
        group.is_active = False
        group.save()
