# Splitcart Testing Strategy

This document outlines the testing strategy for the Splitcart backend. For
scraping specifically — what gets mocked, where, and why no test ever reaches a
supermarket — see [`scraper_testing.md`](scraper_testing.md).

The cross-repository rules are in
[`../../freetheplatform/_docs/testing-standard-backend.md`](../../freetheplatform/_docs/testing-standard-backend.md).
This file records what splitcart actually does; where the two disagree, the
shared standard is the target and
[`convergence/testing.md`](convergence/testing.md) tracks the gap.

## 1. Core Technology Stack

Our testing suite is built on a foundation of powerful and widely-used Python testing libraries:

- **`pytest`**: The core test runner. We use `pytest` for its powerful fixture model, expressive `assert` statements, and rich plugin ecosystem.
- **`pytest-django`**: This essential plugin integrates `pytest` with Django. It provides the `@pytest.mark.django_db` marker to enable database access for tests, as well as helpful fixtures like `client` for testing views.
- **`factory_boy`**: We use `factory_boy` to create test data. Instead of manually creating model instances in each test, we define "factories" that can generate valid model instances with sensible defaults. This makes our tests cleaner, more readable, and easier to maintain.
- **`Faker`**: This library is used within `factory_boy` to generate realistic-looking fake data (names, dates, sentences, etc.).

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

Not every app has every layer. What exists today:

| App         | Test layers present                                                                                                                                                                                                  |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `companies` | `factories/`, `model_tests/`, `serializer_tests/`, `view_tests/`                                                                                                                                                     |
| `products`  | `factories/`, `model_tests/`, `util_tests/`, `view_tests/`                                                                                                                                                           |
| `pipeline`  | `command_tests/`, `model_tests/`, `serializer_tests/`, `util_tests/`, `view_tests/`, plus a `conftest.py`                                                                                                            |
| `scraping`  | `util_tests/` only — the app is model-free, so there is nothing else to test                                                                                                                                         |
| `users`     | **none.** There is no `users/tests/` directory at all, and that app owns authentication, the cart viewset and the optimisation entry point. Closing this is [`convergence/testing.md`](convergence/testing.md) TS-3. |

### Rationale for this structure:

- **Separation of Concerns:** It cleanly separates tests by what they are testing (models, views, serializers, etc.), making it easy to find relevant tests.
- **Scalability:** This structure will scale well as the application grows.
- **Discoverability:** `pytest` can automatically discover tests in any file prefixed with `test_`.

## 3. Testing Philosophy

- **Test What Matters:** We focus on testing our own code, not the functionality of Django or other libraries. We test our custom logic in `save()` methods, view logic, and serializer validation.
- **Use Factories for Data:** We always use factories to create test data, which makes tests cleaner and more maintainable.
- **Clear and Descriptive Test Names:** Test names should clearly describe what they are testing (e.g., `test_notification_start_date_calculation`).
- **Aim for a Healthy Mix:** We write both unit tests (testing small pieces of code in isolation) and integration tests (testing how different parts of the application work together).

## 4. Shared Test Fixtures (`conftest.py`)

There is **no root `conftest.py`**. The only one in the repository is
`pipeline/tests/conftest.py`, so its fixtures are visible to `pipeline/tests`
and nowhere else. It defines exactly one:

### `mock_command`

A `MagicMock` standing in for a Django management command, with
`style.SUCCESS`/`style.WARNING`/`style.ERROR` wired to return their argument
unchanged. The pipeline's service classes take a `command` so they can write
progress to `stdout`; this lets a unit test construct one without a real
command instance and without swallowing the messages.

```python
def test_generator_reports_progress(mock_command):
    Generator(command=mock_command).run()
    assert mock_command.stdout.write.called
```

Everything else is a local fixture or a factory. If a fixture starts being
copied between apps, promote it to a root `conftest.py` — which would then be
the first one.

## 5. Fixing a failing test

Follow
[`../../freetheplatform/_docs/testing-standard-backend.md`](../../freetheplatform/_docs/testing-standard-backend.md#fixing-a-failing-test).
The short version: work out whether the test or the code is wrong before
changing either, and never weaken an assertion to get green. A file you find to
be dead code is worth saying out loud rather than leaving in place.
