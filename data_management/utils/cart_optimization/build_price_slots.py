from products.models import Product, Price

def build_price_slots(cart, stores):
    print("Inside build_price_slots")
    all_slots = []
    product_ids = list(set(item['product_id'] for slot in cart for item in slot))
    print(f"Product IDs: {product_ids}")

    print("Fetching products with in_bulk")
    products = Product.objects.in_bulk(product_ids)
    print("Finished fetching products")

    print("Fetching prices")
    prices = Price.objects.filter(
        price_record__product_id__in=product_ids,
        store__in=stores
    ).select_related('store', 'price_record', 'price_record__product__brand')
    print("Finished fetching prices")

    prices_by_product = {}
    for price in prices:
        prod_id = price.price_record.product_id
        if prod_id not in prices_by_product:
            prices_by_product[prod_id] = []
        prices_by_product[prod_id].append(price)

    print("Looping through cart slots")
    for i, slot in enumerate(cart):
        current_slot = []
        for j, item in enumerate(slot):
            product_id = item['product_id']
            product_obj = products.get(product_id)
            if not product_obj:
                continue

            product_prices = prices_by_product.get(product_id, [])
            for k, price_obj in enumerate(product_prices):
                if not price_obj.price_record:
                    continue
                
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
            
    print("Finished build_price_slots")
    return all_slots
