# FutureReminder Testing Strategy

This document outlines the testing strategy for the FutureReminder project.

## 1. Core Technology Stack

Our testing suite is built on a foundation of powerful and widely-used Python testing libraries:

*   **`pytest`**: The core test runner. We use `pytest` for its powerful fixture model, expressive `assert` statements, and rich plugin ecosystem.
*   **`pytest-django`**: This essential plugin integrates `pytest` with Django. It provides the `@pytest.mark.django_db` marker to enable database access for tests, as well as helpful fixtures like `client` for testing views.
*   **`factory_boy`**: We use `factory_boy` to create test data. Instead of manually creating model instances in each test, we define "factories" that can generate valid model instances with sensible defaults. This makes our tests cleaner, more readable, and easier to maintain.
*   **`Faker`**: This library is used within `factory_boy` to generate realistic-looking fake data (names, dates, sentences, etc.).

## 2. Test Directory Structure

To keep our tests organized and scalable, we follow a consistent directory structure within each Django app.

```
<app_name>/
├── tests/
│   ├── __init__.py
│   ├── factories/
│   │   ├── __init__.py
│   │   ├── <model_name>_factory.py
│   │   └── ...
│   ├── model_tests/
│   │   ├── __init__.py
│   │   ├── test_<model_name>_model.py
│   │   └── ...
│   ├── view_tests/
│   │   ├── __init__.py
│   │   ├── test_<view_name>_view.py
│   │   └── ...
│   ├── serializer_tests/
│   │   ├── __init__.py
│   │   ├── test_<serializer_name>_serializer.py
│   │   └── ...
│   └── util_tests/
│       ├── __init__.py
│       ├── test_<util_name>.py
│       └── ...
└── ...
```

### Rationale for this structure:

*   **Separation of Concerns:** It cleanly separates tests by what they are testing (models, views, serializers, etc.), making it easy to find relevant tests.
*   **Scalability:** This structure will scale well as the application grows.
*   **Discoverability:** `pytest` can automatically discover tests in any file prefixed with `test_`.

## 3. Testing Philosophy

*   **Test What Matters:** We focus on testing our own code, not the functionality of Django or other libraries. We test our custom logic in `save()` methods, view logic, and serializer validation.
*   **Use Factories for Data:** We always use factories to create test data, which makes tests cleaner and more maintainable.
*   **Clear and Descriptive Test Names:** Test names should clearly describe what they are testing (e.g., `test_notification_start_date_calculation`).
*   **Aim for a Healthy Mix:** We write both unit tests (testing small pieces of code in isolation) and integration tests (testing how different parts of the application work together).

## 4. Shared Test Fixtures (`conftest.py`)

To promote reusable test code and solve common setup problems, we use a `conftest.py` file in the project's root directory. `pytest` automatically discovers this file and makes its fixtures available to all tests in the project.

### `drf_request_factory`

Many of our serializers require an authenticated user from the request context to function correctly. Directly testing these serializers requires creating a valid `rest_framework.request.Request` object with an authenticated user attached.

The `drf_request_factory` fixture provides a simple and reliable way to do this.

**Usage:**

```python
def test_my_serializer(drf_request_factory):
    # Create a user for the test
    user = UserFactory()

    # Use the fixture to create a DRF request with the user authenticated
    request = drf_request_factory(user=user)

    # Now you can pass this request in the serializer's context
    serializer = MySerializer(
        data={...},
        context={'request': request}
    )
    ...
```

This fixture handles the complexity of creating a valid request object, ensuring our serializer unit tests are clean, readable, and correctly simulate an authenticated context.


### Notes for AI ###
* In the event of a failing test. You should read all relevant files and assess. If you think that the test is at fault then fix the test. If you think that the project code is at fault. Relay your find to the dev but do not touch any code without approval.