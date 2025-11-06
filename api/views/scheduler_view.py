from rest_framework.views import APIView
from rest_framework.response import Response
from companies.models import Store, StoreGroup
from django.db.models import Count, Q
from django.core.cache import cache
import random
from rest_framework.throttling import ScopedRateThrottle
from api.permissions import IsInternalAPIRequest
from django.utils import timezone
from datetime import timedelta

class SchedulerView(APIView):
    """
    Provides the next store to be scraped, encapsulating the logic
    of the original ScrapeScheduler.
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

        # Set scheduled_at timestamp
        store_to_scrape.scheduled_at = timezone.now()
        store_to_scrape.save(update_fields=['scheduled_at'])

        response_data = {
            'pk': store_to_scrape.pk,
            'store_id': store_to_scrape.store_id,
            'retailer_store_id': store_to_scrape.retailer_store_id,
            'store_name': store_to_scrape.store_name,
            'company_name': store_to_scrape.company.name,
            'state': store_to_scrape.state,
        }
        return Response(response_data)

    def _get_group(self, company_filter):
        """
        Selects a store group to focus on.
        """
        divergent_group = StoreGroup.objects.filter(
            company_filter, 
            is_active=True, 
            status='DIVERGENCE_DETECTED'
        ).first()
        
        if divergent_group:
            return divergent_group

        groups = StoreGroup.objects.filter(company_filter, is_active=True).annotate(member_count=Count('memberships'))
        
        if not groups.exists():
            return None

        largest_group = groups.order_by('-member_count').first()
        
        if random.random() <= 0.8:
            return largest_group
        else:
            if random.random() <= 0.75:
                smaller_groups = groups.exclude(id=largest_group.id)
                if smaller_groups.exists():
                    return random.choice(list(smaller_groups))
                else:
                    return largest_group
            else:
                return None

    def _get_next_candidate(self, company_filter):
        """
        Determines and returns the single next highest-priority store to scrape.
        """
        target_group = self._get_group(company_filter)
        
        if target_group:
            stores_qs = Store.objects.filter(group_membership__group=target_group)
        else:
            stores_qs = Store.objects.filter(company_filter, group_membership__isnull=True)

        coles_exclusion = Q(company__name='Coles') & ~Q(division_id__in=[1, 2, 3])
        woolworths_exclusion = Q(company__name='Woolworths') & ~Q(division_id=6)
        stores_qs = stores_qs.exclude(coles_exclusion | woolworths_exclusion)

        relevant_groups = StoreGroup.objects.filter(company_filter)
        anchor_ids = relevant_groups.filter(anchor__isnull=False).values_list('anchor_id', flat=True)
        candidate_members = relevant_groups.prefetch_related('candidates').values_list('candidates__id', flat=True)

        excluded_ids = set(list(anchor_ids)) | set(list(candidate_members))
        eligible_stores = stores_qs.exclude(id__in=excluded_ids)

        # Exclude stores that have been scheduled recently
        four_hours_ago = timezone.now() - timedelta(hours=4)
        eligible_stores = eligible_stores.exclude(scheduled_at__gte=four_hours_ago)

        unscraped_store = eligible_stores.filter(last_scraped__isnull=True).order_by('pk').first()
        if unscraped_store:
            return unscraped_store

        oldest_scraped_store = eligible_stores.order_by('last_scraped', 'pk').first()
        if oldest_scraped_store:
            return oldest_scraped_store
        
        return None
