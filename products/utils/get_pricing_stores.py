from django.core.cache import cache
from django.db.models import Count
from companies.models import Store, StoreGroup
from products.models import Price

def get_default_anchor_for_company(company_id):
    """
    Finds and caches the anchor of the largest store group for a given company.
    This is used as a fallback for nationally-priced companies.
    """
    cache_key = f'default_anchor_{company_id}'
    default_anchor_id = cache.get(cache_key)
    if default_anchor_id:
        return default_anchor_id

    biggest_group = StoreGroup.objects.filter(company_id=company_id) \
                                        .annotate(num_members=Count('memberships')) \
                                        .order_by('-num_members').first()
    if biggest_group and biggest_group.anchor:
        default_anchor_id = biggest_group.anchor.id
        # Cache for 1 hour
        cache.set(cache_key, default_anchor_id, timeout=3600)
        return default_anchor_id
    return None

def get_pricing_stores_map(requested_store_ids):
    """
    Determines the correct anchor store ID for each requested store ID based on
    business logic for price lookups.

    Returns a dictionary mapping {requested_store_id: final_anchor_id}.
    """
    if not requested_store_ids:
        return {}

    stores = Store.objects.filter(id__in=requested_store_ids).select_related(
        'company', 'group_membership__group__anchor'
    )
    store_map = {s.id: s for s in stores}

    # 1. Create initial translation map based on group membership
    translation_map = {}
    self_anchored_store_ids = set()
    for store in stores:
        if store.group_membership and store.group_membership.group and store.group_membership.group.anchor:
            anchor_id = store.group_membership.group.anchor.id
            translation_map[store.id] = anchor_id
            if store.id == anchor_id:
                self_anchored_store_ids.add(store.id)
        else:
            # Store has no group, so it's its own anchor
            translation_map[store.id] = store.id
            self_anchored_store_ids.add(store.id)

    # 2. Find which self-anchored stores have no price data
    priced_self_anchored_ids = set(Price.objects.filter(store_id__in=self_anchored_store_ids).values_list('store_id', flat=True))
    unpriced_self_anchored_ids = self_anchored_store_ids - priced_self_anchored_ids

    # 3. Apply fallback logic for unpriced, self-anchored stores
    for store_id in unpriced_self_anchored_ids:
        store = store_map.get(store_id)
        if not store:
            continue

        # For IGA, do nothing. Accept that it has no prices.
        if store.company.name.lower() == 'iga':
            continue
        
        # For other companies, find the default anchor for their company
        default_anchor_id = get_default_anchor_for_company(store.company.id)
        if default_anchor_id:
            translation_map[store.id] = default_anchor_id
            
    return translation_map