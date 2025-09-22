import random
from companies.models import Store, StoreGroup
from django.db.models import Count, Q

class ScrapeScheduler:
    """
    Contains the logic for intelligently selecting which stores to scrape next.
    This scheduler uses a continuous loop model, balancing scraping the largest
    store groups with exploring smaller ones and outliers.
    """
    def __init__(self, companies=None):
        """
        Initializes the scheduler, optionally filtering its scope to a specific
        list of company names.
        """
        self.company_filter = Q()
        if companies:
            self.company_filter = Q(company__name__in=companies)

    def _get_group(self):
        """
        Implements the 80/20 logic for selecting a store group to focus on.
        80% of the time, it exploits the largest group.
        20% of the time, it explores smaller groups or outliers.
        """
        # Annotate groups with their member count, applying the company filter
        groups = StoreGroup.objects.filter(self.company_filter, is_active=True).annotate(member_count=Count('memberships'))
        
        if not groups.exists():
            return None # No groups to choose from, default to outlier

        largest_group = groups.order_by('-member_count').first()
        
        # 80/20 split
        if random.random() <= 0.8:
            return largest_group # Exploit largest group
        else:
            # Explore: 15% chance for a smaller group, 5% for an outlier
            if random.random() <= 0.75: # This is 75% of the 20% explore chance
                smaller_groups = groups.exclude(id=largest_group.id)
                if smaller_groups.exists():
                    return random.choice(list(smaller_groups))
                else:
                    return largest_group # Fallback to largest if no smaller groups
            else:
                return None # Signal to scrape an outlier

    def get_next_candidate(self):
        """
        The main public method that determines and returns the single next
        highest-priority store to scrape. It contains all logic for selecting
        a candidate, from group selection to filtering.
        """
        target_group = self._get_group()
        
        # Determine the base queryset based on the group selection
        if target_group:
            # The group is already filtered by company, so members are implicitly filtered
            stores_qs = Store.objects.filter(group_membership__group=target_group)
        else:
            # Outlier query needs the company filter
            stores_qs = Store.objects.filter(self.company_filter, group_membership__isnull=True)

        # Define and apply the division-based exclusion filters
        coles_exclusion = Q(company__name='Coles') & ~Q(division_id__in=[1, 2, 3])
        woolworths_exclusion = Q(company__name='Woolworths') & ~Q(division_id=6)
        stores_qs = stores_qs.exclude(coles_exclusion | woolworths_exclusion)

        # Get IDs of all stores currently assigned as an ambassador or a candidate within the scope
        relevant_groups = StoreGroup.objects.filter(self.company_filter)
        ambassador_ids = relevant_groups.filter(ambassador__isnull=False).values_list('ambassador_id', flat=True)
        candidate_members = relevant_groups.prefetch_related('candidates').values_list('candidates__id', flat=True)

        # Combine and filter the main queryset
        excluded_ids = set(list(ambassador_ids)) | set(list(candidate_members))
        eligible_stores = stores_qs.exclude(id__in=excluded_ids)

        # Prioritize the first store that has never been scraped from the eligible list
        unscraped_store = eligible_stores.filter(last_scraped__isnull=True).first()
        if unscraped_store:
            return unscraped_store

        # If all eligible stores have been scraped at least once, find the oldest
        return eligible_stores.order_by('last_scraped').first()