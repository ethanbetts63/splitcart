# Scraping App

## Overview

The `scraping` app is a dedicated, model-free Django app responsible for orchestrating the collection of product and store data from external grocery store websites. It is designed as a robust, resilient, and extensible system for feeding normalized data into the main application's data processing pipeline.

The app's core design principle is the **separation of concerns**: fetching raw data is distinct from cleaning it, which is in turn separate from the final act of updating the database. This is achieved by having the scrapers' final output be `.jsonl` files staged in an "inbox", which are then consumed by a different process (`data_management` app).

## Core Workflow

The entire scraping process follows a well-defined, sequential workflow:

1.  **Initiation**: A user or a scheduled task runs a Django management command, most notably `python manage.py scrape --<company>`.

2.  **Scraper Selection**: The command selects the appropriate company-specific scraper class from the `scraping/scrapers/` directory. Each scraper inherits from the `BaseProductScraper` abstract base class.

3.  **Orchestration**: The scraper instance follows the rigid workflow defined by `BaseProductScraper`:
    `setup()` → `get_work_items()` → loop (`fetch` → `clean` → `write`).

4.  **Fetching**: The scraper uses the `requests` library, often with a persistent `Session` object and custom headers, to make HTTP calls to the target website's internal APIs. It retrieves raw product data, typically in JSON format, handling company-specific details like authentication and pagination.

5.  **Cleaning & Normalization**: The raw JSON data is immediately passed to a company-specific `DataCleaner` class (e.g., `DataCleanerWoolworths`). This crucial step is responsible for:
    -   Mapping the company's unique field names to a standard internal schema (e.g., `Stockcode` → `sku`).
    -   Cleaning and standardizing data types (e.g., prices, booleans, category paths).
    -   Using pre-downloaded "translation tables" (from the `data_management` app) to normalize product names and brands against canonical database records *at the time of scraping*.

6.  **Staging (The "Inbox" Pattern)**: The cleaned, standardized, and normalized product data is written line-by-line into a new `.jsonl` file. This file is saved into a dedicated "inbox" directory (`data_management/data/inboxes/product_inbox/`), acting as a staging area. This transactional file-based approach ensures that raw scraped data is never lost if a downstream process (like a database update) fails.

7.  **Handover**: Once the `.jsonl` file is successfully created and committed, the `scraping` app's job for that store is complete. A separate process, the `update --products` command in the `data_management` app, is solely responsible for reading from the inbox and populating the main Django database.

## Key Components

-   **`management/commands/`**: These are the entry points for all scraping tasks.
    -   `scrape`: The main command for product scraping. It includes a sophisticated worker model, distinguishing between a modern, session-persistent scraper for Coles (`--coles`) and a legacy, scheduler-driven worker for other companies.
    -   `find_stores`: The command for discovering and scraping store location data.
    -   `scrape_barcodes`: A command to enrich product data with barcode information.

-   **`scrapers/`**: This directory contains the core scraping logic.
    -   `base_product_scraper.py` and `base_store_scraper.py`: Abstract Base Classes that define the required methods and orchestration for any product or store scraper.
    -   `product_scraper_<company>.py`: Concrete implementations for each grocery company (Coles, Woolworths, Aldi, IGA), containing the specific logic for making API calls, handling authentication, and managing pagination.

-   **`utils/product_scraping_utils/`**: A rich toolkit that supports the cleaning and normalization process.
    -   `BaseDataCleaner.py`: An ABC that defines the cleaning process and provides common helper methods (e.g., for price and unit price normalization).
    -   `DataCleaner<Company>.py`: Concrete implementations that handle the unique, messy data structures of each company's API response.
    -   `jsonl_writer.py`: A utility for transactionally writing to the output `.jsonl` files, with `commit()` and `cleanup()` methods to ensure atomicity.
    -   `product_normalizer.py`: A key utility that uses the aforementioned translation tables to standardize product data on the fly.

## Design Principles

-   **Separation of Concerns**: Fetching, cleaning, and database updating are three distinct, decoupled stages. This makes the system easier to debug and maintain.
-   **Resilience**: The "inbox" pattern ensures data is not lost if a database write fails. The data can be re-processed from the `.jsonl` file. The session management for Coles is designed to gracefully handle interruptions like CAPTCHAs.
-   **Extensibility**: Adding a new grocery store follows a clear pattern:
    1.  Create a new `product_scraper_<new_company>.py` class inheriting from `BaseProductScraper`.
    2.  Create a new `DataCleaner<NewCompany>.py` class inheriting from `BaseDataCleaner`.
    3.  Add the new company option to the `scrape` management command.
