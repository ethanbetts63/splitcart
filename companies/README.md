# Companies Django App

This app defines the core data models for the entire SplitCart application, focusing on companies and product taxonomies. It serves as the foundational layer that describes the entities involved in the grocery market.

## Data Architecture

The data model can be understood in two main parts: a company model and a dual-taxonomy system for products.

### 1. Company Data

This defines the grocery retailers.

-   **`Company`**: The top-level entity representing a parent company (e.g., "Coles Group", "Woolworths Group").

### 2. Dual-Taxonomy System for Categories

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

## Management Commands

The app includes commands for data analysis and reporting on the health of the category system.

-   `python manage.py category_stats`
    -   **Description:** Generates a report on product category distribution, showing how many companies stock products in each `PrimaryCategory` and how many products are common across all major retailers.

-   `python manage.py primary_cat_stats`
    -   **Description:** Reports on the integrity of the category mapping system. It shows how many company-specific `Category` objects are linked to each `PrimaryCategory` and lists the number of categories that are currently unassigned.
