from datetime import timedelta
from django.utils import timezone
from django.db import transaction, models
from companies.models import Store, StoreGroup, StoreGroupMembership
from data_management.utils.price_comparer import PriceComparer

class InternalGroupHealthChecker:
    """
    Handles the logic for Phase 1: Internal Group Maintenance (Health Checks).
    It compares members to their anchor to find and eject stores that no longer match.
    """
    def __init__(self, command):
        self.command = command
        self.comparer = PriceComparer(freshness_days=3) # Use 72-hour freshness rule
        self.freshness_threshold = timezone.now() - timedelta(days=3)

    def _store_has_current_pricing(self, store):
        """Helper method to check if a store has any price data newer than the threshold."""
        return store.prices.filter(scraped_date__gte=self.freshness_threshold).exists()

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
        
        groups_to_check = StoreGroup.objects.annotate(num_members=models.Count('memberships')).filter(num_members__gt=1)
        self.command.stdout.write(f"  - Found {len(groups_to_check)} groups with more than one member to check.")

        for group in groups_to_check:
            anchor = group.anchor
            if not anchor:
                self.command.stdout.write(self.command.style.WARNING(f"  - Skipping Group {group.id}: No anchor set."))
                continue

            self.command.stdout.write(f"  - Checking Group {group.id} (Anchor: {anchor.store_name})...")
            anchor_is_current = self._store_has_current_pricing(anchor)
            
            # Get all members excluding the anchor
            members_to_check = Store.objects.filter(group_membership__group=group).exclude(pk=anchor.pk)

            for member in members_to_check:
                if not self._store_has_current_pricing(member):
                    # If member has no current data, we can't check it. Skip.
                    continue

                # We have current data for the member. Now we can perform a check.
                self.command.stdout.write(f"    - Comparing member '{member.store_name}' against anchor...")
                
                match = self.comparer.compare(anchor, member)

                if not match:
                    # The stores do not match. Now we apply the stale anchor rule.
                    if not anchor_is_current:
                        # Anchor data is stale. Flag it for a high-priority re-scrape.
                        self.command.stdout.write(self.command.style.WARNING(f"    - Mismatch found, but anchor data is stale. Flagging anchor '{anchor.store_name}' for re-scrape."))
                        anchor.needs_rescraping = True
                        anchor.save(update_fields=['needs_rescraping'])
                    else:
                        # Anchor data is fresh, so the member is a confirmed rogue.
                        self.command.stdout.write(self.command.style.ERROR(f"    - Mismatch confirmed. Ejecting member."))
                        with transaction.atomic():
                            self._eject_member(member, group)
                else:
                    self.command.stdout.write(self.command.style.SUCCESS("    - Match confirmed. Member is healthy."))
