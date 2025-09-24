"""
This file contains the field mapping dictionaries for each store.
It translates the raw field names from each store's data_management into a standardized
internal schema. This allows the data cleaners to be more declarative and
easier to maintain.

Dot notation is used to access nested fields in the raw JSON data.
"""

# --- Standardized Internal Fields Schema ---
# {
#     "sku": str,
#     "name": str,
#     "brand": str,
#     "barcode": str,
#     "description": str,
#     "ingredients": str,
#     "allergens": str,
#     "country_of_origin": str,
#     "size": str,
#     "image_url": str,
#     "url": str,
#     "category_path": list,
#
#     # Price related fields
#     "price_current": float,
#     "price_was": float,
#     "per_unit_price_string": str,
#     "per_unit_price_value": float,
#     "per_unit_price_measure": str,
#
#     # Ratings and Health Stars
#     "average_user_rating": float,
#     "rating_count": int,
#     "health_star_rating": float,
#
#     # The following are calculated by the BaseDataCleaner, not mapped directly
#     # "is_on_special": bool,
#     # "price_save_amount": float,
#     # "sizes": list,
#     # "normalized_name_brand_size": str,
#     # "normalized_key": str,
#     # "scraped_date": str,
# }
# ------------------------------------------

COLES_FIELD_MAP = {
    "sku": "id",
    "name": "name",
    "brand": "brand",
    "barcode": "barcode",
    "description": "description",
    "size": "size",
    "image_url": "imageUris.0.uri",
    "url": None,
    "category_path": "onlineHeirs",
    "price_current": "pricing.now",
    "price_was": "pricing.was",
    "per_unit_price_string": "pricing.comparable",
    "per_unit_price_value": "pricing.unit.price",
    "per_unit_price_measure": "pricing.unit.ofMeasureUnits",
    "average_user_rating": None,
    "rating_count": None,
    "health_star_rating": None,
    "is_available": "availability",
}

WOOLWORTHS_FIELD_MAP = {
    "sku": "Stockcode",
    "name": "Name",
    "brand": "Brand",
    "barcode": "Barcode",
    "description": "Description",
    "ingredients": "AdditionalAttributes.ingredients",
    "allergens": "AdditionalAttributes.allergystatement",
    "country_of_origin": "AdditionalAttributes.countryoforigin",
    "size": "PackageSize",
    "image_url": "LargeImageFile",
    "url": "UrlFriendlyName",
    "category_path": "AdditionalAttributes.piesdepartmentnamesjson",
    "price_current": "Price",
    "price_was": "WasPrice",
    "per_unit_price_string": "CupString",
    "per_unit_price_value": "InstoreCupPrice",
    "per_unit_price_measure": "CupMeasure",
    "average_user_rating": "Rating.Average",
    "rating_count": "Rating.ReviewCount",
    "health_star_rating": "AdditionalAttributes.healthstarrating",
}

IGA_FIELD_MAP = {
    "sku": "productId",
    "name": "name",
    "brand": "brand",
    "barcode": "barcode",
    "description": "description",
    "ingredients": None,
    "allergens": None,
    "country_of_origin": None,
    "size": "unitOfSize.size",
    "image_url": "image.default",
    "url": None,
    "category_path": "defaultCategory.0.categoryBreadcrumb",
    "price_current": "priceNumeric",
    "price_was": None,
    "per_unit_price_string": "pricePerUnit",
    "per_unit_price_value": None,
    "per_unit_price_measure": None,
    "average_user_rating": None,
    "rating_count": None,
    "health_star_rating": None,
}

ALDI_FIELD_MAP = {
    "sku": "sku",
    "name": "name",
    "brand": "brandName",
    "barcode": None,
    "description": None,
    "ingredients": None,
    "allergens": None,
    "country_of_origin": None,
    "size": "sellingSize",
    "image_url": "assets.0.url",
    "url": "urlSlugText",
    "category_path": "categories",
    "price_current": "price.amount",
    "price_was": "price.wasPriceDisplay",
    "per_unit_price_string": "price.comparisonDisplay",
    "per_unit_price_value": "price.comparison",
    "per_unit_price_measure": None,
    "average_user_rating": None,
    "rating_count": None,
    "health_star_rating": None,
}