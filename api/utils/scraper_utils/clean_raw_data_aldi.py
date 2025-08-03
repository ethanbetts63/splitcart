import re
from datetime import datetime

def clean_raw_data_aldi(raw_product_list: list, company: str, store: str, category_slug: str, page_num: int, timestamp: datetime) -> dict:
    """
    Cleans a list of raw ALDI product data from its API and wraps it in a 
    dictionary containing metadata about the scrape.
    """
    cleaned_products = []
    
    for product in raw_product_list:
        price_info = product.get('price', {})
        
        current_price = price_info.get('amount')
        if current_price is not None:
            current_price /= 100.0

        comparison_price = price_info.get('comparison')
        if comparison_price is not None:
            comparison_price /= 100.0
            
        unit_of_measure = None
        comparison_display = price_info.get('comparisonDisplay')
        if comparison_display:
            match = re.search(r'/\s*(.*)', comparison_display)
            if match:
                unit_of_measure = match.group(1).strip()

        category_hierarchy = product.get('categories', [])
        departments = [category_hierarchy[0]] if len(category_hierarchy) > 0 else []
        categories = [category_hierarchy[1]] if len(category_hierarchy) > 1 else []
        subcategories = [category_hierarchy[2]] if len(category_hierarchy) > 2 else []

        product_url = f"https://www.aldi.com.au/product/{product.get('urlSlugText', '')}" if product.get('urlSlugText') else None

        clean_product = {
            'name': product.get('name'),
            'brand': product.get('brandName'),
            'barcode': None,
            'stockcode': product.get('sku'),
            'package_size': price_info.get('sellingSize'),
            'price': current_price,
            'was_price': price_info.get('wasPriceDisplay'),
            'is_on_special': price_info.get('wasPriceDisplay') is not None,
            'is_available': not product.get('notForSale', True),
            'unit_price': comparison_price,
            'unit_of_measure': unit_of_measure,
            'url': product_url,
            'departments': [{'name': dept.get('name'), 'id': dept.get('id')} for dept in departments],
            'categories': [{'name': cat.get('name'), 'id': cat.get('id')} for cat in categories],
            'subcategories': [{'name': sub.get('name'), 'id': sub.get('id')} for sub in subcategories]
        }
        cleaned_products.append(clean_product)
    
    return {
        "metadata": {
            "company": company,
            "store": store,
            "category": category_slug,
            "page_number": page_num,
            "scraped_at": timestamp.isoformat()
        },
        "products": cleaned_products
    }
