# API App Migration Plan

This document outlines the plan to dismantle the `api` Django app and merge its components into other applications within the project.

## Guiding Principles

- **Co-location:** Views and serializers should be located within the same app as the models they primarily interact with.
- **App Responsibilities:** Each app should have a clear and distinct responsibility.
  - `products`: Manages `Product` and related models, and their lifecycle.
  - `companies`: Manages `Company`, `Store`, and related models.
  - `users`: Manages `User`, `Cart`, and `SelectedStoreList` models.
  - `data_management`: Handles cross-cutting data concerns like import/export, and models that don't fit neatly elsewhere (like `FAQ`, `PillarPage`).
- **New Structure:** API-specific code within apps will be organized into `views/api/` subdirectories and `serializers/` and `utils/` subdirectories, to keep it separate from other app logic.

---

## Migration Plan by Target App

### 1. To `products` app

- **Reasoning:** All product-centric logic.
- **New Files/Directories:**
  - `products/serializers/`
  - `products/views/api/`
  - `products/utils/`

| File from `api` app                                        | New Location                                       | Notes                                          |
| ---------------------------------------------------------- | -------------------------------------------------- | ---------------------------------------------- |
| `serializers/product_serializer.py`                        | `products/serializers/product_serializer.py`       | New directory and file.                        |
| `serializers/product_substitution_serializer.py`           | `products/serializers/product_substitution_serializer.py`| New file.                                      |
| `serializers/price_serializer.py`                          | `products/serializers/price_serializer.py`         | New file.                                      |
| `serializers/bargain_stats_serializer.py`                  | `products/serializers/bargain_stats_serializer.py` | New file.                                      |
| `views/frontend_views/product_list_view.py`                | `products/views/api/product_list_view.py`          | New directory and file.                        |
| `views/frontend_views/product_detail_view.py`              | `products/views/api/product_detail_view.py`        | New file.                                      |
| `views/frontend_views/bargain_carousel_view.py`            | `products/views/api/bargain_carousel_view.py`      | New file.                                      |
| `views/frontend_views/product_substitute_list_view.py`     | `products/views/api/product_substitute_list_view.py`| New file.                                    |
| `views/frontend_views/bargain_stats_view.py`               | `products/views/api/bargain_stats_view.py`         | New file.                                      |
| `views/product_barcode_view.py`                            | `products/views/api/product_barcode_view.py`       | New file.                                      |
| `utils/bargain_utils.py`                                   | `products/utils/bargain_utils.py`                  | New directory and file.                        |
| `utils/product_ordering.py`                                | `products/utils/product_ordering.py`               | New file.                                      |

### 2. To `companies` app

- **Reasoning:** Company and store-related logic.
- **New Files/Directories:**
  - `companies/serializers/`
  - `companies/views/api/`

| File from `api` app                                        | New Location                                       | Notes                                                          |
| ---------------------------------------------------------- | -------------------------------------------------- | -------------------------------------------------------------- |
| `serializers/company_serializer.py`                        | `companies/serializers/company_serializer.py`      | New directory and file.                                        |
| `serializers/store_serializer.py`                          | `companies/serializers/store_serializer.py`        | New file.                                                      |
| `serializers/postcode_serializer.py`                       | `companies/serializers/postcode_serializer.py`     | New file.                                                      |
| `serializers/primary_category_serializer.py`               | `companies/serializers/primary_category_serializer.py`| New file. Also move `PrimaryCategory` model? (See note)        |
| `views/frontend_views/store_list_views/nearby_store_list_view.py` | `companies/views/api/nearby_store_list_view.py`    | New directory and file.                                        |
| `views/frontend_views/postcode_search_view.py`             | `companies/views/api/postcode_search_view.py`      | New file.                                                      |
| `views/company_list_view.py`                               | `companies/views/api/company_list_view.py`         | New file.                                                      |

**Note:** `PrimaryCategory` is currently in `companies.models`, so its serializer belongs here. We should confirm if this is the best long-term home for this model.

### 3. To `users` app

- **Reasoning:** User, cart, and authentication-related logic.
- **New Files/Directories:**
  - `users/serializers/`
  - `users/views/api/`

