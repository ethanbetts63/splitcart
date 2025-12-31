# Users Django App

This app is a core part of the SplitCart backend, responsible for managing users, authentication, and user-specific data like shopping carts and saved store lists.

## Core Models

-   **`User`**: Extends Django's default user model.
-   **`Cart`**: Represents a user's shopping list. A user can have multiple carts, but only one can be `is_active`. Carts can belong to an authenticated user or an anonymous user session.
-   **`CartItem`**: An item within a `Cart`, linked to a `Product`.
-   **`CartSubstitution`**: A potential substitute for a `CartItem`.
-   **`SelectedStoreList`**: A user-defined list of stores to use for price comparisons.

## API Endpoints & Frontend Interaction

The `users` app provides several API endpoints for the frontend to interact with. These are built with Django Rest Framework, primarily using ViewSets for a consistent RESTful interface.

### Authentication

User registration and authentication (login/logout) are handled by the `dj_rest_auth` library, which provides its own standard endpoints (e.g., `/api/auth/login/`).

### Carts (`/api/carts/`)

-   **View:** `CartViewSet`
-   **Description:** Manages all operations related to user shopping carts.

#### Key Endpoints:

-   `GET /api/carts/`
    -   **Action:** Lists all carts belonging to the authenticated user.

-   `POST /api/carts/`
    -   **Action:** Creates a new, empty cart. Automatically sets the new cart as the active one.

-   `GET /api/carts/active/`
    -   **Action:** Retrieves the user's currently active cart. If no active cart exists, one is created automatically. This is the primary endpoint for the frontend to initialize the cart state.

-   `POST /api/carts/sync/`
    -   **Action:** Synchronizes the entire state of a cart's items from the client. The frontend uses this with a "debounce" mechanism, sending the full list of items after a period of user inactivity. This is more efficient than making individual API calls for each item added or removed.
    -   **Body:** `{ "cart_id": "...", "items": [{ "product_id": ..., "quantity": ... }] }`

-   `POST /api/carts/{pk}/optimize/`
    -   **Action:** Triggers the price optimization logic for the specified cart. This performs the "split cart" calculation across the user's selected stores.

-   `DELETE /api/carts/{pk}/`
    -   **Action:** Deletes a specific cart.

### Cart Items (`/api/carts/{cart_pk}/items/`)

-   **View:** `CartItemViewSet`
-   **Description:** Manages the items within a specific cart. The frontend does not use these endpoints directly anymore, preferring the more efficient `/api/carts/sync/` endpoint.

### Cart Item Substitutions (`/api/carts/{cart_pk}/items/{item_pk}/substitutions/`)

-   **View:** `CartSubstitutionViewSet`
-   **Description:** Manages the approval and quantity of product substitutions for a specific cart item.

#### Key Endpoints:

-   `PATCH /api/carts/{cart_pk}/items/{item_pk}/substitutions/{pk}/`
    -   **Action:** Updates a substitution. Used by the frontend on the substitution review page to approve/un-approve a substitute.
    -   **Body:** `{ "is_approved": true/false, "quantity": ... }`

### Store Lists (`/api/store-lists/`)

-   **View:** `SelectedStoreListViewSet`
-   **Description:** Manages user-created lists of stores.
-   **Actions:** Provides standard RESTful `GET`, `POST`, `PUT`, `DELETE` operations for managing store lists.
