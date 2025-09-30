from products.models import Product, Price

def build_price_slots(cart, stores):
    """
    Builds the detailed 'slots' data structure required by the optimization engine.

    Args:
        cart (list): The user's shopping cart, a list of lists of product IDs.
        stores (QuerySet): A QuerySet of Store objects to consider for pricing.

    Returns:
        list: A list of lists, where each inner list contains price options for a product.
    """
    all_slots = []
    # Extract all unique product IDs from the cart for efficient querying
    product_ids = list(set(item['product_id'] for slot in cart for item in slot))

    # Fetch all relevant products and prices in fewer queries
    products = Product.objects.in_bulk(product_ids)
    prices = Price.objects.filter(
        price_record__product_id__in=product_ids,
        store__in=stores
    ).select_related('store', 'price_record', 'price_record__product__brand')

    # Group prices by product ID for efficient lookup
    prices_by_product = {}
    for price in prices:
        prod_id = price.price_record.product_id
        if prod_id not in prices_by_product:
            prices_by_product[prod_id] = []
        prices_by_product[prod_id].append(price)

    for slot in cart:
        current_slot = []
        for item in slot:
            product_id = item['product_id']
            product_obj = products.get(product_id)
            if not product_obj:
                continue

            # Get pre-fetched prices for this product
            product_prices = prices_by_product.get(product_id, [])

            for price_obj in product_prices:
                if not price_obj.price_record:
                    continue
                
                # Account for quantity
                quantity = item.get('quantity', 1)
                total_price = float(price_obj.price_record.price) * quantity

                current_slot.append({
                    "product_id": product_id,
                    "product_name": product_obj.name,
                    "brand": product_obj.brand.name if product_obj.brand else None,
                    "sizes": product_obj.sizes,
                    "store_id": price_obj.store.id,
                    "store_name": price_obj.store.store_name,
                    "price": total_price,
                    "quantity": quantity
                })
        
        if current_slot:
            all_slots.append(current_slot)
            
    return all_slots