| File from `api` app                                        | New Location                                       | Notes                                          |
| ---------------------------------------------------------- | -------------------------------------------------- | ---------------------------------------------- |
| `serializers/cart_serializer.py`                           | `users/serializers/cart_serializer.py`             | New directory and file.                        |
| `serializers/cart_item_serializer.py`                      | `users/serializers/cart_item_serializer.py`        | New file.                                      |
| `serializers/cart_substitution_serializer.py`              | `users/serializers/cart_substitution_serializer.py`| New file.                                      |
| `serializers/selected_store_list_serializer.py`            | `users/serializers/selected_store_list_serializer.py`| New file.                                    |
| All files in `views/frontend_views/cart_views/`            | `users/views/api/cart_views/`                      | Move files to this new directory.              |
| All files in `views/frontend_views/store_list_views/`      | `users/views/api/store_list_views/`                | Move store list management with user lists.    |
| `views/frontend_views/cart_optimization_view.py`           | `users/views/api/cart_optimization_view.py`        | New file.                                      |
| `views/frontend_views/cart_export_view.py`                 | `users/views/api/cart_export_view.py`              | New file.                                      |
| `views/frontend_views/initial_setup_view.py`               | `users/views/api/initial_setup_view.py`            | New file.                                      |

### 4. To `data_management` app

- **Reasoning:** For data import/export tasks and content models that don't fit elsewhere.
- **New Files/Directories:**
  - `data_management/serializers/`
  - `data_management/views/api/`

| File from `api` app                               | New Location                                           | Notes                                                        |
| ------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------ |
| `views/product_file_upload_view.py`               | `data_management/views/api/product_file_upload_view.py`| New directory and file.                                      |
| `views/gs1_file_upload_view.py`                   | `data_management/views/api/gs1_file_upload_view.py`    | New file.                                                    |
| `views/store_file_upload_view.py`                 | `data_management/views/api/store_file_upload_view.py`  | New file.                                                    |
| `views/category_links_file_upload_view.py`        | `data_management/views/api/category_links_file_upload_view.py` | New file.                                                  |
| `views/substitutions_file_upload_view.py`         | `data_management/views/api/substitutions_file_upload_view.py` | New file.                                                |
| `views/product_translation_file_view.py`          | `data_management/views/api/product_translation_file_view.py` | New file.                                                |
| `views/brand_translation_file_view.py`            | `data_management/views/api/brand_translation_file_view.py` | New file.                                                |
| `views/import_semantic_data_view.py`              | `data_management/views/api/import_semantic_data_view.py` | New file.                                                |
| `views/gs1_views.py`                              | `data_management/views/api/gs1_views.py`               | New file.                                                    |
| `views/export_categories_view.py`                 | `data_management/views/api/export_categories_view.py`  | New file.                                                    |
| `views/export_categories_with_products_view.py`   | `data_management/views/api/export_categories_with_products_view.py`| New file.                                                |
| `views/export_products_view.py`                   | `data_management/views/api/export_products_view.py`    | New file.                                                    |
| `views/export_prices_view.py`                     | `data_management/views/api/export_prices_view.py`      | New file.                                                    |
| `views/export_anchor_stores_view.py`              | `data_management/views/api/export_anchor_stores_view.py`| New file.                                                  |
| `views/export_category_links_view.py`             | `data_management/views/api/export_category_links_view.py`| New file.                                                  |
| `views/export_stores_view.py`                     | `data_management/views/api/export_stores_view.py`      | New file.                                                    |
| `serializers/faq_serializer.py`                   | `data_management/serializers/faq_serializer.py`        | New directory and file. Also move `Faq` model to `data_management.models`. |
| `serializers/pillar_page_serializer.py`           | `data_management/serializers/pillar_page_serializer.py`| New file. Also move `PillarPage` model.                     |
| `views/frontend_views/faq_list_view.py`           | `data_management/views/api/faq_list_view.py`           | New file.                                                    |
| `views/frontend_views/pillar_page_view.py`        | `data_management/views/api/pillar_page_view.py`        | New file.                                                    |
| `views/scheduler_view.py`                         | `data_management/views/api/scheduler_view.py`          | New file.                                                    |

### 5. To `splitcart` (main project) app

- **Reasoning:** Project-wide API configuration.

| File from `api` app | New Location               | Notes                           |
| ------------------- | -------------------------- | ------------------------------- |
| `permissions.py`    | `splitcart/permissions.py` | New file for global permissions. |
| `exception_handler.py` | `splitcart/exception_handler.py` | New file. Update in `settings.py`. |
| `cache.py`          | `splitcart/cache.py`       | New file. Review usage.         |

---

## Final Steps

1.  **URL Configuration:** After moving all views, the main `splitcart/urls.py` will need to be updated to include the new API URL patterns from `products/urls.py`, `users/urls.py`, `companies/urls.py`, and `data_management/urls.py`. The `api/urls.py` will be deleted.
2.  **Settings:** Update `settings.py` to remove the `api` app from `INSTALLED_APPS`. Update the `REST_FRAMEWORK` settings if `exception_handler` path changes.
3.  **Delete `api` app:** Once all files are moved and the project is tested, the `api` directory can be deleted.