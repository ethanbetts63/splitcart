from companies.models import Company, Store, Division

def get_or_create_store(company_obj: Company, division_obj: Division, store_id: str, store_data: dict) -> tuple[Store, bool]:
    """
    Finds or creates a single Store instance based on its store_id and company.
    Updates store details if it already exists.

    Args:
        company_obj: The Company object this store belongs to.
        division_obj: The Division object this store belongs to (can be None).
        store_id: The unique identifier for the store.
        store_data: A dictionary containing store info to create or update.

    Returns:
        A tuple containing the Store object and a boolean indicating if it was created.
    """
    defaults = {
        'name': store_data.get('store_name', 'N/A'),
        'division': division_obj,
        'phone_number': store_data.get('phone_number', ''),
        'address_line_1': store_data.get('address_line_1', ''),
        'address_line_2': store_data.get('address_line_2', ''),
        'suburb': store_data.get('suburb', ''),
        'state': store_data.get('state', ''),
        'postcode': store_data.get('postcode', ''),
        'latitude': store_data.get('latitude'),
        'longitude': store_data.get('longitude'),
        'trading_hours': store_data.get('trading_hours'),
        'facilities': store_data.get('facilities'),
        'is_trading': store_data.get('is_trading'),
        'retailer_store_id': store_data.get('retailer_store_id', ''),
        'email': store_data.get('email', ''),
        'online_shop_url': store_data.get('online_shop_url', ''),
        'store_url': store_data.get('store_url', ''),
        'ecommerce_url': store_data.get('ecommerce_url', ''),
        'record_id': store_data.get('record_id', ''),
        'status': store_data.get('status', ''),
        'store_type': store_data.get('store_type', ''),
        'site_id': store_data.get('site_id', ''),
        
        'shopping_modes': store_data.get('shopping_modes'),
        'available_customer_service_types': store_data.get('available_customer_service_types'),
        'alcohol_availability': store_data.get('alcohol_availability'),
    }

    # Remove keys where value is None, to avoid overwriting existing data with nulls
    # for fields that can be null (like lat/long, json fields)
    update_defaults = {k: v for k, v in defaults.items() if v is not None}

    store_obj, created = Store.objects.update_or_create(
        store_id=store_id,
        company=company_obj,
        defaults=update_defaults
    )
    return store_obj, created
