from collections import defaultdict
from django.db.models import Q, Min, Case, When
from products.models import Product, Price, ProductPriceSummary

def get_bargain_first_ordering(anchor_store_ids, primary_category_slugs, limit=20):
    """
    Gets a hybrid list of product IDs. It prioritizes bargain products
    and fills the remaining slots with the best unit-price products.
    """
    bargain_map = {}

    if not anchor_store_ids:
        return [], {}

    # --- Step 1: Identify potential candidates ---
    candidate_product_ids = list(ProductPriceSummary.objects.filter(
        product__category__primary_category__slug__in=primary_category_slugs,
        product__prices__store__id__in=anchor_store_ids
    ).distinct().order_by('-best_possible_discount').values_list('product_id', flat=True)[:200])

    if not candidate_product_ids:
        # Fallback to simple unit price ordering if no candidates found
        fallback_queryset = Product.objects.filter(
            category__primary_category__slug__in=primary_category_slugs,
            prices__store__id__in=anchor_store_ids
        ).distinct().annotate(
            min_unit_price=Min('prices__unit_price', filter=Q(prices__store__id__in=anchor_store_ids))
        ).order_by('min_unit_price')
        return list(fallback_queryset.values_list('pk', flat=True)[:limit]), {}

    # --- Step 2: Calculate "real" bargains for the candidates ---
    live_prices = Price.objects.filter(
        product_id__in=candidate_product_ids,
        store_id__in=anchor_store_ids
    ).select_related('store__company')

    products_with_prices = defaultdict(list)
    for price in live_prices:
        products_with_prices[price.product_id].append(price)

    calculated_bargains = []
    for product_id, prices in products_with_prices.items():
        if len(prices) < 2:
            continue
        
        company_ids = {p.store.company_id for p in prices}
        is_iga = any(p.store.company.name.lower() == 'iga' for p in prices)
        iga_stores = {p.store_id for p in prices if p.store.company.name.lower() == 'iga'}
        if len(company_ids) < 2 and (not is_iga or len(iga_stores) < 2):
            continue

        min_price_obj = min(prices, key=lambda p: p.price)
        max_price_obj = max(prices, key=lambda p: p.price)

        if min_price_obj.price == max_price_obj.price:
            continue

        actual_discount = int(((max_price_obj.price - min_price_obj.price) / max_price_obj.price) * 100)
        if not (5 <= actual_discount <= 70):
            continue
        
        calculated_bargains.append({
            'product_id': product_id, 'discount': actual_discount,
            'cheaper_store_name': min_price_obj.store.store_name,
            'cheaper_company_name': min_price_obj.store.company.name,
        })
    
    sorted_bargains = sorted(calculated_bargains, key=lambda b: b['discount'], reverse=True)
    
    bargain_map = {b['product_id']: b for b in sorted_bargains}
    confirmed_bargain_ids = [b['product_id'] for b in sorted_bargains]

    # --- Step 3: Get Filler Products if needed ---
    num_bargains = len(confirmed_bargain_ids)
    filler_product_ids = []
    if num_bargains < limit:
        num_to_fill = limit - num_bargains
        
        filler_queryset = Product.objects.filter(
            prices__store__id__in=anchor_store_ids,
            category__primary_category__slug__in=primary_category_slugs
        ).exclude(
            pk__in=confirmed_bargain_ids
        ).annotate(
            min_unit_price=Min('prices__unit_price', filter=Q(prices__store__id__in=anchor_store_ids))
        ).order_by('min_unit_price')
        
        filler_product_ids = list(filler_queryset.values_list('pk', flat=True)[:num_to_fill])

    # --- Step 4: Combine ---
    final_product_ids = confirmed_bargain_ids + filler_product_ids

    return final_product_ids, bargain_map
