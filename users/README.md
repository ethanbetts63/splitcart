# Users Django App

This app is a core part of the SplitCart backend, responsible for managing users, authentication, and user-specific data like shopping carts. It contains the business logic for cart price optimization, user session management, and customized authentication flows.

## Core Models

-   **`User`**: A custom user model that extends Django's `AbstractUser`.
    -   It uses the `email` field as the unique identifier (`USERNAME_FIELD`) instead of a username.
    -   Includes a `full_name` field.
    -   Managed by a `UserManager` that handles user creation with email.

-   **`Cart`**: Represents a user's shopping list.
    -   Can belong to an authenticated user or an anonymous session (`anonymous_id`).
    -   A user/session can have multiple carts, but only one can be `is_active` at a time. The model's `save()` method enforces this constraint.

-   **`CartItem`**: An item within a `Cart`, linking a `Product` with a specific `quantity`.

-   **`CartSubstitution`**: A potential substitute for a `CartItem`. It links an `original_cart_item` to a `substituted_product` and includes a flag `is_approved` to indicate if the user has accepted the substitution.

## Key Services & Logic (`users.utils`)

This app contains several key business logic components:

### Cart Optimization (`cart_optimization.py`)

-   This service orchestrates the core "split cart" functionality. The `run_cart_optimization` function is called by the `/api/carts/{pk}/optimize/` endpoint.
-   It calculates costs for multiple scenarios:
    1.  **Baseline Cost**: The total cost if all original items were bought at their average company price.
    2.  **Optimized (With Substitutes)**: The best possible cost by splitting the cart (including approved substitutes) across a given number of companies.
    3.  **Optimized (No Substitutes)**: The best possible cost by splitting the cart (original items only) across a given number of companies.
-   It returns a detailed breakdown of costs, savings, and a full `shopping_plan` showing which items to buy from each company.

### Anonymous Session Merging (`session_merger.py`)

-   The `merge_anonymous_session` function handles the transfer of an anonymous user's data when they log in or create an account.
-   When a user logs in and provides their `anonymous_id`, this service:
    1.  Finds the active anonymous `Cart`.
    2.  Creates a new `Cart` for the authenticated user.
    3.  Copies all items from the anonymous record to the new one.
    4.  Deletes the old anonymous record.
-   This ensures a seamless user experience, preserving the user's work from their anonymous session.

### Unique Name Generation (`name_generator.py`)

-   A simple utility to generate unique names for `Cart` objects. If a user tries to create a cart with a name that already exists, it appends an incrementing number (e.g., "My Shopping #2").

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

### Request validation

Every write on `CartViewSet` validates through a serializer in
`users/serializers/cart_action_serializers.py` before anything reaches the
database. `rename` used to assign `cart.name` from `request.data.get('new_name')`
with no check of any kind, and a `cart_id` that was not a UUID reached the ORM
as a raw string; `sync` read nested item and substitution data the same way,
with no bound on how many rows one request could ask for.

The bounds are the model column where one exists (`Cart.name`'s 255) and
otherwise a ceiling on work per request: 300 items, 50 substitutions an item,
999 of anything, 10 optimiser options. A rejected request answers 400 with the
`error` key callers already read, plus an `errors` object carrying the
per-field detail.

`CustomRegisterSerializer` bounds `password1`/`password2` at 128 characters and
`email` at 150. Registration is unauthenticated and hashing is deliberately
expensive, so an unbounded password field is an unbounded amount of CPU per
request; 150 sits below `auth.User.username`'s width, which is what an address
is truncated into.

### Throttling

`users/views/auth_views.py` subclasses dj_rest_auth's views for one reason: to
give each a throttle scope, since they are routed from an include and there is
nowhere else to declare one. Login is `5/minute`, registration and password
reset `5/hour`. `config/urls.py`'s rates and the reasoning behind them are in
`config/settings.py`.

Rate limiting here is a cost control, not a credential control. What should
stop a password guess is account lockout, which does not exist yet — see
[`_docs/convergence/auth-migration.md`](../_docs/convergence/auth-migration.md).

## Tests

`users/tests/` follows the layout in
[`_docs/TESTING.md`](../_docs/TESTING.md): `factories/`, `serializer_tests/`
and `view_tests/`, with an `auth_client` fixture in `conftest.py` that
authenticates the way the live frontend does. Coverage today is the validation
and throttling regressions described above, not the whole app.
