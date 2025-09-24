"""
This file contains the field mapping dictionaries for store data.
It translates the raw field names from each store's data_management into a standardized
internal schema.
"""

# --- Standardized Internal Fields Schema for Stores ---
# {
#     "store_id": str,
#     "retailer_store_id": str,
#     "store_name": str,
#     "is_active": bool,
#     "division": str,
#     "email": str,
#     "phone_number": str,
#     "address_line_1": str,
#     "address_line_2": str,
#     "suburb": str,
#     "state": str,
#     "postcode": str,
#     "latitude": float,
#     "longitude": float,
#     "trading_hours": str, # Or could be a structured dict
#     "facilities": list,
#     "is_trading": bool,
#     "online_shop_url": str,
#     "store_url": str,
#     "ecommerce_url": str,
#     "record_id": str,
#     "status": str,
#     "store_type": str,
#     "site_id": str,
#     "shopping_modes": list,
#     "available_customer_service_types": list,
#     "alcohol_availability": str,
# }
# ----------------------------------------------------

# For the data_management at https://www.woolworths.com.au/apis/ui/StoreLocator/Stores
WOOLWORTHS_STORE_MAP_API1 = {
    "store_id": "StoreNo",
    "store_name": "Name",
    "division": "Division",
    "phone_number": "Phone",
    "address_line_1": "AddressLine1",
    "address_line_2": "AddressLine2",
    "suburb": "Suburb",
    "state": "State",
    "postcode": "Postcode",
    "latitude": "Latitude",
    "longitude": "Longitude",
    "trading_hours": "TradingHours",
    "facilities": "Facilities",
    "is_trading": "IsOpen",
}

# For the data_management at https://www.woolworths.com.au/data_management/v3/ui/fulfilment/stores
WOOLWORTHS_STORE_MAP_API2 = {
    "store_id": "FulfilmentStoreId",
    "retailer_store_id": "FulfilmentStoreId",
    "store_name": "Description",
    "address_line_1": "Street1",
    "address_line_2": "Street2",
    "suburb": "Suburb",
    "postcode": "Postcode",
    "shopping_modes": "FulfilmentDeliveryMethods",
}

ALDI_STORE_MAP = {
    "store_id": "id",
    "store_name": "name",
    "phone_number": "publicPhoneNumber",
    "address_line_1": "address.address1",
    "address_line_2": "address.address2",
    "suburb": "address.city",
    "state": "address.regionName",
    "postcode": "address.zipCode",
    "latitude": "address.latitude",
    "longitude": "address.longitude",
    "facilities": "facilities",
    "is_trading": "isOpenNow",
    "available_customer_service_types": "availableCustomerServiceTypes",
    "alcohol_availability": "alcoholAvailability",
}

COLES_STORE_MAP = {
    "store_id": "id",
    "store_name": "name",
    "phone_number": "phone",
    "address_line_1": "address.addressLine",
    "suburb": "address.suburb",
    "state": "address.state",
    "postcode": "address.postcode",
    "latitude": "position.latitude",
    "longitude": "position.longitude",
    "is_trading": "isTrading",
}

IGA_STORE_MAP = {
    "store_id": "storeId",
    "retailer_store_id": "tag",
    "store_name": "storeName",
    "email": "email",
    "phone_number": "phone",
    "address_line_1": "address",
    "suburb": "suburb",
    "state": "state",
    "postcode": "postcode",
    "latitude": "latitude",
    "longitude": "longitude",
    "trading_hours": "hours",
    "online_shop_url": "onlineShopUrl",
    "store_url": "storeUrl",
    "ecommerce_url": "ecommerceUrl",
    "record_id": "id",
    "status": "status",
    "store_type": "type",
    "site_id": "siteId",
    "shopping_modes": "shoppingModes",
}