# Splitcart Testing Strategy

This document outlines the testing strategy for the Splitcart backend. For
scraping specifically — what gets mocked, where, and why no test ever reaches a
supermarket — see [`scraper_testing.md`](scraper_testing.md).

The cross-repository rules are in
[`../../freetheplatform/_docs/testing-standard-backend.md`](../../freetheplatform/_docs/testing-standard-backend.md).
This file records what splitcart actually does; where the two disagree, the
shared standard is the target and
[`convergence/testing.md`](convergence/testing.md) tracks the gap.

## Running the suite

```
./venv/Scripts/python -m pytest                    # everything
./venv/Scripts/python -m pytest users              # one app
./venv/Scripts/python -m pytest users/tests/view_tests/test_cart_viewset.py
```

Model changes also need:

```
DJANGO_SETTINGS_MODULE=settings_test ./venv/Scripts/python manage.py makemigrations --check --dry-run
```

The settings module has to be named there because `config.settings` loads the
MySQL backend on import and `mysqlclient` is not installed — see below.

### Building the virtualenv

`requirements_dev.txt` is the full local set and will not install as written on
a machine without a C compiler and a Python it has wheels for. Two packages in
it are the reason, and neither is needed to run the suite:

| Package                                             | Why it is skipped                                                                                                                        |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `mysqlclient`                                       | C extension. No wheel for Python 3.14; building it needs the MSVC build tools. The suite does not use MySQL — see below.                 |
| `torch`, `transformers`, `sentence-transformers`, … | The ML half of substitution generation. No wheels for Python 3.14, and roughly 2.5 GB when there are. Only `generate --subs` needs them. |

Everything else installs from the pinned versions, with one caveat: the
analysis packages (`numpy`, `pandas`, `matplotlib`) have no wheels for Python
3.14 at the versions the lockfile pins either, so the venv here carries newer
ones. They are imported only by `pipeline/analysers/`, which has no tests. On
the Python 3.12 the lockfile was resolved for -- the version PythonAnywhere
runs -- the pins install as written.

Without the ML half, four
tests in `pipeline/tests/command_tests/test_generate_command.py` fail: they
patch `pipeline.utils.generation_utils.substitutions_generator`, and the module
cannot be imported without `torch`. The patch target is correct and the tests
are right; they simply need the dependency. **Four failures with
`No module named 'torch'` in the traceback are expected on a machine without
the ML stack. Any other failure is not.**

### Which database the tests run against

`pytest.ini` names `settings_test`, not `config.settings`. That module is
`config.settings` with two changes: a fallback `SECRET_KEY` so a clone without a
`.env` can still run, and an in-memory SQLite database in place of MySQL.

MySQL is the only engine the site runs on, and the suite not using it is a
deliberate trade rather than an oversight. Creating a test database means
`CREATE DATABASE test_splitcart`, and the MySQL user on the development
machines is granted only `test_allbikes`, `test_bloomprint` and
`test_freethedesk`. Without that grant — and without `mysqlclient`, above —
there is no version of "the tests pass" anyone can check.

What it costs is the MySQL-specific half of persistence: collation and case
sensitivity on the unique `email` column, silent truncation under a non-strict
`sql_mode`, index-length limits, and any migration SQLite accepts and MySQL
rejects. Bounds that used to rely on MySQL truncating an over-long value are
now enforced in the serializers, which is where they belong.

To run against the real engine once a grant exists:

```
SPLITCART_TEST_DB=mysql ./venv/Scripts/python -m pytest
```

That needs `mysqlclient` installed and `CREATE`/`DROP` on `test_<DB_NAME>`.
**Granting it is an outstanding manual step**, and until someone does, no run
here has exercised MySQL.

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

