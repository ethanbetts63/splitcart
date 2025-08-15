from datetime import datetime

def clean_raw_store_data_coles(raw_store_data: dict, company: str, timestamp: datetime) -> dict:
    """
    Cleans a raw Coles store data dictionary according to our standardized schema.
    """
    
    store_id = raw_store_data.get('id')
    print(store_id)
    address = raw_store_data.get('address', {})
    position = raw_store_data.get('position', {})
    brand = raw_store_data.get('brand', {})

    cleaned_data = {
        "name": raw_store_data.get('name'),
        "store_id": store_id,
        "retailer_store_id": None,
        "is_active": True,  # Assuming all discovered stores are active
        "division": brand.get('name'),
        "email": None,
        "phone_number": raw_store_data.get('phone'),
        "address_line_1": address.get('addressLine'),
        "address_line_2": None,
        "suburb": address.get('suburb'),
        "state": address.get('state'),
        "postcode": address.get('postcode'),
        "latitude": position.get('latitude'),
        "longitude": position.get('longitude'),
        "trading_hours": None,
        "facilities": None,
        "is_trading": raw_store_data.get('isTrading'),
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

    metadata = {
        "company": company,
        "brand": brand.get('id'),
        "scraped_at": timestamp.isoformat()
    }

    return {
        "metadata": metadata,
        "store_data": cleaned_data
    }
