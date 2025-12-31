# Products App

## Overview

The `products` app is the central hub for managing all product-related data within the SplitCart project. It defines the core data models for products, brands, prices, and their complex relationships. It also provides a comprehensive and highly optimized set of API endpoints for querying, displaying, and managing this data for the frontend application.

The app is designed for performance and scalability, making extensive use of caching, pre-calculated summary tables, and intelligent, context-aware serialization to handle large volumes of data efficiently.

## Data Models

The data architecture is built around the following key models:

-   **`Product`**: The core model representing a single, unique product. It stores essential details like `name`, `size`, `barcode`, and a link to its brand. A crucial field is `normalized_name_brand_size`, which provides a canonical, unique identifier for the product based on its key attributes.
-   **`ProductBrand`**: Represents a brand entity. It stores the canonical brand name and maintains a list of all known variations (`name_variations`) to consolidate different spellings or representations into a single record (e.g., 'St Dalfour' vs. 'St. Dalfour').
-   **`SKU`**: A simple model that links a `Product` to a `Company` via a company-specific SKU (Stock Keeping Unit).
-   **`Price`**: Represents the price of a `Product` at a specific `Store` on a given date. This one-to-many relationship allows for tracking price history and variations across different retail locations.
-   **`ProductSubstitution`**: A "through" model that defines a ranked and classified substitution relationship between two products. This allows the system to suggest alternatives (e.g., "Same brand, different size" or "Same category, similar product").
-   **`ProductPriceSummary`**: A key performance optimization. This is an aggregation table that stores pre-calculated metrics for each product, such as its minimum and maximum price across all stores and its `best_possible_discount`. This denormalized data allows for extremely fast discovery of potential bargains without expensive real-time calculations on the entire price table.

## Key API Endpoints & Functionality

The app exposes several powerful endpoints to serve data to the frontend.

### Product Listing & Search

-   **Endpoint**: `GET /api/products/`
-   **View**: `ProductListView`
-   **Functionality**: This is the primary endpoint for all product browsing and searching. It is highly flexible and accepts numerous query parameters for filtering (`search`, `primary_category_slug`, `bargain_company`) and sorting (`price_asc`, `unit_price_asc`). A key feature is the "bargain-first" default ordering (`get_bargain_first_ordering`), which intelligently prioritizes displaying products with the best available discounts based on the user's selected stores. The entire view is heavily cached and optimized with `prefetch_related` to ensure fast response times.

### Product Details

-   **Endpoint**: `GET /api/products/<int:pk>/`
-   **View**: `ProductDetailView`
-   **Functionality**: A standard cached endpoint to retrieve all details for a single product. It uses the `get_pricing_stores_map` utility to ensure that prices are fetched from the correct "anchor" stores relevant to the user's location.

### Bargain Discovery

-   **Endpoint**: `GET /api/products/bargain-carousel/`
-   **View**: `BargainCarouselView`
-   **Functionality**: A dedicated, highly optimized view designed to power the "Bargains" carousel. It uses a two-step process for maximum performance:
    1.  It first queries the `ProductPriceSummary` model to quickly get a list of candidate products with high theoretical discounts.
    2.  It then runs an in-memory calculation using the `bargain_utils.calculate_bargains` utility to determine the *true*, user-specific bargains from that candidate list.
    This approach avoids slow, complex queries on the live price data while ensuring accuracy.

### Product Substitutions

-   **Endpoint**: `GET /api/products/<int:product_id>/substitutes/`
-   **View**: `ProductSubstituteListView`
-   **Functionality**: Finds and ranks up to 5 available substitutes for a given product. It can be filtered by `store_ids` to ensure that the suggested substitutes are actually available for purchase in the user's selected stores.

### Data Management

-   **Endpoints**: `/api/export/...` and `/api/upload/...`
-   **Functionality**: The app provides a suite of administrative endpoints for exporting core data (products, categories, prices) and for bulk-uploading data, such as product substitution lists.

## Core Utilities & Design Patterns

The `products` app relies on several important utilities and design patterns to achieve its goals.

-   **`bargain_utils.py`**: Contains the core business logic for calculating real-time bargain percentages for products based on a user's selected stores.
-   **`product_ordering.py`**: Home to the `get_bargain_first_ordering` function, which orchestrates the complex logic of finding and ranking products to ensure the best deals are shown first.
-   **Context-Aware Serialization**: The `ProductSerializer` is a highly intelligent component. It receives significant context from the views (e.g., `nearby_store_ids`, `bargain_info_map`). This allows it to perform complex tasks—like calculating the correct image URL or displaying the right bargain message—efficiently during serialization, avoiding redundant logic and database queries.
-   **Performance Optimization**: The app demonstrates a strong focus on performance through extensive view caching, query optimization (`prefetch_related`, `defer`), and the use of the `ProductPriceSummary` table for pre-calculating expensive aggregations.
