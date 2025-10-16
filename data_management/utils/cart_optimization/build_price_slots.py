from products.models import Product, Price

def build_price_slots(cart, stores):    
    # Step 1: Gather all unique product IDs from the entire cart (originals and substitutes).
    all_slots = []
    product_ids = list(set(item['product_id'] for slot in cart for item in slot))

    # Step 2: Fetch all relevant product and price data from the database in bulk to minimize queries.
    products = Product.objects.in_bulk(product_ids)
    prices = Price.objects.filter(
        price_record__product_id__in=product_ids,
        store__in=stores
    ).select_related('store', 'price_record', 'price_record__product__brand')

    # Step 3: Organize the fetched prices into a dictionary for quick lookups by product ID.
    prices_by_product = {}
    for price in prices:
        prod_id = price.price_record.product_id
        if prod_id not in prices_by_product:
            prices_by_product[prod_id] = []
        prices_by_product[prod_id].append(price)

    # Step 4: Process each slot from the original cart structure.
    for i, slot in enumerate(cart):
        current_slot = []
        
        if not slot:
            print("  - Input slot is empty.")
            if current_slot:
              all_slots.append(current_slot)
            continue

        # Step 5: For each product within the slot (e.g., an original item and its substitutes), find its prices.
        for j, item in enumerate(slot):
            product_id = item['product_id']
            
            product_obj = products.get(product_id)
            if not product_obj:
                print(f"    - WARNING: Product object not found in bulk fetch for ID {product_id}. Skipping.")
                continue

            # Step 6: Look up the prices for the current product ID.
            product_prices = prices_by_product.get(product_id, [])
            if not product_prices:
                print(f"    - No prices found for product ID {product_id} in the selected stores.")

            # Step 7: Create the detailed 'option' dictionaries for each available price.
            for k, price_obj in enumerate(product_prices):
                if not price_obj.price_record:
                    continue
                
                quantity = item.get('quantity', 1)
                unit_price = float(price_obj.price_record.price)
                total_price = unit_price * quantity

                # Find the correct image_url from the product's image_url_pairs
                company_name = price_obj.store.company.name
                image_urls_by_company = {k.lower(): v for k, v in product_obj.image_url_pairs}
                company_name_lower = company_name.lower()
                image_url = image_urls_by_company.get(company_name_lower)

                # Construct the store address
                address_parts = [
                    price_obj.store.address_line_1,
                    price_obj.store.suburb,
                    price_obj.store.state,
                    price_obj.store.postcode
                ]
                store_address = ", ".join(part for part in address_parts if part)

                current_slot.append({
                    "product_id": product_id,
                    "product_name": product_obj.name,
                    "brand": product_obj.brand.name if product_obj.brand else None,
                    "size": product_obj.size,
                    "store_id": price_obj.store.id,
                    "store_name": price_obj.store.store_name,
                    "company_name": company_name,
                    "store_address": store_address,
                    "price": total_price,
                    "unit_price": unit_price,
                    "quantity": quantity,
                    "image_url": image_url
                })
        
        # Step 8: If, after checking all products in a slot, no price options were found, the slot is currently dropped.
        if not current_slot:
            print(f"  - WARNING: No options generated for Slot {i+1}. This slot will be dropped.")

        if current_slot:
            all_slots.append(current_slot)
            
    return all_slots
