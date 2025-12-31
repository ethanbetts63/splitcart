# Data Management Commands

This directory contains custom Django management commands for processing, generating, and uploading data for the SplitCart application.

## Command Reference

Below is a detailed explanation of the available commands and their workflows.

### Data Update Workflow

The core workflow for updating product and store data involves three main stages: uploading raw data, processing it on the server, and then running post-processing tasks.

#### 1. Uploading Data (Local)

These commands are run on a local development machine to send data to the server's "inbox" directories.

-   `python manage.py upload --products --dev`
    Uploads new or updated product data (`.jsonl` files) to the server. The `--dev` flag targets the development server.

-   `python manage.py upload --cat-links --dev`
    Uploads generated category link files to the server.

-   `python manage.py upload --subs --dev`
    Uploads generated product substitution files to the server.

#### 2. Processing Data (Server)

Once data is uploaded to the server's inboxes, these `update` commands are run to process it and update the main database.

-   `python manage.py update --products`
    Processes `.jsonl` files from the `product_inbox`. It reads the scraped product data, cleans it, and updates the corresponding `Product` and `Price` models in the database. This command runs in a loop, processing files until the inbox is empty.

-   `python manage.py update --cat-links`
    Processes files from the `category_links_inbox` to update category relationships.

-   `python manage.py update --subs`
    Processes files from the `substitutions_inbox` to update product substitution data.

-   `python manage.py update --archive`
    Flushes the entire database and restores it from the most recent database archive. This is a destructive operation and should be used with caution.

### Data Generation Workflow

These commands generate supplementary data, statistics, and content required by the application. Some are designed for local use (`--dev`), while others run on the server.

#### 1. Local Generation and Upload

-   `python manage.py generate --cat-links --dev`
    Analyzes product and category data to generate optimized category links, which are saved to a file locally.

-   `python manage.py generate --subs --dev`
    Generates product substitution recommendations based on existing data and saves them to a file locally.

#### 2. Server-Side Generation

These commands are typically run on the server to create derived data or perform analysis.

-   `python manage.py generate --store-groups`
    Analyzes stores and their product offerings to group them into logical clusters for comparison.

-   `python manage.py generate --primary-cats`
    Generates primary categories based on the existing category hierarchy.

-   `python manage.py generate --bargain-stats`
    Calculates and caches statistics about the best bargains available across different companies.

-   `python manage.py generate --pillars`
    Generates "pillar pages," which are landing pages for primary product categories.

-   `python manage.py generate --price-comps`
    Generates data for price comparisons between different stores.

-   `python manage.py update --faqs`
    Updates Frequently Asked Questions (FAQs) from a `FAQ.jsonl` file.

-   `python manage.py generate --store-stats`
    Generates and displays a report on data freshness and coverage for all stores.

-   `python manage.py generate --price-summaries`
    Aggregates price data to create summary views, improving performance for product listings.

-   `python manage.py generate --default-stores`
    Sets a default list of "anchor stores" that are used for site-wide comparisons.

### Miscellaneous Commands

-   `python manage.py import_postcodes`
    Populates the `Postcode` model from a `postcodes.json` file. This is typically a one-time setup command.
