# Products App

## Overview

The `products` app is the central hub for product-related data in SplitCart. It defines products, brands, prices, substitutions, summaries, and the API endpoints used by the frontend.

The app is designed for performance and scalability, using caching, pre-calculated summary tables, and context-aware serialization to handle large product catalogs efficiently.

## Data Models

- **`Product`**: The core model representing a single, unique product. It stores details like `name`, `size`, `barcode`, brand, and normalized identity fields.
- **`ProductBrand`**: Represents a brand entity and known brand-name variations.
- **`SKU`**: Links a `Product` to a `Company` via a company-specific SKU.
- **`Price`**: Represents the price of a `Product` at a specific `Company` on a given date.
- **`ProductSubstitution`**: Defines ranked and classified substitution relationships between products.
- **`ProductPriceSummary`**: Stores pre-calculated price metrics for each product, such as minimum price, maximum price, and `best_possible_discount`.

## Key API Endpoints

### Product Listing & Search

- **Endpoint**: `GET /api/products/`
- **View**: `ProductListView`
- **Functionality**: Product browsing and searching with filters like `search`, `primary_category_slug`, and `bargain_company`, plus sorting like `price_asc` and `unit_price_asc`. The default bargain-first ordering prioritizes products with strong discounts across companies.

### Product Details

- **Endpoint**: `GET /api/products/<int:pk>/`
- **View**: `ProductDetailView`
- **Functionality**: Cached endpoint for retrieving all details for a single product.

### Bargain Discovery

- **Endpoint**: `GET /api/products/bargain-carousel/`
- **View**: `BargainCarouselView`
- **Functionality**: Powers the bargains carousel by querying `ProductPriceSummary` for candidates, then using `bargain_utils.calculate_bargains` to confirm real discounts from live price data.

### Product Substitutions

- **Endpoint**: `GET /api/products/<int:product_id>/substitutes/`
- **View**: `ProductSubstituteListView`
- **Functionality**: Finds and ranks available substitutes for a given product.

## Core Utilities

- **`bargain_utils.py`**: Calculates real-time bargain percentages for products across companies.
- **`product_ordering.py`**: Implements bargain-first product ordering.
- **Context-Aware Serialization**: `ProductSerializer` uses view context such as `bargain_info_map` to display bargain messages efficiently.
- **Performance Optimization**: Uses view caching, query optimization, and `ProductPriceSummary` for expensive aggregations.
