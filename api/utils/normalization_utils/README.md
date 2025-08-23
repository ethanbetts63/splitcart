# Normalization Utilities

This directory contains a suite of utility functions responsible for cleaning, extracting, and standardizing product data, primarily for the purpose of creating a robust de-duplication key (`normalized_name_brand_size`) and extracting structured size information.

## Importance

The data scraped from various grocery store websites is highly inconsistent in its format, especially regarding product names, brands, and size information. These utilities are crucial for:
-   **Standardization**: Transforming disparate raw data into a consistent format.
-   **De-duplication**: Enabling the system to identify and group identical products from different sources or with slight variations in their descriptions. This is achieved by generating a unique `normalized_name_brand_size` string for each product.
-   **Data Quality**: Improving the overall quality and usability of the product data in the database.

## How They Work Together (Data Flow)

The utilities in this directory work in a pipeline to process product information:

1.  **`extract_sizes.py`**:
    *   **Purpose**: This is the lowest-level utility for size extraction. It takes a raw text string (e.g., a product name, brand, or package size description) and uses regular expressions to identify and extract any size-related substrings. This is important becuase the size information is often in the brand or product name instead of or in addition to the size field. 
    *   **Output**: Returns a list of raw size strings found (e.g., `["500g"]`, `["1 each"]`, `["4x250ml"]`). It does *not* standardize these values.

2.  **`get_extracted_sizes.py`**:
    *   **Purpose**: This function orchestrates the use of `extract_sizes.py`. It takes a product dictionary (or model instance) and applies `extract_sizes` to relevant fields like `name`, `brand`, and `package_size`. It aggregates all found sizes.
    *   **Output**: Returns a sorted list of unique raw size strings. This list is stored directly in the `Product.sizes` JSONField in the database, preserving the original extracted values.

3.  **`get_cleaned_name.py`**:
    *   **Purpose**: This utility aims to derive a "clean" base name for a product by removing elements that might vary but don't define the core product. Specifically, it removes the brand name and any identified size strings from the product's original name.
    *   **Output**: A string representing the product's name stripped of brand and size information.

4.  **`standardize_sizes_for_norm_string.py`**:
    *   **Purpose**: This function is specifically designed for de-duplication. It takes the list of raw sizes (from `get_extracted_sizes`) and standardizes them into a consistent format. For example, "each", "1 each", and "1ea" would all be standardized to "1ea". Similarly, "pack" and "pk" variations are standardized.
    *   **Output**: A list of standardized size strings, used *only* for constructing the `normalized_name_brand_size` key.

5.  **`clean_value.py`**:
    *   **Purpose**: A general-purpose helper function used across the normalization process. It takes any string value and prepares it for inclusion in the `normalized_name_brand_size` key. This involves lowercasing, splitting into words, sorting the words alphabetically, and removing non-alphanumeric characters. This ensures that variations in word order, casing, or punctuation do not prevent de-duplication.
    *   **Output**: A cleaned and sorted string.

6.  **`get_normalized_string.py`**:
    *   **Purpose**: This is the central function for generating the `normalized_name_brand_size` de-duplication key. It brings together the outputs of other utilities.
    *   **Process**:
        *   It first calls `get_cleaned_name` to get the base product name.
        *   It then calls `standardize_sizes_for_norm_string` on the `extracted_sizes` to get a de-duplication-friendly list of sizes.
        *   Finally, it applies `clean_value` to the cleaned name, brand, and the standardized sizes, concatenating them into the final `normalized_name_brand_size` string.
    *   **Output**: The unique `normalized_name_brand_size` string, which is critical for identifying duplicate products across the entire dataset.
