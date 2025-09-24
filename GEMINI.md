# Project Overview

This project is a Django-based application called "splitcart". It is designed as a web scraper and data aggregation tool for comparing prices of products from different Australian grocery stores, including Coles, Woolworths, IGA, Spudshed, and Aldi. The project is structured into three main Django apps: `companies`, `products`, and `data_management`.

**Key Technologies:**

*   **Backend:** Django
*   **Database:** SQLite (as per `settings.py`)
*   **Data Scraping:** The project uses custom scrapers to fetch data from stores' websites.

**Architecture:**

1.  **Data Scraping & Normalization:**
    *   The `scrape` management command initiates the scraping process, with options for specific stores (e.g., `python manage.py scrape --coles`).
    *   Each product is individually cleaned, normalized (generating a `normalized_name_brand_size` string), and saved as a JSON line (`.jsonl`) file in the `data_management/data/product_inbox/` directory. This approach isolates errors and improves resilience.

2.  **Database Update (Refactored OOP System):**
    *   The `update_db` management command (specifically the `--products` flag) now utilizes a refactored, object-oriented system to process files from the `product_inbox` and update the database.
    *   This system is designed for clarity, testability, and robustness, handling data consolidation, product matching, category relationships, and price updates efficiently.

    **Core Database Update Services:**
    *   **`UpdateOrchestrator`**: The central controller. It iterates through inbox files, instantiates per-file services, and manages the overall flow from consolidation to final commit and cleanup.
    *   **`ProductResolver`**: Built per-file, this service holds contextual in-memory caches (barcodes, normalized strings, store-specific product IDs, existing prices) to efficiently match incoming products against existing database records.
    *   **`UnitOfWork`**: Manages all proposed database changes (new products, prices, updates). It collects these changes and performs efficient `bulk_create` and `bulk_update` operations within a single, atomic database transaction.
    *   **`CategoryManager`**: Handles the creation of new categories, establishes parent-child relationships, and links products to their respective categories within the database transaction.
    *   **`VariationManager`**: Detects product name variations, manages a reconciliation list for potential duplicates, and performs post-processing reconciliation to merge actual duplicate product records.
    *   **`TranslationTableGenerator`**: A utility that regenerates a Python file containing a mapping of product name variations to their canonical names, based on the database's `name_variations` data.

**Models:**

*   **`companies` app:**
    *   `Store`: Represents a grocery store (e.g., Coles, Woolworths).
    *   `Category`: Represents a product category, with support for hierarchical relationships and association with a `Company`.
*   **`products` app:**
    *   `Product`: Represents a master product, independent of any single store, with fields for name variations and normalized identifiers.
    *   `Price`: Represents the price of a product at a specific store on a specific date, linked to `Product` and `Store` models.

## Management Commands

Here is a brief overview of the available management commands:

*   `find_stores`: Discovers store locations for a specific company and saves the data for processing.
*   `scrape`: Scrapes product data from specified store websites, saving it to the `product_inbox`.
*   `update_db`: A consolidated command that updates the database with new data. Its `--products` flag now uses the refactored OOP system for robust product and price updates from the inbox. It also supports updating stores from discovery (`--stores`) or from archives (`--archive`).
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

*   **Update:** Use the `update_db --products` command to populate the database with the processed product and price information from the `product_inbox`. This step now leverages the refactored object-oriented system for robust and efficient processing. For a detailed explanation of this new workflow, refer to `final_workflow_explanation.txt`.
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

## Session Summaries

At the end of each session, a summary file must be created to document the work performed. This summary should cover all major changes, discussions, and decisions made during the session.

-   **Location:** `C:\Users\ethan\coding\splitcart\gemini_session_summaries\`
-   **Naming Convention:** The file must be named `summary<N>.txt`, where `N` is the number of the previous summary file plus one (e.g., `summary28.txt`).
