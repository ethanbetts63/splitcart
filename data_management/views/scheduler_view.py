from rest_framework.views import APIView
from rest_framework.response import Response
from companies.models import Store
from django.db.models import Q
from rest_framework.throttling import ScopedRateThrottle
from splitcart.permissions import IsInternalAPIRequest
from django.utils import timezone
from datetime import timedelta

class SchedulerView(APIView):
    """
    Provides the next store to be scraped based on a clear priority:
    1. Stores that have never been scraped.
    2. Stores flagged for a high-priority re-scrape.
    3. The store that was scraped the longest time ago.
    """
    permission_classes = [IsInternalAPIRequest]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'internal'

    def get(self, request, *args, **kwargs):
        companies_to_scrape = request.query_params.getlist('company')
        company_filter = Q()
        if companies_to_scrape:
            company_filter = Q(company__name__in=companies_to_scrape)

        now = timezone.now()
        four_hours_ago = now - timedelta(hours=4)

        store_to_scrape = self._get_next_candidate(company_filter)

        if not store_to_scrape:
            return Response({}, status=204) # No content

        # DEBUG: log the state of the selected store before saving
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"[SCHEDULER DEBUG] Selected store PK={store_to_scrape.pk} name={store_to_scrape.store_name!r} "
            f"last_scraped={store_to_scrape.last_scraped!r} "
            f"scheduled_at_before_save={store_to_scrape.scheduled_at!r} "
            f"needs_rescraping={store_to_scrape.needs_rescraping} "
            f"now={now!r} four_hours_ago={four_hours_ago!r}"
        )

        # Un-flag the store if it was a priority scrape and set the scheduled_at time
        if store_to_scrape.needs_rescraping:
            store_to_scrape.needs_rescraping = False
        store_to_scrape.scheduled_at = now
        store_to_scrape.save(update_fields=['needs_rescraping', 'scheduled_at'])

        # DEBUG: re-fetch from DB and confirm the save took effect
        store_to_scrape.refresh_from_db(fields=['scheduled_at'])
        logger.warning(
            f"[SCHEDULER DEBUG] After save+refresh PK={store_to_scrape.pk} "
            f"scheduled_at_after_save={store_to_scrape.scheduled_at!r}"
        )

        response_data = {
            'pk': store_to_scrape.pk,
            'store_id': store_to_scrape.store_id,
            'retailer_store_id': store_to_scrape.retailer_store_id,
            'store_name': store_to_scrape.store_name,
            'company_name': store_to_scrape.company.name,
            'state': store_to_scrape.state,
        }
        return Response(response_data)

    def _get_next_candidate(self, company_filter):
        """
        Determines and returns the single next highest-priority store to scrape.
        """
        import logging
        logger = logging.getLogger(__name__)

        # Define base queryset with company filter and exclusions
        stores_qs = Store.objects.filter(company_filter)
        coles_exclusion = Q(company__name='Coles') & ~Q(division_id__in=[1, 2, 3])
        woolworths_exclusion = Q(company__name='Woolworths') & ~Q(division_id=6)
        eligible_stores = stores_qs.exclude(coles_exclusion | woolworths_exclusion)

        # Exclude stores that have been scheduled recently
        four_hours_ago = timezone.now() - timedelta(hours=4)
        recently_scheduled = eligible_stores.filter(scheduled_at__gte=four_hours_ago)
        logger.warning(
            f"[SCHEDULER DEBUG] Total eligible before 4h exclusion: {eligible_stores.count()} | "
            f"Recently scheduled (excluded): {recently_scheduled.count()} | "
            f"four_hours_ago={four_hours_ago!r}"
        )
        for s in recently_scheduled.order_by('scheduled_at')[:10]:
            logger.warning(
                f"[SCHEDULER DEBUG]   excluded PK={s.pk} name={s.store_name!r} scheduled_at={s.scheduled_at!r}"
            )
        eligible_stores = eligible_stores.exclude(scheduled_at__gte=four_hours_ago)

        # Priority 1: Stores that have never been scraped
        unscraped_store = eligible_stores.filter(last_scraped__isnull=True).order_by('pk').first()
        if unscraped_store:
            return unscraped_store

        # Priority 2: Stores flagged for re-scraping
        priority_store = eligible_stores.filter(needs_rescraping=True).order_by('last_updated').first()
        if priority_store:
            return priority_store

        # Priority 3: Oldest scraped store
        oldest_scraped_store = eligible_stores.order_by('last_scraped', 'pk').first()
        return oldest_scraped_store
