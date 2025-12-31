# Companies Django App

This app defines the core data models for the entire SplitCart application, focusing on the representation of companies, stores, their geographic data, and their product taxonomies. It serves as the foundational layer that describes the entities involved in the grocery market.

## Data Architecture

The data model can be understood in four main parts: a corporate hierarchy, a geographic system, store clustering, and a dual-taxonomy system for products.

### 1. Corporate & Geographic Hierarchy

This defines the physical and organizational structure of the grocery retailers.

-   **`Company`**: The top-level entity representing a parent company (e.g., "Coles Group", "Woolworths Group").
-   **`Division`**: A specific banner or brand under a `Company` (e.g., "Coles Supermarkets", "Woolworths Metro").
-   **`Store`**: An individual physical store. It holds address information, geographic coordinates (latitude/longitude), and a unique `store_id` from the parent company's system. It also contains metadata for managing data scraping (`last_scraped`, `needs_rescraping`).
-   **`Postcode`**: A model storing Australian postcodes with their corresponding state and geographic center (latitude/longitude), used for proximity searches.

### 2. Store Clustering

To simplify price comparisons across hundreds of stores, the app groups them into logical clusters. The detailed "bottom-up" logic for how these groups are automatically created and maintained is documented in `data_management/database_updating_classes/product_updating/group_maintanance/README.md`.

-   **`StoreGroup`**: A logical grouping of `Store` objects from a single `Company`, typically based on geographic proximity.
-   **`anchor`**: A key field on the `StoreGroup` model that points to a single `Store`. This "anchor store" is considered the source of truth for pricing for all other stores in its group.
-   **`StoreGroupMembership`**: A simple through model that explicitly links a `Store` to a `StoreGroup`. A store can only belong to one group.

### 3. Dual-Taxonomy System for Categories

A major function of this app is to normalize product categories from different retailers. It does this using a two-tiered system.

**Internal (Normalized) Taxonomy:**
This is our internal, standardized hierarchy used for SEO, content generation, and high-level analysis.
-   **`PillarPage`**: The highest-level grouping, designed for creating SEO content (e.g., a landing page for "Fresh Produce"). Contains fields for page titles and introduction text.
-   **`PrimaryCategory`**: A standardized, high-level category (e.g., "Fruit", "Dairy"). These are the building blocks of `PillarPage`s.

**External (Company-Specific) Taxonomy:**
This represents the native category structure as found on each retailer's website.
-   **`Category`**: A category specific to one `Company` (e.g., the "Fruit & Veg" category on the Coles website). It can have its own parent/child relationships to mirror the source website's hierarchy.
-   **`CategoryLink`**: The crucial `through` model that maps relationships *between* `Category` objects from different companies. This is what allows the system to understand that Coles' "Bakery" category is a `MATCH` for Woolworths' "Bread & Bakery" category.

## API Endpoints

This app primarily provides internal-facing APIs for data export and searching, protected by the `IsInternalAPIRequest` permission.

-   `GET /api/companies/export/companies/`
    -   **View:** `CompanyListView`
    -   **Description:** Returns a list of all `Company` objects.

-   `GET /api/companies/export/stores/`
    -   **View:** `ExportStoresView`
    -   **Description:** Exports a detailed list of all `Store` objects.

-   `GET /api/companies/export/anchor-stores/`
    -   **View:** `ExportAnchorStoresView`
    -   **Description:** Exports a list of store IDs for all stores that are designated as an `anchor` for a `StoreGroup`. This is used by other services to identify the primary sources for pricing data.

-   `GET /api/companies/postcodes/search/?postcode=<postcode>`
    -   **View:** `PostcodeSearchView`
    -   **Description:** Searches for and returns the details of a single `Postcode` object. The result is cached for 24 hours.

## Management Commands

The app includes commands for data analysis and reporting on the health of the category system.

-   `python manage.py category_stats`
    -   **Description:** Generates a report on product category distribution, showing how many companies stock products in each `PrimaryCategory` and how many products are common across all major retailers.

-   `python manage.py primary_cat_stats`
    -   **Description:** Reports on the integrity of the category mapping system. It shows how many company-specific `Category` objects are linked to each `PrimaryCategory` and lists the number of categories that are currently unassigned.
