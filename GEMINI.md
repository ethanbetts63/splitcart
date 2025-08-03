# Project Overview

This project is a Django-based application called "splitcart". It appears to be a web scraper and data aggregation tool for comparing prices of products from different Australian grocery stores, specifically coles, woolworths, IGA, spudshed and aldi. The project is structured into three main Django apps: `stores`, `products`, and `api`.

**Key Technologies:**

*   **Backend:** Django
*   **Database:** SQLite (as per `settings.py`)
*   **Data Scraping:** The project uses custom scrapers to fetch data from stores websites. 

**Architecture:**

1.  **Data Scraping:**
    *   Management commands (`scrape_coles`, `scrape_woolworths`, etc) are used to initiate the scraping process.
    *   Scraped data is saved as raw JSON files in the `api/data/raw_data` directory.

2.  **Data Processing:**
    *   The `process_raw_data` management command processes the raw JSON files.
    *   It combines data by category and archives it in the `api/data/processed_data` directory.

3.  **Database Update:**
    *   The `update_database` management command is intended to update the database with the processed data, but it is currently empty.

**Models:**

*   **`stores` app:**
    *   `Store`: Represents a grocery store (e.g., coles, woolworths).
    *   `Category`: Represents a product category, with support for hierarchical categories.
*   **`products` app:**
    *   `Product`: Represents a master product, independent of any single store.
    *   `Price`: Represents the price of a product at a specific store on a specific date.

# Building and Running

**1. Setup:**

*   It is assumed that a Python virtual environment is set up in the `venv` directory.
*   Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

**2. Database Migration:**

*   Apply the database migrations to create the necessary tables:
    ```bash
    python manage.py migrate
    ```

**3. Data Scraping and Processing:**

*   To scrape data from coles:
    ```bash
    python manage.py scrape_coles
    ```
*   To scrape data from woolworths:
    ```bash
    python manage.py scrape_woolworths
    ```
*   To process the scraped data:
    ```bash
    python manage.py process_raw_data
    ```

**4. Running the Development Server:**

*   To run the Django development server:
    ```bash
    python manage.py runserver
    ```

# Development Conventions

*   The project follows the standard Django project structure.
*   Code is organized into separate apps for `stores`, `products`, and `api`.
*   Management commands are used for data scraping and processing tasks.
*   The project includes a comprehensive test suite, with tests for models, management commands, and utility functions.
