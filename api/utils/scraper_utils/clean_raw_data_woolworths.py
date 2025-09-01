import json
from datetime import datetime
from api.utils.product_normalizer import ProductNormalizer
from .wrap_cleaned_products import wrap_cleaned_products

def clean_raw_data_woolworths(raw_product_list: list, company: str, store_id: str, store_name: str, state: str, timestamp: datetime) -> dict:
    """
    Cleans a list of raw Woolworths product data according to the V2 schema and
    wraps it in a dictionary containing metadata about the scrape.
    """
    cleaned_products = []
    if not raw_product_list:
        raw_product_list = []

    for product in raw_product_list:
        if not product:
            continue

        attrs = product.get('AdditionalAttributes', {}) or {}
        rating_info = product.get('Rating', {}) or {}
        stockcode = product.get('Stockcode')
        url_slug = product.get('UrlFriendlyName')

        product_url = f"https://www.woolworths.com.au/shop/productdetails/{stockcode}/{url_slug}" if stockcode and url_slug else None

        tags = []
        if product.get('IsNew'):
            tags.append('new')
        if attrs.get('lifestyleanddietarystatement'):
            tags.extend([tag.strip() for tag in attrs['lifestyleanddietarystatement'].split(',')])
        if product.get('ImageTag', {}).get('FallbackText'):
            tags.append(product['ImageTag']['FallbackText'])
        
        category_path = []
        attrs = product.get('AdditionalAttributes', {}) or {}
        
        dept = attrs.get('sapdepartmentname')
        cat = attrs.get('sapcategoryname')
        sub_cat = attrs.get('sapsubcategoryname')
        segment = attrs.get('sapsegmentname')

        if dept:
            category_path.append(dept)
        if cat:
            category_path.extend([part.strip() for part in cat.split('/')])
        if sub_cat:
            category_path.append(sub_cat)
        if segment:
            category_path.append(segment)

        if not category_path:
            try:
                pies_dept = json.loads(attrs.get('piesdepartmentnamesjson', '[]'))
                pies_cat = json.loads(attrs.get('piescategorynamesjson', '[]'))
                pies_sub_cat = json.loads(attrs.get('piessubcategorynamesjson', '[]'))
                
                if pies_dept:
                    category_path.append(pies_dept[0])
                if pies_cat:
                    category_path.append(pies_cat[0])
                if pies_sub_cat:
                    category_path.append(pies_sub_cat[0])
            except (json.JSONDecodeError, TypeError, IndexError):
                pass
        
        category_path = [part.strip().title() for part in category_path if part]

        clean_product = {
            "product_id_store": str(stockcode) if stockcode else None,
            "barcode": product.get('Barcode'), # Pass raw barcode to be cleaned by normalizer
            "name": product.get('Name'),
            "brand": product.get('Brand'),
            "description_short": product.get('Description'),
            "description_long": attrs.get('description'),
            "url": product_url,
            "image_url_main": product.get('LargeImageFile'),
            "image_urls_all": [product.get(f'{size}ImageFile') for size in ['Small', 'Medium', 'Large'] if product.get(f'{size}ImageFile')],
            "price_current": product.get('Price'),
            "price_was": product.get('WasPrice'),
            "is_on_special": product.get('IsOnSpecial', False),
            "price_save_amount": product.get('SavingsAmount'),
            "promotion_type": product.get('CentreTag', {}).get('TagType'),
            "price_unit": product.get('CupPrice'),
            "unit_of_measure": product.get('CupMeasure'),
            "unit_price_string": product.get('CupString'),
            "is_available": product.get('IsAvailable', False),
            "stock_level": "In Stock" if product.get('IsInStock') else "Out of Stock",
            "purchase_limit": product.get('SupplyLimit'),
            "package_size": product.get('PackageSize'),
            "country_of_origin": attrs.get('countryoforigin'),
            "health_star_rating": float(attrs['healthstarrating']) if attrs.get('healthstarrating') else None,
            "ingredients": attrs.get('ingredients'),
            "allergens_may_be_present": [allergen.strip() for allergen in attrs['allergenmaybepresent'].split(',')] if attrs.get('allergenmaybepresent') else [],
            "category_path": category_path,
            "tags": list(set(tags)),
            "rating_average": rating_info.get('Average'),
            "rating_count": rating_info.get('ReviewCount'),
        }
        cleaned_products.append(clean_product)

    # --- Final generic cleaning and normalization ---
    final_products = []
    for p in cleaned_products:
        normalizer = ProductNormalizer(p)
        p['sizes'] = normalizer.get_raw_sizes()
        p['normalized_name_brand_size'] = normalizer.get_normalized_string()
        p['barcode'] = normalizer.get_cleaned_barcode()

        # Add normalized price key
        price_normalizer = PriceNormalizer()
        p['normalized_key'] = price_normalizer.get_normalized_key(
            product_id=p.get('product_id_store'), 
            store_id=store_id, 
            price=p.get('price_current'), 
            date=timestamp.date().isoformat()
        )
        p['scraped_date'] = timestamp.date().isoformat()

        final_products.append(p)
    
    return wrap_cleaned_products(
        products=final_products,
        company=company,
        store_name=store_name,
        store_id=store_id,
        state=state,
        timestamp=timestamp
    )