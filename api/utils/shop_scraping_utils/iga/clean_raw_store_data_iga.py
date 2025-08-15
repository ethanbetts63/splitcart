from datetime import datetime

def clean_raw_store_data_iga(raw_store_data: dict, company: str, timestamp: datetime) -> dict:
    """
    Cleans a raw IGA store data dictionary according to our standardized schema.
    """
    
    store_id = raw_store_data.get('storeId')
    
    cleaned_data = {
        "name": raw_store_data.get('storeName'),
        "store_id": store_id,
        "retailer_store_id": raw_store_data.get('retailerStoreId'),
        "is_active": True,  # Assuming all discovered stores are active
        "division": None,  # IGA doesn't seem to have divisions in the same way as Coles/Woolies
        "email": raw_store_data.get('email'),
        "phone_number": raw_store_data.get('phone'),
        "address_line_1": raw_store_data.get('address'),
        "address_line_2": None,
        "suburb": raw_store_data.get('suburb'),
        "state": raw_store_data.get('state'),
        "postcode": raw_store_data.get('postcode'),
        "latitude": raw_store_data.get('latitude'),
        "longitude": raw_store_data.get('longitude'),
        "trading_hours": raw_store_data.get('hours'),
        "facilities": None,
        "is_trading": None, # Not available in IGA data
        "online_shop_url": raw_store_data.get('onlineShopUrl'),
        "store_url": raw_store_data.get('storeUrl'),
        "ecommerce_url": raw_store_data.get('ecommerceUrl'),
        "record_id": raw_store_data.get('id'),
        "status": raw_store_data.get('status'),
        "store_type": raw_store_data.get('type'),
        "site_id": raw_store_data.get('siteId'),
        
        "shopping_modes": raw_store_data.get('shoppingModes'),
        "available_customer_service_types": None,
        "alcohol_availability": None,
    }

    metadata = {
        "company": company,
        "scraped_at": timestamp.isoformat()
    }

    return {
        "metadata": metadata,
        "store_data": cleaned_data
    }
