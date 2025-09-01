"""
This file contains the field mapping dictionaries for each store.
It translates the raw field names from each store's API into a standardized
internal schema. This allows the data cleaners to be more declarative and
easier to maintain.

Dot notation is used to access nested fields in the raw JSON data.
"""


COLES_FIELD_MAP = {
    # Standardized Field : Raw Field from Coles API
    "product_id_store": "id",
    "name": "name",
    "brand": "brand",
    "barcode": "barcode", # Note: Not always present in Coles data
    "description": "description",
    "package_size": "size",
    "image_url": "imageUris.0.uri", # Takes the first image URI
    "url": None, # Not directly available in the product list API
    "category_path": "onlineHeirs.0", # Takes the first category path

    # Price related fields
    "price_current": "pricing.now",
    "price_was": "pricing.was",
    "per_unit_price_string": "pricing.comparable",
    "per_unit_price_value": "pricing.unit.price",
    "per_unit_price_measure": "pricing.unit.ofMeasureUnits",

    # Ratings and Health Stars
    "average_rating": None,
    "review_count": None,
    "health_star_rating": None,
}

WOOLWORTHS_FIELD_MAP = {
    # Standardized Field : Raw Field from Woolworths API
    "product_id_store": "Stockcode",
    "name": "Name",
    "brand": "Brand",
    "barcode": "Barcode",
    "description": "Description",
    "ingredients": "AdditionalAttributes.ingredients",
    "allergens": "AdditionalAttributes.allergystatement",
    "country_of_origin": "AdditionalAttributes.countryoforigin",
    "package_size": "PackageSize",
    "image_url": "LargeImageFile",
    "url": "UrlFriendlyName", # This is a partial URL slug
    "category_path": "AdditionalAttributes.piesdepartmentnamesjson", # This is a JSON string

    # Price related fields
    "price_current": "Price",
    "price_was": "WasPrice",
    "per_unit_price_string": "CupString",
    "per_unit_price_value": "InstoreCupPrice",
    "per_unit_price_measure": "CupMeasure",

    # Ratings and Health Stars
    "average_rating": "Rating.Average",
    "review_count": "Rating.ReviewCount",
    "health_star_rating": "AdditionalAttributes.healthstarrating",
}

IGA_FIELD_MAP = {
    # Standardized Field : Raw Field from IGA API
    "product_id_store": "productId",
    "name": "name",
    "brand": "brand",
    "barcode": "barcode",
    "description": "description",
    "ingredients": None, # Not consistently available
    "allergens": None, # Not consistently available
    "country_of_origin": None, # Not consistently available
    "package_size": "unitOfSize.size", # e.g., 200
    "image_url": "image.default",
    "url": None,
    "category_path": "defaultCategory.0.categoryBreadcrumb", # e.g., "Grocery/Drinks/Long Life Milk"

    # Price related fields
    "price_current": "priceNumeric",
    "price_was": None, # Not available in the provided IGA data
    "per_unit_price_string": "pricePerUnit",
    "per_unit_price_value": None,
    "per_unit_price_measure": None,

    # Ratings and Health Stars
    "average_rating": None,
    "review_count": None,
    "health_star_rating": None,
}

ALDI_FIELD_MAP = {
    # Standardized Field : Raw Field from ALDI API
    "product_id_store": "sku",
    "name": "name",
    "brand": "brandName",
    "barcode": None, # Not available in ALDI product list API
    "description": None, # Not available in ALDI product list API
    "ingredients": None, # Not available in ALDI product list API
    "allergens": None, # Not available in ALDI product list API
    "country_of_origin": None, # Not available in ALDI product list API
    "package_size": "sellingSize", # e.g., "280 g"
    "image_url": "assets.0.url", # Takes the first image URL
    "url": "urlSlugText", # This is a partial URL slug
    "category_path": "categories", # This is a list of category dicts

    # Price related fields
    "price_current": "price.amount", # Note: in cents, needs division by 100
    "price_was": "price.wasPriceDisplay", # Note: seems to be a string like "$x.xx"
    "per_unit_price_string": "price.comparisonDisplay",
    "per_unit_price_value": "price.comparison", # Note: in cents
    "per_unit_price_measure": None, # Must be parsed from comparisonDisplay

    # Ratings and Health Stars
    "average_rating": None,
    "review_count": None,
    "health_star_rating": None,
}
