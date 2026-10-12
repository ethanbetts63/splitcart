# Users Django App

This app is a core part of the SplitCart backend, responsible for managing users, authentication, and user-specific data like shopping carts. It contains the business logic for cart price optimization, user session management, and customized authentication flows.

## Core Models

- **`User`**: A custom user model that extends Django's `AbstractUser`.
  - It uses the `email` field as the unique identifier (`USERNAME_FIELD`) instead of a username.
  - Includes a `full_name` field.
  - Managed by a `UserManager` that handles user creation with email.

- **`Cart`**: Represents a user's shopping list.
  - Can belong to an authenticated user or an anonymous session (`anonymous_id`).
  - A user/session can have multiple carts, but only one can be `is_active` at a time. The model's `save()` method enforces this constraint.

- **`CartItem`**: An item within a `Cart`, linking a `Product` with a specific `quantity`.

- **`CartSubstitution`**: A potential substitute for a `CartItem`. It links an `original_cart_item` to a `substituted_product` and includes a flag `is_approved` to indicate if the user has accepted the substitution.

## Key Services & Logic (`users.utils`)

This app contains several key business logic components:

### Cart Optimization (`cart_optimization.py`)

- This service orchestrates the core "split cart" functionality. The `run_cart_optimization` function is called by the `/api/carts/{pk}/optimize/` endpoint.
- It calculates costs for multiple scenarios:
  1.  **Baseline Cost**: The total cost if all original items were bought at their average company price.
  2.  **Optimized (With Substitutes)**: The best possible cost by splitting the cart (including approved substitutes) across a given number of companies.
  3.  **Optimized (No Substitutes)**: The best possible cost by splitting the cart (original items only) across a given number of companies.
- It returns a detailed breakdown of costs, savings, and a full `shopping_plan` showing which items to buy from each company.

### Anonymous Session Merging (`session_merger.py`)

- The `merge_anonymous_session` function handles the transfer of an anonymous user's data when they log in or create an account.
- When a user logs in and provides their `anonymous_id`, this service:
  1.  Finds the active anonymous `Cart`.
  2.  Creates a new `Cart` for the authenticated user.
  3.  Copies all items from the anonymous record to the new one.
  4.  Deletes the old anonymous record.
- This ensures a seamless user experience, preserving the user's work from their anonymous session.

### Unique Name Generation (`name_generator.py`)

- A simple utility to generate unique names for `Cart` objects. If a user tries to create a cart with a name that already exists, it appends an incrementing number (e.g., "My Shopping #2").

## Authentication

Sessions are `freetheplatform.auth`'s: an access and a rotating refresh token in
HttpOnly cookies (`splitcart_access`, `splitcart_refresh`), revoked by
blacklisting, with account lockout, password change and password reset. Its
contract is [`../../freetheplatform/_docs/apps/auth.md`](../../freetheplatform/_docs/apps/auth.md).
What is splitcart's:

- **`principal.py`**: what `/api/me/` and login answer with — id, email,
  full name, and `role`, always `"shopper"`. Nothing is gated on it.
- **`credentials.py`**: maps the login form's `email` to both names simplejwt
  and the package read it under, resolved to the stored spelling ignoring case.
- **`notifications.py`**: the reset email, linking to the frontend's
  `/reset-password/<uid>/<token>/`, and the lockout alert to `ADMIN_EMAIL`.
- **`views/auth_views.py`**: `LoginView` puts two things in front of the
  package's — a bound on the body before anything is hashed, and the
  anonymous cart handed to the account once the login succeeds.
  `RegisterView` is the package's missing door: it creates the account, hands
  over the cart, and ends signed in the same way.

## API Endpoints & Frontend Interaction

The `users` app provides several API endpoints for the frontend to interact with. These are built with Django Rest Framework.

### Authentication (`/api/`)

| Path                                                                                                                     | View                                          |
| ------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------- |
| `POST token/`                                                                                                            | `LoginView` (splitcart's, over the package's) |
| `POST register/`                                                                                                         | `RegisterView`                                |
| `POST token/refresh/`, `token/logout/`, `GET me/`, `POST password/change/`, `password/reset/`, `password/reset/confirm/` | `freetheplatform.auth`, as it comes           |

The browser reaches these through the frontend's same-origin `/api/*` rewrite,
and login, signup and the reset forms through Server Actions on the frontend's
server. Nothing calls Django cross-origin, so there is no CORS.

### Carts (`/api/carts/`)

- **View:** `CartViewSet`
- **Description:** Manages all operations related to user shopping carts.
- **Key Endpoints:**
  - `GET /api/carts/active/`: Retrieves the user's currently active cart (or creates one). This is the primary endpoint for initializing cart state.
  - `POST /api/carts/sync/`: Efficiently synchronizes the entire state of a cart's items from the client.
  - `POST /api/carts/{pk}/optimize/`: Triggers the cart optimization service.

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

`RegisterSerializer` and `LoginRequestSerializer` bound every field by kind from
`freetheplatform.security.bounds` — `password` at 128, `email` at 150, `name` at 120. Both doors are unauthenticated and hashing is deliberately expensive, so an
unbounded password field is an unbounded amount of CPU per request.

### Throttling

Login is `5/minute`, registration and password reset `5/hour`; the rates and
the reasoning behind them are in `config/settings.py`. Every route declares a
scope, and `ftp_security.E006` refuses to start one that does not.

Rate limiting here is a cost control. What stops a password guess is the
package's account lockout: ten consecutive failures lock an account for fifteen
minutes, and `ADMIN_EMAIL` is told at five.

## Tests

`users/tests/` follows the layout in
[`_docs/TESTING.md`](../_docs/TESTING.md): `factories/`, `model_tests/`,
`serializer_tests/`, `util_tests/` and `view_tests/`, with `auth_client` and
`anonymous_client` fixtures in `conftest.py` that authenticate the way the live
frontend and a signed-out browser do.

Two things in here are worth knowing before changing a test:

- **Every cart route is asked who may reach it.** One account against another's
  rows, a signed-out browser against an account's, and two signed-out browsers
  against each other's. The queryset is the only thing keeping them apart, and
  `CartViewSet` carries `never_cache` because the whole-site cache middleware in
  `config/settings.py` was handing one shopper's cart to the next caller.
- **The anonymous-cart merge is pinned three times.**
  `util_tests/test_session_merger.py` covers the behaviour as a function,
  `view_tests/test_login.py` and `serializer_tests/test_register_serializer.py`
  each door, and `view_tests/test_anonymous_cart_at_both_doors.py` that the two
  doors agree. That last one names no view or serializer, which is how it
  survived the move off dj-rest-auth unchanged in substance.
- **`tests/sessions.py` signs a client in** by putting tokens in its cookie jar,
  the state a login leaves behind, without a round trip through the login view.
