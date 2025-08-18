from datetime import datetime

def clean_raw_store_data_woolworths(raw_store_data: dict, company: str, timestamp: datetime) -> dict:
    """
    Cleans a raw Woolworths store data dictionary according to our standardized schema.
    """
    
    store_id = raw_store_data.get('StoreNo')
    
    cleaned_data = {
        "store_name": raw_store_data.get('Name'),
        "store_id": store_id,
        "retailer_store_id": None,
        "is_active": True,  # Assuming all discovered stores are active
        "division": raw_store_data.get('Division'),
        "email": None,
        "phone_number": raw_store_data.get('Phone'),
        "address_line_1": raw_store_data.get('AddressLine1'),
        "address_line_2": raw_store_data.get('AddressLine2'),
        "suburb": raw_store_data.get('Suburb'),
        "state": raw_store_data.get('State'),
        "postcode": raw_store_data.get('Postcode'),
        "latitude": raw_store_data.get('Latitude'),
        "longitude": raw_store_data.get('Longitude'),
        "trading_hours": raw_store_data.get('TradingHours'),
        "facilities": raw_store_data.get('Facilities'),
        "is_trading": raw_store_data.get('IsOpen'),
        "online_shop_url": None,
        "store_url": None,
        "ecommerce_url": None,
        "record_id": None,
        "status": None,
        "store_type": None,
        "site_id": None,
        
        "shopping_modes": None,
        "available_customer_service_types": None,
        "alcohol_availability": None,
    }

    if cleaned_data.get('store_name') == 'N/A' and cleaned_data.get('suburb'):
        cleaned_data['store_name'] = cleaned_data['suburb']
        
    metadata = {
        "company": company,
        "scraped_at": timestamp.isoformat()
    }

    return {
        "metadata": metadata,
        "store_data": cleaned_data
    }
