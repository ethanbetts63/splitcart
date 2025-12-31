# SplitCart

**Live Site:** [https://www.splitcart.com.au/]

## The Smart Grocery Price Comparison Platform

Splitcart is an Australian smart grocery price comparison platform that finds the absolute cheapest way to buy your entire shopping list by intelligently splitting it across multiple supermarkets. Instead of just comparing single-store totals, it accounts for real item-level price differences, delivery fees, store availability, distance, and user constraints (like max stores or minimum savings), while also suggesting cheaper substitute products you approve.

Under the hood, it cleans and normalizes messy supermarket data, matches equivalent products across brands and stores, and runs an optimization algorithm to surface the best combination—saving users real money without the manual tab-hopping. It’s built for budget-conscious shoppers who want clear, actionable savings, and for scale, it opens the door to insights like national average prices, true discount tracking, and where groceries are genuinely cheaper.

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
    Create a `.env` file in the root of the project with the following structure. **Do not use these exact values in production.**

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
    Update your WSGI file on PythonAnywhere with the following configuration:
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
