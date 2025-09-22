from products.models import Price

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
        active_prices = Price.objects.filter(store=store, is_active=True)
        return {price.product_id: price.price for price in active_prices}

    def _is_match(self, store_a, store_b):
        """Calculates the 'True Overlap' between two stores based on their active prices."""
        print(f"    Comparing prices for {store_a.store_name} and {store_b.store_name}...")
        prices_a = self._get_active_prices_for_store(store_a)
        prices_b = self._get_active_prices_for_store(store_b)

        if not prices_a or not prices_b:
            print("    One or both stores have no active prices. Cannot compare.")
            return False

        common_product_ids = set(prices_a.keys()) & set(prices_b.keys())

        if not common_product_ids:
            print("    No common products found between the stores.")
            return False

        identically_priced_count = 0
        for product_id in common_product_ids:
            if prices_a[product_id] == prices_b[product_id]:
                identically_priced_count += 1
        
        # The overlap percentage is based on the number of common products
        overlap_percentage = (identically_priced_count / len(common_product_ids)) * 100
        
        print(f"    Found {len(common_product_ids)} common products.")
        print(f"    Found {identically_priced_count} identically priced products.")
        print(f"    True Overlap: {overlap_percentage:.2f}%")

        return overlap_percentage >= self.true_overlap_threshold

    def _promote_new_ambassador(self, group, new_ambassador_store):
        """Updates the group to set a new ambassador."""
        group.ambassador = new_ambassador_store
        group.save()

    def _outcast_rogue(self, rogue_store):
        """Removes a store from its group and attempts to re-home it."""
        rogue_store.group_membership.delete()
        print(f"  Store {rogue_store.store_name} outcast. Attempting to find a new home...")
        self._find_new_home_for_rogue(rogue_store)

    def _find_new_home_for_rogue(self, rogue_store):
        """Implements the two-stage check to find a new group for a rogue store."""
        # This is a placeholder for the re-homing logic.
        # 1. Get all other groups.
        # 2. For each group, run cheap "Range Overlap" check against its Ambassador.
        # 3. If Range Overlap > threshold, run expensive "True Overlap" check.
        # 4. If a match is found, create a new StoreGroupMembership.
        # 5. If no match is found, the store remains an outlier.
        print(f"  (Placeholder) Re-homing process for {rogue_store.store_name} would run here.")
        return

    def _dissolve_group(self, group):
        """Deactivates a group and removes all its members."""
        print(f"  Dissolving group {group.name} due to major schism.")
        group.memberships.all().delete()
        group.is_active = False
        group.save()
