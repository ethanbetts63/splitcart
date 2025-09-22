import random
from companies.models import Store, StoreGroup, StoreGroupMembership
from django.db.models import Count

class ScrapeScheduler:
    """
    Contains the logic for intelligently selecting which stores to scrape next.
    This scheduler uses a continuous loop model, balancing scraping the largest
    store groups with exploring smaller ones and outliers.
    """

    def _get_candidates(self, stores_queryset, limit=1):
        """
        A reusable method that takes a queryset and returns the stores that were
        scraped the longest time ago. It prioritizes stores that have never been scraped
        and filters out any stores that are already serving as a group's ambassador or
        are pending as a candidate.
        """
        # Get IDs of all stores currently assigned as an ambassador or a candidate
        ambassador_ids = StoreGroup.objects.filter(ambassador__isnull=False).values_list('ambassador_id', flat=True)
        candidate_members = StoreGroup.candidates.through.objects.values_list('store_id', flat=True)

        # Combine and filter the main queryset
        excluded_ids = set(list(ambassador_ids)) | set(list(candidate_members))
        eligible_stores = stores_queryset.exclude(id__in=excluded_ids)

        # Prioritize stores that have never been scraped from the eligible list
        unscraped_stores = eligible_stores.filter(last_scraped__isnull=True)
        if unscraped_stores.exists():
            return list(unscraped_stores[:limit])

        # If all eligible stores have been scraped at least once, find the oldest
        return list(eligible_stores.order_by('last_scraped')[:limit])

    def _get_group(self):
        """
        Implements the 80/20 logic for selecting a store group to focus on.
        80% of the time, it exploits the largest group.
        20% of the time, it explores smaller groups or outliers.
        """
        # Annotate groups with their member count
        groups = StoreGroup.objects.filter(is_active=True).annotate(member_count=Count('memberships'))
        
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

    def get_scrape_queue(self, candidate_count=2):
        """
        The main public method that generates the next queue of stores to scrape.
        """
        target_group = self._get_group()
        
        if target_group:
            # We are scraping a specific group
            stores_qs = Store.objects.filter(group_membership__group=target_group)
            return self._get_candidates(stores_qs, limit=candidate_count)
        else:
            # We are scraping an outlier
            outlier_qs = Store.objects.filter(group_membership__isnull=True)
            return self._get_candidates(outlier_qs, limit=candidate_count)