| App         | Test layers present                                                                                                                                       |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `companies` | `factories/`, `model_tests/`, `serializer_tests/`, `view_tests/`                                                                                          |
| `config`    | `tests/` — one module, for the root URLconf. The project package has no models or serializers to mirror.                                                  |
| `products`  | `factories/`, `model_tests/`, `serializer_tests/`, `util_tests/`, `view_tests/`                                                                           |
| `pipeline`  | `command_tests/`, `model_tests/`, `serializer_tests/`, `util_tests/`, `view_tests/`, plus a `conftest.py`                                                 |
| `scraping`  | `util_tests/` only — the app is model-free, so there is nothing else to test. The scraper classes are tested here too rather than in a `scrapers/` layer. |
| `users`     | `factories/`, `model_tests/`, `serializer_tests/`, `util_tests/`, `view_tests/`, plus a `conftest.py`                                                     |

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

There are three, and they nest: the root one is visible everywhere, and an
app's own adds to it.

### Root `conftest.py` — every app

| Fixture               | What it is for                                                                                                              |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `api_client`          | A DRF `APIClient`. pytest-django's built-in `client` speaks sessions, and every authenticated route here is token auth.     |
| `drf_request_factory` | Builds an authenticated `rest_framework.request.Request`, for serializers that resolve the current user from their context. |
| `empty_caches`        | Autouse. Clears the throttle cache and the page cache between tests, so no test inherits another's rate-limit history.      |

```python
def test_my_serializer(drf_request_factory):
    request = drf_request_factory(user=UserFactory())
    serializer = MySerializer(data={...}, context={'request': request})
```

`empty_caches` is not optional bookkeeping. Throttle counters live in the
`throttling` cache and survive the per-test database rollback, so without it a
test that signs in fails because five earlier ones already spent the
five-per-minute login rate — and it fails only in a full run, which is the
worst way to find out.

**Two of freethedesk's root fixtures are deliberately absent.** It holds an OS
lock for the length of a run, and refuses to start against a test database
missing tables. Both failure modes need a database that outlives the process,
and splitcart's is in-memory and per process. A lock would serialise runs for
nothing, and a schema guard cannot tell a database that was never built from a
half-built one — pytest-django builds none at all for a session whose tests
never ask for one, so the guard broke `pytest <a file with no database tests>`
outright. Running with `SPLITCART_TEST_DB=mysql` reintroduces the shared
database and both failure modes with it; that is when those two fixtures earn
their place.

### `users/tests/conftest.py`

| Fixture            | What it is for                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------ |
| `user`             | An ordinary account, from `UserFactory`.                                                   |
| `auth_client`      | An `APIClient` holding `user`'s session cookies — the way the live frontend authenticates. |
| `other_user`       | A second account, for the cross-user boundary tests. Named for what it is for.             |
| `anonymous_id`     | The ID a signed-out browser carries.                                                       |
| `anonymous_client` | A signed-out `APIClient` that keeps one `anonymous_id` across requests.                    |

`anonymous_client` exists because `config.middleware.AnonymousUserMiddleware`
mints a fresh ID for any request that arrives without one. A plain `api_client`
is therefore a _different_ signed-out shopper on every request, which is useful
in its own right — it is how the tests prove two browsers cannot see each
other's carts.

### `pipeline/tests/conftest.py`

`mock_command`: a `MagicMock` standing in for a Django management command, with
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
copied between apps, promote it to the root file.

## 5. Fixing a failing test

Follow
[`../../freetheplatform/_docs/testing-standard-backend.md`](../../freetheplatform/_docs/testing-standard-backend.md#fixing-a-failing-test).
The short version: work out whether the test or the code is wrong before
changing either, and never weaken an assertion to get green. A file you find to
be dead code is worth saying out loud rather than leaving in place.

### Tests that are expected to fail

None, today. A `pytest.mark.xfail(strict=True)` on a single test is how a defect
found while writing tests, and not fixed because fixing it is a product or
compatibility decision, is recorded: the test asserts the behaviour that is
owed, and `strict=True` fails the run the day it starts passing, which is the
alarm to delete the marker. `xfail` is a record of a reported defect, not a way
to park a failing test.
