from companies.models import Store, StoreGroup, StoreGroupMembership
from django.db.models import Count, Q

class ScrapeScheduler:
    """
    Contains the logic for intelligently selecting which stores to scrape next
    based on the discovery and optimization strategy.
    """

    def _get_oldest_unscraped_from_queryset(self, stores_queryset, limit=1):
        """
        A reusable method that takes a queryset and returns the stores that were
        scraped the longest time ago. It prioritizes stores that have never been scraped.
        """
        # Prioritize stores that have never been scraped
        unscraped_stores = stores_queryset.filter(last_scraped_products__isnull=True)
        if unscraped_stores.exists():
            return list(unscraped_stores[:limit])

        # If all have been scraped at least once, find the oldest
        return list(stores_queryset.order_by('last_scraped_products')[:limit])

    def get_discovery_mode_queue(self, batch_size=20):
        """
        Generates a queue of stores to scrape during the Discovery Phase,
        following the 80/20 strategy.
        """
        queue = []
        num_primary_scrapes = int(batch_size * 0.8)
        num_exploratory_scrapes = batch_size - num_primary_scrapes

        # 1. Find the Primary Target Cluster
        # This is the largest group that still has unscraped stores.
        primary_target_group = StoreGroup.objects.annotate(
            unscraped_count=Count('memberships__store', filter=Q(memberships__store__last_scraped_products__isnull=True))
        ).filter(unscraped_count__gt=0).order_by('-unscraped_count').first()

        # 2. Get the 80% from the Primary Target Cluster
        if primary_target_group:
            primary_stores_qs = Store.objects.filter(
                group_membership__group=primary_target_group,
                last_scraped_products__isnull=True
            )
            # In discovery, we just get any unscraped, order doesn't matter as much
            primary_stores_to_add = list(primary_stores_qs[:num_primary_scrapes])
            queue.extend(primary_stores_to_add)

        # 3. Get the 20% from all other unscraped stores (exploratory)
        all_unscraped_qs = Store.objects.filter(last_scraped_products__isnull=True)
        
        # Exclude any stores already in the queue
        queued_store_ids = [store.id for store in queue]
        exploratory_stores_qs = all_unscraped_qs.exclude(id__in=queued_store_ids)

        # We use a random order for the exploratory part to ensure variety
        exploratory_stores = list(exploratory_stores_qs.order_by('?')[:num_exploratory_scrapes])
        queue.extend(exploratory_stores)

        if not queue:
            print("No unscraped stores found for discovery mode.")

        return queue