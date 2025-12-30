from rest_framework.views import APIView
from rest_framework.response import Response
from companies.models import Store
from django.db.models import Q
from rest_framework.throttling import ScopedRateThrottle
from api.permissions import IsInternalAPIRequest
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

        store_to_scrape = self._get_next_candidate(company_filter)

        if not store_to_scrape:
            return Response({}, status=204) # No content

        # Un-flag the store if it was a priority scrape and set the scheduled_at time
        if store_to_scrape.needs_rescraping:
            store_to_scrape.needs_rescraping = False
        store_to_scrape.scheduled_at = timezone.now()
        store_to_scrape.save(update_fields=['needs_rescraping', 'scheduled_at'])

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
        # Define base queryset with company filter and exclusions
        stores_qs = Store.objects.filter(company_filter)
        coles_exclusion = Q(company__name='Coles') & ~Q(division_id__in=[1, 2, 3])
        woolworths_exclusion = Q(company__name='Woolworths') & ~Q(division_id=6)
        eligible_stores = stores_qs.exclude(coles_exclusion | woolworths_exclusion)

        # Exclude stores that have been scheduled recently
        four_hours_ago = timezone.now() - timedelta(hours=4)
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
