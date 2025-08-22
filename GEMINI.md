# Project Overview

This project is a Django-based application called "splitcart". It appears to be a web scraper and data aggregation tool for comparing prices of products from different Australian grocery stores, specifically coles, woolworths, IGA, spudshed and aldi. The project is structured into three main Django apps: `companies`, `products`, and `api`.

**Key Technologies:**

*   **Backend:** Django
*   **Database:** SQLite (as per `settings.py`)
*   **Data Scraping:** The project uses custom scrapers to fetch data from stores websites. 

**Architecture:**

1.  **Data Scraping & Normalization:**
    *   The `scrape` management command is used to initiate the scraping process, with options for specific stores (e.g., `python manage.py scrape --coles`).
    *   Each product is individually cleaned, normalized, and saved as a separate JSON file in the `api/data/product_inbox/` directory. This isolates errors and improves resilience.

2.  **Database Update:**
    *   The `update_db` management command processes the files in the `product_inbox`. It performs in-memory de-duplication using a normalized key and then performs efficient batch operations to update the database with new products and prices.

**Models:**

*   **`companies` app:**
    *   `Store`: Represents a grocery store (e.g., coles, woolworths).
    *   `Category`: Represents a product category, with support for hierarchical categories.
*   **`products` app:**
    *   `Product`: Represents a master product, independent of any single store.
    *   `Price`: Represents the price of a product at a specific store on a specific date.

## Management Commands

Here is a brief overview of the available management commands:

*   `find_stores`: Finds stores for a specific company and saves the data to be processed.
*   `scrape`: Scrapes product data from the websites of the specified stores, saving it to the product inbox.
*   `update_db`: A consolidated command that updates the database with all new data, including stores from discovery and products from the inbox or archives.
*   `build_company_jsons`: Generates JSON archives containing data about companies and their stores.
*   `build_store_jsons`: Generates detailed JSON archives for each store, including product and price history.
*   `analyze_data`: A flexible tool for data analysis that can generate various reports, charts, and heatmaps.
*   `compare_stores`: A utility to compare the product offerings between two specified stores.
*   `get_woolworths_substitutes`: A specialized command to fetch substitute product information from Woolworths.

## Data Pipeline Flow

This section outlines the standard workflow for collecting, processing, and archiving data.

### Step 1: Discover and Add Stores

1.  **Find Stores:** Use the `find_stores` command to discover store locations for a specific company.
    ```bash
    python manage.py find_stores --company <company_name>
    ```
2.  **Update Database:** Use the `update_db` command to add the newly discovered stores to the database.
    ```bash
    python manage.py update_db --stores
    ```

### Step 2: Scrape Product Data

*   **Scrape:** Use the `scrape` command to fetch product data for the stores of a specific company. The scraped data is cleaned, normalized, and saved into the `product_inbox`.
    ```bash
    python manage.py scrape --<company_name>
    ```

### Step 3: Update Database with Products

*   **Update:** Use the `update_db` command again, this time to populate the database with the processed product and price information from the `product_inbox`.
    ```bash
    python manage.py update_db --products
    ```

### Step 4: Analyze Data and Generate Archives (Optional)

*   **Analyze:** Use the `analyze_data` command to generate reports, charts, and heatmaps.
    ```bash
    python manage.py analyze_data --report company_heatmap
    ```
*   **Archive:** Use the `build_company_jsons` and `build_store_jsons` commands to create data archives.
    ```bash
    python manage.py build_company_jsons
    python manage.py build_store_jsons
    ```
