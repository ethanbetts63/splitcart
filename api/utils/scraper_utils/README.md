
# Scraper Data Cleaning Utilities

This directory contains utility functions for cleaning the raw product data scraped from different grocery store websites. Each function takes a list of raw product objects and transforms them into a standardized schema before they are passed to the normalization and database update processes.

## General Process

For each store, the cleaning process involves:
1.  Iterating through the raw product list.
2.  Extracting key information such as name, brand, price, size, and categories.
3.  Performing store-specific transformations to fit the standardized V2 schema.
4.  Wrapping the cleaned product list in a metadata dictionary that includes information about the scrape (e.g., store ID, timestamp).

## Store-Specific Cleaning Logic

### `clean_raw_data_coles.py`

-   **Product ID:** Extracted from the `id` field.
-   **URL:** Constructed from the product `id`, `name`, and `size`.
-   **Pricing:**
    -   `price_current` is taken from `pricing.now`.
    -   `price_was` is taken from `pricing.was`.
    -   `is_on_special` is determined by `pricing.onlineSpecial`.
-   **Categories:** The category path is constructed from the `onlineHeirs` object.
-   **Images:** Image URLs are constructed by prepending the base URL to the URI from `imageUris`.
-   **Tags:** A "special" tag is added if `promotionType` is "SPECIAL".
-   **Barcode:** Not available in the raw data.

### `clean_raw_data_woolworths.py`

-   **Product ID:** Extracted from the `Stockcode` field.
-   **Barcode:** Extracted from the `Barcode` field.
-   **URL:** Constructed from the `Stockcode` and `UrlFriendlyName`.
-   **Pricing:**
    -   `price_current` is taken from `Price`.
    -   `price_was` is taken from `WasPrice`.
-   **Categories:** The category path is constructed primarily from the `sap...name` fields in `AdditionalAttributes`. It falls back to the `pies...json` fields if the SAP fields are not available.
-   **Attributes:** Many detailed attributes (country of origin, ingredients, allergens, health star rating) are extracted from the nested `AdditionalAttributes` dictionary.
-   **Tags:** Tags are created from the `IsNew` flag, `lifestyleanddietarystatement`, and `ImageTag.FallbackText`.

### `clean_raw_data_aldi.py`

-   **Product ID:** Extracted from the `sku` field.
-   **URL:** Constructed from the `urlSlugText`.
-   **Pricing:**
    -   The price is converted from cents to dollars (e.g., `469` -> `4.69`).
    -   `is_on_special` is inferred from the presence of a `wasPriceDisplay`.
-   **Categories:** The category path is constructed from the `categories` list.
-   **Images:** Image URLs are extracted from the `assets` list.
-   **Tags:** Tags are extracted from the `badges` list.
-   **Barcode:** Not available in the raw data.

### `clean_raw_data_iga.py`

-   **Product ID:** Extracted from the `sku` field.
-   **Barcode:** Extracted from the `barcode` field.
-   **URL:** Not available in the raw data.
-   **Pricing:**
    -   `is_on_special` is determined by the presence of a `wasWholePrice` key.
    -   The logic handles different fields for regular price (`wholePrice`) and special price (`tprPrice`).
-   **Categories:** The category path is constructed from the `categoryBreadcrumb` of the last category in the `categories` list.
-   **Country of Origin:** This was previously extracted from the description but has been removed to simplify the cleaner. It is now always `None`.
-   **Images:** Image URLs are extracted from the `image` dictionary.
