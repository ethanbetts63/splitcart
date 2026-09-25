"""Settings for the test suite: `config.settings`, with a database it can create.

`config.settings` points at MySQL on purpose -- it is the only engine the site
runs on, and `requirements.in` says so. It is also the reason the suite could
not be run at all. Creating a test database means `CREATE DATABASE
test_splitcart`, and no developer machine here holds that grant:

    GRANT ALL PRIVILEGES ON `test_allbikes`.*    TO `ethan`@`127.0.0.1`
    GRANT ALL PRIVILEGES ON `test_bloomprint`.*  TO `ethan`@`127.0.0.1`
    GRANT ALL PRIVILEGES ON `test_freethedesk`.* TO `ethan`@`127.0.0.1`
    -- nothing for splitcart

`mysqlclient` is the second half of the same wall: it is a C extension with no
wheel for the Python on this machine, so importing `django.db.backends.mysql`
fails during `django.setup()` and collection dies before a single test module is
read.

So the suite runs on an in-memory SQLite database, created fresh per process.
That is a deliberate trade, not an accident:

* it makes the suite runnable from a clean clone with no database privileges,
  which is the only version of "the tests pass" anyone can check;
* it costs the MySQL-specific half of persistence -- collation and case
  sensitivity on the unique `email` column, silent truncation under a
  non-strict `sql_mode`, index-length limits, and any migration that SQLite
  accepts and MySQL rejects. Bounds that used to depend on MySQL's truncation
  behaviour are now enforced in the serializers (see
  `users/serializers/cart_action_serializers.py`), which is where they belong.

Set `SPLITCART_TEST_DB=mysql` to run against the real engine once a grant
exists. That path needs `mysqlclient` installed and `CREATE`/`DROP` on
`test_<DB_NAME>`; see `_docs/TESTING.md`.
"""

import os

from config.settings import *  # noqa: F401,F403
from config.settings import BASE_DIR
from config.settings import DATABASES as _CONFIGURED_DATABASES

# `config.settings` reads this from `.env`, which a fresh clone does not have.
# Django refuses to start without one, and a test run has nothing to protect.
SECRET_KEY = os.getenv("SECRET_KEY") or "splitcart-test-key-not-a-secret"

if os.getenv("SPLITCART_TEST_DB") == "mysql":
    DATABASES = _CONFIGURED_DATABASES
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            # No NAME under TEST: Django builds the SQLite test database in
            # memory, so every run owns its own and two runs cannot collide.
            "TEST": {},
        }
    }
