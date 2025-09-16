
from products.models import Product, Price
from companies.models import Category

class StoreProductLister:
    """
    Builds a list of product dictionaries for a given store, including price history.
    This class is a generator that processes products in chunks.
    """

    def __init__(self, store):
        self.store = store
        self.category_path_map_cache = {}

    def get_products(self):
        """
        A generator that yields a dictionary for each product in the store.
        """
        product_ids = list(Price.objects.filter(store=self.store).values_list('product_id', flat=True).distinct())

        chunk_size = 500
        for i in range(0, len(product_ids), chunk_size):
            chunk_ids = product_ids[i:i + chunk_size]

            products_in_chunk = Product.objects.filter(id__in=chunk_ids).prefetch_related('category')
            prices_in_chunk = Price.objects.filter(store=self.store, product_id__in=chunk_ids).order_by('-scraped_at')

            prices_by_product = {}
            for price in prices_in_chunk:
                if price.product_id not in prices_by_product:
                    prices_by_product[price.product_id] = []
                prices_by_product[price.product_id].append(price)

            all_category_ids = {cat.id for p in products_in_chunk for cat in p.category.all()}
            self._build_category_path_map(list(all_category_ids))

            for product in products_in_chunk:
                yield self._build_product_dict(product, prices_by_product.get(product.id, []))

    def _build_category_path_map(self, category_ids):
        """
        Builds a map of category IDs to their full hierarchical paths efficiently.
        """
        if not category_ids:
            return

        # Reduce the category_ids to only those not already in the cache
        ids_to_fetch = [id for id in category_ids if id not in self.category_path_map_cache]
        if not ids_to_fetch:
            return

        all_parents_map = {c['id']: {'name': c['name'], 'parent_id': c['parents__id']} for c in Category.objects.values('id', 'name', 'parents__id')}

        for cat_id in ids_to_fetch:
            path = []
            current_id = cat_id
            depth = 0
            max_depth = 20

            while current_id and depth < max_depth:
                category_info = all_parents_map.get(current_id)
                if not category_info:
                    break
                
                path.insert(0, category_info['name'])
                current_id = category_info['parent_id']
                depth += 1
            
            self.category_path_map_cache[cat_id] = path

    def _build_product_dict(self, product, prices):
        """
        Builds a dictionary for a single product.
        """
        price_history = []
        for price in prices:
            price_data = {
                'sku': price.sku,
                'price': str(price.price),
                'was_price': str(price.was_price) if price.was_price else None,
                'unit_price': str(price.unit_price) if price.unit_price else None,
                'unit_of_measure': price.unit_of_measure,
                'is_on_special': price.is_on_special,
                'is_available': price.is_available,
                'scraped_at': price.scraped_at.isoformat(),
                'url': product.url
            }
            cleaned_price_data = {k: v for k, v in price_data.items() if v is not None}
            price_history.append(cleaned_price_data)

        category_paths = [self.category_path_map_cache.get(cat.id) for cat in product.category.all() if self.category_path_map_cache.get(cat.id)]

        product_data = {
            'name': product.name,
            'brand': product.brand.name if product.brand else None,
            'sizes': product.sizes,
            'description': product.description,
            'image_url': product.image_url,
            'country_of_origin': product.country_of_origin,
            'allergens': product.allergens,
            'ingredients': product.ingredients,
            'barcode': product.barcode,
            'normalized_name_brand_size': product.normalized_name_brand_size,
            'price_history': price_history,
            'category_paths': category_paths
        }

        return {k: v for k, v in product_data.items() if v is not None and v != "" and v != []}
