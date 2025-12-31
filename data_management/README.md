# Data Management App

The `data_management` app is the central hub for processing, cleaning, and updating all data within the SplitCart ecosystem. It acts as the bridge between the raw, scraped data collected by the `scraping` app and the structured, queryable data served by the main Django application.

This app is responsible for consuming data from the various "inbox" directories, where scrapers deposit their findings as `.jsonl` files. It then uses a series of robust, object-oriented services to validate, clean, and persist this information into the database.

## Core Responsibilities

1.  **Data Consumption and Processing**:
    -   The app's primary entry point is the `update` management command, which orchestrates the entire data update process.
    -   It processes product data from the `product_inbox`, store data from the `store_inbox`, and other data types from their respective inboxes.
    -   A sophisticated, multi-stage pipeline handles the creation and updating of `Products`, `Prices`, `Categories`, `Brands`, and their complex relationships. This pipeline is designed for speed and clarity, using in-memory caches and bulk database operations to minimize overhead. For a detailed explanation of this workflow, see the `database_updating_classes/product_updating/README.md` file.

2.  **Data Generation and Analysis**:
    -   Beyond simple data ingestion, this app is responsible for generating derived data and performing analysis.
    -   The `generate` command can create supplementary data like `StoreGroups`, `PrimaryCategories`, and `ProductPriceSummary` statistics.
    -   It also includes tools for analyzing data freshness (`--store-stats`) and generating content for the site, such as pillar pages.

3.  **Data Integrity and Maintenance**:
    -   The app includes post-processing steps to ensure data integrity, such as reconciling duplicate products and brands.
    -   It contains logic to detect and fix issues in the category hierarchy, such as circular dependencies.
    -   The `GroupMaintenanceOrchestrator` ensures that `StoreGroup` entities remain healthy and accurate over time.

## Key Components

-   **`management/commands`**: Contains all the custom Django commands for triggering data updates and generation. See the `management/commands/README.md` for a full command reference.
-   **`database_updating_classes`**: The core of the data processing pipeline. This directory contains the object-oriented services responsible for handling each aspect of the database update, from reading files to persisting data.
-   **`analysers`**: Contains scripts for performing various analyses on the data, such as calculating product overlap between companies.
-   **`utils`**: A collection of utility functions and classes that support the main data processing and generation tasks. This includes generators for substitutions, category links, and price comparisons.
-   **`config.py`**: A centralized configuration file for parameters used in data generation and analysis, such as semantic similarity thresholds and savings benchmark settings.

## Workflow Overview

The typical data flow through this app is as follows:

1.  **Upload**: Raw data (`.jsonl` files) is uploaded to the appropriate inbox directory on the server (e.g., `data_management/data/inboxes/product_inbox/`).
2.  **Update**: The `python manage.py update` command is executed on the server.
3.  **Processing**: The `UpdateOrchestrator` reads files from the inbox and passes the data through a series of specialized managers (`BrandManager`, `ProductManager`, `CategoryManager`, `PriceManager`).
4.  **Persistence**: Each manager handles its own database operations, using bulk methods to efficiently create and update records.
5.  **Post-Processing**: After all files are processed, a series of maintenance and reconciliation tasks are run to clean the data and ensure its integrity.
6.  **Generation**: The `python manage.py generate` command is run to create derived data, statistics, and other content required by the application.
