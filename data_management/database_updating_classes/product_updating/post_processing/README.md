# Post-Processing Step Explanations

This document explains the purpose of each file in the `post_processing` directory. These scripts are run by the `UpdateOrchestrator` after all the product data from the inbox files has been processed and saved to the database. Their collective goal is to clean, merge, and maintain the integrity of the product data.

### Order of Operations

The post-processing scripts are run in a specific, deliberate order to ensure data integrity. The sequence is:

1.  **Generators (`...TranslationTableGenerator.py`):** These run first. They act like detectives, scanning the newly updated database to find products and brands that look like duplicates (e.g., 'St Dalfour' and 'St. Dalfour'). They don't change any data; they simply create "instruction files" (translation tables) for the next step.

2.  **Reconcilers (`...Reconciler.py`):** These run second. They are the "movers" that read the instruction files from the generators. They perform the actual merging of duplicate products and brands, re-assigning prices and other linked data to the single canonical record. This step must happen before category and group maintenance, as it can change which products belong to which categories or stores.

3.  **`CategoryCycleManager.py`:** This runs after reconciliation. Merging products that belonged to different categories can sometimes create illogical loops in the category hierarchy (e.g., 'Snacks' -> 'Chips' -> 'Snacks'). This utility cleans up any such cycles.

4.  **`GroupMaintenanceOrchestrator.py`:** This is the final cleanup step. It ensures that store groupings are correct after all the underlying product data has been settled and reconciled.

### `product_enricher.py`

*   **Purpose:** This file contains a single utility class, `ProductEnricher`, which is not a standalone process but a helper used by the `ProductReconciler`.
*   **Functionality:** Its main job is to merge the data from a duplicate product into a canonical (master) product. When the `ProductReconciler` decides that "Product B" is a duplicate of "Product A", it uses the `ProductEnricher` to copy over valuable information. It intelligently merges data by:
    *   Filling in blank fields on the canonical product (like `barcode` or `url`) if the duplicate has data for them.
    *   Combining lists of variations (like `sizes` and `normalized_name_brand_size_variations`) to ensure no information is lost.
    *   This ensures that when the duplicate product is deleted, all its useful information has been transferred to the master product.

### `brand_reconciler.py`

*   **Purpose:** To find and merge duplicate `ProductBrand` records in the database.
*   **Trigger:** It runs after the `BrandTranslationTableGenerator` creates a "dictionary" of known brand synonyms.
*   **Functionality:** It reads the translation table (e.g., `{'mc cain': 'McCain'}`). For each entry, it identifies the "duplicate" brand ('mc cain') and the "canonical" brand ('McCain'). It then performs a merge by:
    1.  Finding all `Product`s that are linked to the duplicate brand and re-assigning them to the canonical brand.
    2.  Merging the `name_variations` from the duplicate brand into the canonical brand's list.
    3.  Deleting the now-empty duplicate brand record.
    *   This process keeps the brand data clean and ensures that different spellings of the same brand are all linked to a single master record.

### `product_reconciler.py`

*   **Purpose:** This is the product-level equivalent of the `brand_reconciler`. It finds and merges duplicate `Product` records.
*   **Trigger:** It runs after the `ProductTranslationTableGenerator` creates a dictionary of product name synonyms.
*   **Functionality:** It reads the product translation table to identify duplicate/canonical pairs. For each pair, it performs a merge:
    1.  It uses the `ProductEnricher` to copy all useful field data from the duplicate product to the canonical one.
    2.  It finds all `Price` records linked to the duplicate product and re-assigns them to the canonical product. This step includes logic to handle conflicts, keeping only the most recently scraped price if both products had a price at the same store.
    3.  It deletes the now-empty duplicate product record.
    *   This is a critical step for data quality, ensuring that different variations of a product name resolve to a single, master product entry.

### `category_cycle_manager.py`

*   **Purpose:** To maintain the health of the category hierarchy by detecting and fixing circular dependencies.
*   **Functionality:** A circular dependency (or cycle) would be if 'Snacks' is a parent of 'Chips', and 'Chips' is also a parent of 'Snacks'. This would cause infinite loops in any code trying to traverse the category tree. This manager runs for each company and:
    1.  Traverses the category tree for that company.
    2.  Keeps track of the path it has taken.
    3.  If it encounters a category that is already in its current path, it identifies this as a cycle.
    4.  It then "prunes" the cycle by removing the problematic parent-child link, ensuring the category hierarchy remains a valid tree structure.

### `group_maintenance_orchestrator.py`

*   **Purpose:** This is the final step in post-processing. It runs a two-phase process to ensure the health of `StoreGroup` entities after all product and category changes have been finalized.
*   **Functionality:**
    *   **Phase 1 (Internal Health Check)**: Compares member stores within each group to their group's anchor store and ejects any that no longer have a matching product set.
    *   **Phase 2 (Inter-Group Merging)**: Compares the anchors of different groups and merges any groups that are found to be identical, reducing redundancy.
