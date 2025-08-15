from datetime import datetime

def clean_raw_store_data_aldi(raw_store_data: dict, company: str, timestamp: datetime) -> dict:
    """
    Cleans a raw ALDI store data dictionary according to our standardized schema.
    """
    
    # Using field names from companies/models/store.py comments for ALDI
    store_id = raw_store_data.get('id')
    address_data = raw_store_data.get('address', {})

    cleaned_data = {
        "name": raw_store_data.get('name'),
        "store_id": store_id,
        "retailer_store_id": None,
        "is_active": True,
        "division": None,
        "email": None,
        "phone_number": raw_store_data.get('publicPhoneNumber'),
        "address_line_1": address_data.get('address1'),
        "address_line_2": address_data.get('address2'),
        "suburb": address_data.get('city'),
        "state": address_data.get('regionName'),
        "postcode": address_data.get('zipCode'),
        "latitude": address_data.get('latitude'),
        "longitude": address_data.get('longitude'),
        "trading_hours": None,
        "facilities": raw_store_data.get('facilities'),
        "is_trading": raw_store_data.get('isOpenNow'),
        "online_shop_url": None,
        "store_url": None,
        "ecommerce_url": None,
        "record_id": None,
        "status": None,
        "store_type": None,
        "site_id": None,
        
        "shopping_modes": None,
        "available_customer_service_types": raw_store_data.get('availableCustomerServiceTypes'),
        "alcohol_availability": raw_store_data.get('alcoholAvailability'),
    }

    metadata = {
        "company": company,
        "scraped_at": timestamp.isoformat()
    }

    return {
        "metadata": metadata,
        "store_data": cleaned_data
    }
