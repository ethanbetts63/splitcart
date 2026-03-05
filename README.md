# SplitCart

**Live Site:** [https://www.splitcart.com.au/]

## The Smart Grocery Price Comparison Platform

Splitcart is an Australian grocery price comparison platform that finds the absolute cheapest way to buy your entire shopping list by intelligently splitting it across multiple supermarkets. Instead of just comparing single-store totals, it accounts for real item-level price differences, delivery fees, store availability, distance, and user constraints (like max stores or minimum savings), while also suggesting cheaper substitute products you approve.

Under the hood, it cleans and normalizes messy supermarket data, matches equivalent products across brands and stores, and runs an optimization algorithm to surface the best combination—saving users real money without the manual tab-hopping. It’s built for budget-conscious shoppers who want clear, actionable savings, and for scale, it opens the door to insights like national average prices, true discount tracking, and where groceries are genuinely cheaper.

> **Two most interesting pieces of engineering in this codebase:**
> - [`_docs/normalized_name_brand_size.md`](_docs/normalized_name_brand_size.md) — A self-improving feedback loop that learns to recognize the same product across different supermarkets, getting smarter with every scrape run.
> - [`_docs/store_grouping.md`](_docs/store_grouping.md) — A self-organizing clustering system that detects which stores share identical prices and deduplicates the database automatically, converging toward a minimal representation over time.

> **Looking to contribute?** The inferred barcode prefix method in [`_docs/gs1.md`](_docs/gs1.md) is an unsolved problem — a promising idea that hasn't been fully validated or wired in yet.

## Documentation

The `_docs/` directory contains in-depth references for the non-obvious parts of the system. Start here before working in an unfamiliar area.

- [`pipeline.md`](_docs/pipeline.md) — Full data lifecycle — from local scrape to live DB, including the two-environment split
- [`normalized_name_brand_size.md`](_docs/normalized_name_brand_size.md) — How products are identified across stores using a self-improving normalized key
- [`store_grouping.md`](_docs/store_grouping.md) — How stores with identical pricing are detected and deduplicated at the DB level
- [`optimization.md`](_docs/optimization.md) — The LP-based cart splitting algorithm and the factors that determine savings potential
- [`gs1.md`](_docs/gs1.md) — How GS1 barcode prefixes are used to normalize brand names authoritatively
- [`product_brand.md`](_docs/product_brand.md) — `ProductBrand` model — fields, variation accumulation, brand translation table, and the GS1→reconciler loop
- [`substitutions.md`](_docs/substitutions.md) — How substitute products are matched and ranked across brands and categories
- [`bargains.md`](_docs/bargains.md) — How bargain products are detected and scored
- [`product_price_summary.md`](_docs/product_price_summary.md) — Pre-computed price aggregates that make bargain queries fast
- [`bargain_stats.md`](_docs/bargain_stats.md) — Pre-computed head-to-head company price comparison stats
- [`categories.md`](_docs/categories.md) — The product categorisation hierarchy and how primary categories are assigned
- [`scraping.md`](_docs/scraping.md) — How the scraping pipeline works end to end
- [`scraper_testing.md`](_docs/scraper_testing.md) — Strategy for testing scrapers and normalization
- [`TESTING.md`](_docs/TESTING.md) — Testing philosophy, stack (pytest/factory_boy), and fixture conventions
- [`home.md`](_docs/home.md) — Home page and featured content logic
- [`recommendations.md`](_docs/recommendations.md) — Essentially a to do list

---

## Project Structure

This project is a monorepo containing both the Django backend and the React frontend.

### Backend

The backend is a Django application responsible for data scraping, processing, and serving the API. It is divided into several apps:

-   **`products`**: Manages all product-related data, including models for products, brands, prices, and substitutions. It also provides the primary API endpoints for the frontend. See the [products/README.md](products/README.md) for more details.
-   **`companies`**: Defines the core data models for companies, stores, geographic data, and product taxonomies. See the [companies/README.md](companies/README.md) for more details.
-   **`scraping`**: A dedicated, model-free app responsible for orchestrating the collection of product and store data from external grocery store websites. See the [scraping/README.md](scraping/README.md) for more details.
-   **`data_management`**: The central hub for processing, cleaning, and updating all data within the ecosystem. It acts as the bridge between the raw, scraped data and the structured, queryable data. See the [data_management/README.md](data_management/README.md) for more details.
-   **`users`**: Manages users, authentication, and user-specific data like shopping carts and saved store lists. It contains the business logic for cart price optimization and user session management. See the [users/README.md](users/README.md) for more details.

### Frontend

The frontend is a modern React application built with TypeScript. It provides a user-friendly interface for searching for products, managing shopping lists, and discovering bargains.

The frontend is located in the `frontend` directory and uses the following technologies:

-   **React**: A JavaScript library for building user interfaces.
-   **TypeScript**: A typed superset of JavaScript that compiles to plain JavaScript.
-   **Vite**: A build tool that provides a faster and leaner development experience for modern web projects.
-   **React Router**: For declarative routing in the application.
-   **React Context**: For state management.
-   **Tailwind CSS**: A utility-first CSS framework for rapid UI development.

## Development Setup

For a complete and robust local development setup, use the `reset_splitcart.ps1` PowerShell script. This script automates the entire process of resetting the database, cleaning migrations, and applying a fresh database schema.

Please refer to the script for detailed instructions on how to manually reset the MySQL database before running the script.

## Deployment (PythonAnywhere)

The project is configured for deployment on PythonAnywhere. The following steps outline the deployment process:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ethanbetts63/splitcart.git
    ```
2.  **Set up the virtual environment:**
    ```bash
    cd splitcart
    python3.12 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  **Apply database migrations:**
    ```bash
    python manage.py migrate
    ```
4.  **Build the frontend:**
    ```bash
    deactivate
    cd ~/splitcart/frontend
    npm install
    npm run build
    ```
5.  **Collect static files:**
    ```bash
    cd ..
    source venv/bin/activate
    python manage.py collectstatic --noinput
    ```
6.  **Create the `.env` file:**
    Create a `.env` file in the root of the project with the following structure. 

    ```
    API_SERVER_URL="http://www.your-domain.com/"
    EMAIL_HOST_PASSWORD=your_email_password
    SECRET_KEY="your_django_secret_key"
    INTERNAL_API_KEY="your_internal_api_key"
    DEBUG=False
    DB_NAME=your_db_name
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    DB_HOST=your_db_host
    PORT=3306
    ```
7.  **Configure the WSGI file:**
    SplitCart is deployed to python anywhere. This is a set up that works there:
    ```python
    import os
    import sys

    path = '/home/your_username/splitcart'
    if path not in sys.path:
        sys.path.append(path)

    os.environ['DJANGO_SETTINGS_MODULE'] = 'splitcart.settings'

    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    ```
