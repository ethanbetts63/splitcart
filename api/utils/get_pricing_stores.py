from django.core.cache import cache
from django.db.models import Count
from companies.models import Store, StoreGroup
from products.models import Price

def get_default_anchor(company_id):
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

def get_pricing_stores(requested_store_ids):
    """
    Determines the correct store IDs to use for price lookups.

    For a given list of store IDs, this function returns a list of store IDs that
    should be used for fetching prices.

    - If a store's designated anchor has price data, that anchor is used.
    - If the anchor has no price data and the store is not IGA, it falls back
      to the default national anchor for that company.
    - For IGA, it always uses the store's own anchor.
    """
    if not requested_store_ids:
        return []

    stores = Store.objects.filter(id__in=requested_store_ids).select_related(
        'company', 'group_membership__group__anchor'
    )
    
    # Create a map of {store_id: store_object}
    store_map = {s.id: s for s in stores}

    # Get all unique anchors for the requested stores
    anchor_map = {
        s.id: s.group_membership.group.anchor
        for s in stores if s.group_membership and s.group_membership.group and s.group_membership.group.anchor
    }
    all_possible_anchor_ids = {a.id for a in anchor_map.values()}

    # Find which of those anchors have price data
    priced_anchor_ids = set(Price.objects.filter(store_id__in=all_possible_anchor_ids).values_list('store_id', flat=True))

    final_pricing_stores = set()

    for store_id in requested_store_ids:
        store = store_map.get(store_id)
        if not store:
            continue

        anchor = anchor_map.get(store.id)

        # Case 1: The store's anchor has prices. Use it.
        if anchor and anchor.id in priced_anchor_ids:
            final_pricing_stores.add(anchor.id)
            continue

        # Case 2: Anchor has no prices, and company is not IGA. Use default.
        if store.company.name != 'Iga':
            default_anchor_id = get_default_anchor(store.company.id)
            if default_anchor_id:
                final_pricing_stores.add(default_anchor_id)
            # Fallback to the store's own (unpriced) anchor if no default exists
            elif anchor:
                final_pricing_stores.add(anchor.id)
            else: # Ultimate fallback to the store itself
                final_pricing_stores.add(store.id)
        
        # Case 3: For IGA, always use its own anchor, even if unpriced.
        else:
            if anchor:
                final_pricing_stores.add(anchor.id)
            else: # Fallback for IGA store with no group/anchor
                final_pricing_stores.add(store.id)
            
    return list(final_pricing_stores) if final_pricing_stores else requested_store_ids
