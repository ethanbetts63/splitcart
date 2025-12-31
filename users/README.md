# Users Django App

This app is a core part of the SplitCart backend, responsible for managing users, authentication, and user-specific data like shopping carts and saved store lists. It contains the business logic for cart price optimization, user session management, and customized authentication flows.

## Core Models

-   **`User`**: A custom user model that extends Django's `AbstractUser`.
    -   It uses the `email` field as the unique identifier (`USERNAME_FIELD`) instead of a username.
    -   Includes a `full_name` field.
    -   Managed by a `UserManager` that handles user creation with email.

-   **`Cart`**: Represents a user's shopping list.
    -   Can belong to an authenticated user or an anonymous session (`anonymous_id`).
    -   A user/session can have multiple carts, but only one can be `is_active` at a time. The model's `save()` method enforces this constraint.
    -   Linked to a `SelectedStoreList` to know which stores to use for price comparisons.

-   **`CartItem`**: An item within a `Cart`, linking a `Product` with a specific `quantity`.

-   **`CartSubstitution`**: A potential substitute for a `CartItem`. It links an `original_cart_item` to a `substituted_product` and includes a flag `is_approved` to indicate if the user has accepted the substitution.

-   **`SelectedStoreList`**: A user-defined list of stores.
    -   Can be associated with an authenticated user or an anonymous session.
    -   Users can create and manage multiple lists of stores for different shopping scenarios.

## Key Services & Logic (`users.utils`)

This app contains several key business logic components:

### Cart Optimization (`cart_optimization.py`)

-   This service orchestrates the core "split cart" functionality. The `run_cart_optimization` function is called by the `/api/carts/{pk}/optimize/` endpoint.
-   It calculates costs for multiple scenarios:
    1.  **Baseline Cost**: The total cost if all original items were bought from the cheapest possible single store in the user's list.
    2.  **Optimized (With Substitutes)**: The best possible cost by splitting the cart (including approved substitutes) across a given number of stores.
    3.  **Optimized (No Substitutes)**: The best possible cost by splitting the cart (original items only) across a given number of stores.
-   It returns a detailed breakdown of costs, savings, and a full `shopping_plan` showing which items to buy at which store.

### Anonymous Session Merging (`session_merger.py`)

-   The `merge_anonymous_session` function handles the transfer of an anonymous user's data when they log in or create an account.
-   When a user logs in and provides their `anonymous_id`, this service:
    1.  Finds the active anonymous `Cart` and its associated `SelectedStoreList`.
    2.  Creates new `Cart` and `SelectedStoreList` objects for the authenticated user.
    3.  Copies all items and stores from the anonymous records to the new ones.
    4.  Deletes the old anonymous records.
-   This ensures a seamless user experience, preserving the user's work from their anonymous session.

### Unique Name Generation (`name_generator.py`)

-   A simple utility to generate unique names for `Cart` and `SelectedStoreList` objects. If a user tries to create a list with a name that already exists, it appends an incrementing number (e.g., "My Shopping #2").

## Authentication Flow

The app uses `dj_rest_auth` and `allauth` for authentication, but customizes several parts of the flow:

-   **`CustomRegisterSerializer`**: Modifies the registration endpoint to include the `full_name` field, saving it to the `User` model.
-   **`CustomLoginSerializer`**: Enhances the login process by accepting an `anonymous_id`. If provided, it triggers the `session_merger` service to import the anonymous user's cart.
-   **`CustomAccountAdapter`**: Overrides the default email adapter to send multipart (HTML and text) emails for all authentication-related communication (e.g., password reset). It embeds the SplitCart logo directly into the email for a branded experience.

## API Endpoints & Frontend Interaction

The `users` app provides several API endpoints for the frontend to interact with. These are built with Django Rest Framework.

### Authentication (`/api/auth/`)

-   Handled by `dj_rest_auth` using the custom serializers mentioned above.
-   Endpoints: `/api/auth/login/`, `/api/auth/logout/`, `/api/auth/registration/`, etc.

### Carts (`/api/carts/`)

-   **View:** `CartViewSet`
-   **Description:** Manages all operations related to user shopping carts.
-   **Key Endpoints:**
    -   `GET /api/carts/active/`: Retrieves the user's currently active cart (or creates one). This is the primary endpoint for initializing cart state.
    -   `POST /api/carts/sync/`: Efficiently synchronizes the entire state of a cart's items from the client.
    -   `POST /api/carts/{pk}/optimize/`: Triggers the cart optimization service.

### Store Lists (`/api/store-lists/`)

-   **View:** `SelectedStoreListViewSet`
-   **Description:** Provides full RESTful CRUD operations for managing a user's `SelectedStoreList` objects.

### Nearby Stores (`/api/users/stores/nearby/`)

-   **View:** `NearbyStoreListView`
-   **Description:** Finds stores within a specified radius of a postcode.
-   **URL:** `/api/users/stores/nearby/?postcode=<postcode>&radius=<km>&companies=<company_slugs>`
-   **Action:** Returns a list of `Store` objects and a mapping of which "anchor" stores are used for pricing.