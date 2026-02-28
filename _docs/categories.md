# Category System Overview

The SplitCart category system is designed to normalize and aggregate messy, store-specific product data into a clean, user-friendly browsing experience. It operates on a three-tier hierarchy:

## 1. Categories (Raw Data)
*   **What they are:** These are the raw, unstandardized categories directly scraped from the supermarkets (e.g., "Woolworths Biscuits", "Coles Cookies & Crackers", "Aldi Sweet Treats").
*   **Source:** The web scrapers populate the `Category` model.
*   **Characteristics:** They are numerous, inconsistent, and often change names.

## 2. Primary Categories (Standardized)
*   **What they are:** This is the internal standard. Multiple raw Categories are mapped to a single, clean Primary Category.
*   **Example:** "Woolworths Biscuits", "Coles Cookies", and "Aldi Sweet Treats" are all mapped to the **Snacks** Primary Category.
*   **Definition:** Defined in `splitcart/data_management/data/category_mappings.py`.
*   **Generation:** The `PrimaryCategoriesGenerator` reads the mappings and creates standardized `PrimaryCategory` objects. It then links every raw `Category` to its corresponding `PrimaryCategory`.
*   **Usage:** Used in the scrolling "Category Bar" on the frontend.

## 3. Pillar Pages (Aggregated)
*   **What they are:** These are high-level, thematic "Super Categories" designed for the main navigation and SEO landing pages. They group multiple Primary Categories together.
*   **Example:** The **Snacks & Sweets** Pillar Page aggregates the **Snacks**, **Chocolate**, and **Lollies** Primary Categories.
*   **Definition:** Defined in `splitcart/data_management/data/pillar_pages.jsonl`.
*   **Generation:** The `PillarsGenerator` reads the JSONL file and creates `PillarPage` objects. It links the specified `PrimaryCategory` objects to the Pillar.
*   **Usage:** Used in the "Browse Categories Section" on the homepage.

---

## Data Flow Summary
1.  **Ingest:** Scrapers bring in raw **Categories**.
2.  **Normalize:** `PrimaryCategoriesGenerator` maps raw Categories -> **Primary Categories**.
3.  **Aggregate:** `PillarsGenerator` groups Primary Categories -> **Pillar Pages**.
4.  **Display:**
    *   **Category Bar:** Displays Primary Categories directly.
    *   **Home Page:** Displays links to Pillar Pages.
