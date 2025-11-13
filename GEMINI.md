# Project Overview

This project is a Django-based application called "splitcart". It is designed as a web scraper and data aggregation tool for comparing prices of products from different Australian grocery stores, including Coles, Woolworths, IGA, and Aldi. 

**Key Technologies:**

*   **Backend:** Django
*   **Database:** MySql (as per `settings.py`)
*   **Data Scraping:** The project uses custom scrapers to fetch data from stores' websites.

**Frontend Architecture:**

The frontend is built using React (JavaScript/TypeScript) and leverages the following technologies and patterns:

*   **Framework:** React (JavaScript/TypeScript) for building interactive user interfaces.
*   **Styling:** Tailwind CSS for utility-first styling, complemented by Shadcn/ui for pre-built, customizable UI components.
*   **Routing:** React Router DOM for declarative routing within the single-page application.
*   **State Management:** React Context API is extensively used for managing global application state, including:
    *   `ShoppingListContext`: Manages the user's current shopping list items.
    *   `StoreContext`: Handles the selection and management of grocery stores.
    *   `SubstitutionContext`: Manages product substitution selections.
    *   `AuthContext`: Manages user authentication status and tokens.
*   **UI Components:** A mix of custom-built React components (e.g., `FaqImageSection`, `ProductCarousel`, `ProductTile`, `CartItemTile`) and components provided by Shadcn/ui (e.g., `Button`, `Input`, `Card`, `Accordion`, `AspectRatio`, `Switch`, `Label`, `Badge`) are used to construct the user interface.

**Architecture:**

1.  **Data Scraping & Normalization:**
    *   The `scrape` management command initiates the scraping process, with options for specific stores (e.g., `python manage.py scrape --coles`).
    *   Each product is individually cleaned, normalized (generating a `normalized_name_brand_size` string), and saved as a JSON line (`.jsonl`) file in the `data_management/data/inboxes/product_inbox/` directory. This approach isolates errors and improves resilience.

2.  **Database Update (Refactored OOP System):**
    *   The `update` management command (specifically the `--products` flag) now utilizes a refactored, object-oriented system to process files from the `product_inbox` and update the database.
    *   This system is designed for clarity, testability, and robustness, handling data consolidation, product matching, category relationships, and price updates efficiently.

    **Core Database Update Services:**

**Models:**


## Management Commands

Here is a brief overview of the available management commands:


## Data Pipeline Flow

This section outlines the standard workflow for collecting, processing, and archiving data.

### Step 1: Discover and Add Stores

1.  **Find Stores:** Use the `find_stores` command to discover store locations for a specific company.
    ```bash
    python manage.py find_stores --company <company_name>
    ```
2.  **Update Database:** Use the `update` command to add the newly discovered stores to the database.
    ```bash
    python manage.py update --stores
    ```

### Step 2: Scrape Product Data

*   **Scrape:** Use the `scrape` command to fetch product data for the stores of a specific company. The scraped data is cleaned, normalized, and saved into the `product_inbox`.
    ```bash
    python manage.py scrape --<company_name>
    ```

### Step 3: Update Database with Products

*   **Update:** Use the `update --products` command to populate the database with the processed product and price information from the `product_inbox`. This step now leverages the refactored object-oriented system for robust and efficient processing. For a detailed explanation of this new workflow, refer to `final_workflow_explanation.txt`.
    ```bash
    python manage.py update --products
    ```

## Session Summaries

At the end of each session, a summary file must be created to document the work performed. This summary should cover all major changes, discussions, and decisions made during the session.

-   **Location:** `C:\Users\ethan\coding\splitcart\gemini_session_summaries\`
-   **Naming Convention:** The file must be named `summary<N>.txt`, where `N` is the number of the previous summary file plus one (e.g., `summary28.txt`).
