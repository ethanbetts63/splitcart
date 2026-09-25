# SplitCart

**Live site:** https://www.splitcart.com.au/

## The smart grocery price comparison platform

SplitCart is an Australian grocery price comparison platform that finds the
cheapest way to buy your entire shopping list by splitting it across multiple
supermarkets. Instead of comparing single-store totals, it accounts for real
item-level price differences across Coles, Woolworths and Aldi, and for user
constraints like the maximum number of chains you are willing to shop at —
while also suggesting cheaper substitute products you approve.

Under the hood, it cleans and normalises messy supermarket data, matches
equivalent products across brands and chains, and runs a linear program to
surface the best combination — saving users real money without the manual
tab-hopping. It is built for budget-conscious shoppers who want clear,
actionable savings, and at scale it opens the door to insights like national
average prices, true discount tracking, and where groceries are genuinely
cheaper.

> **Two most interesting pieces of engineering in this codebase:**
>
> - [`_docs/normalized_name_brand_size.md`](_docs/normalized_name_brand_size.md)
>   — a self-improving feedback loop that learns to recognise the same product
>   across different supermarkets, getting better with every scrape run.
> - [`_docs/optimization.md`](_docs/optimization.md) — the cart split itself: a
>   mixed-integer program over per-product price slots that decides which chains
>   to use and what to buy where, with substitutes folded into the same solve.

## Documentation

`_docs/` holds in-depth references for the non-obvious parts of the system.
Start here before working in an unfamiliar area. Agents should start at
[`AGENTS.md`](AGENTS.md) instead, which routes by issue type.

- [`pipeline.md`](_docs/pipeline.md) — the full data lifecycle, from local
  scrape to live database, including the two-environment split
- [`scraping.md`](_docs/scraping.md) — how the scrapers work end to end
- [`scraper_testing.md`](_docs/scraper_testing.md) — how the scraping app is
  tested without ever contacting a supermarket
- [`normalized_name_brand_size.md`](_docs/normalized_name_brand_size.md) — how
  products are identified across chains using a self-improving normalised key
- [`product_brand.md`](_docs/product_brand.md) — the `ProductBrand` model,
  variation accumulation, and the brand translation table
- [`optimization.md`](_docs/optimization.md) — the LP-based cart splitting
  algorithm and the factors that determine savings potential
- [`substitutions.md`](_docs/substitutions.md) — how substitute products are
  matched and ranked across brands and categories
- [`bargains.md`](_docs/bargains.md) — how bargain products are detected and
  scored
- [`product_price_summary.md`](_docs/product_price_summary.md) — pre-computed
  price aggregates that make bargain queries fast
- [`bargain_stats.md`](_docs/bargain_stats.md) — pre-computed head-to-head
  company price comparison stats
- [`categories.md`](_docs/categories.md) — the product categorisation hierarchy
  and how primary categories are assigned
- [`TESTING.md`](_docs/TESTING.md) — testing philosophy, stack
  (pytest/factory_boy), and fixture conventions
- [`recommendations.md`](_docs/recommendations.md) — essentially a to-do list
- [`convergence/`](_docs/convergence/README.md) — the migration bringing
  SplitCart onto the shared engineering policies in `../freetheplatform/_docs`

---

## Project structure

A monorepo: a Django REST API at the root and a Next.js frontend under
`frontend/`. The two deploy separately.

### Backend

- **`products`** — products, brands, SKUs, prices, substitutions and price
  summaries, plus the primary API the frontend reads. See
  [`products/README.md`](products/README.md).
- **`companies`** — the `Company` model and the dual-taxonomy category system
  (scraped retailer categories on one side, the internal normalised hierarchy
  and pillar pages on the other). See
  [`companies/README.md`](companies/README.md).
- **`scraping`** — a model-free app that collects product, price and barcode
  data from supermarket APIs. Documented in
  [`_docs/scraping.md`](_docs/scraping.md).
- **`pipeline`** — the bridge between raw scraped JSONL and the structured
  database: ingest, reconcile, and generate all derived data. See
  [`pipeline/README.md`](pipeline/README.md).
- **`users`** — users, authentication, shopping carts, and the cart price
  optimisation. See [`users/README.md`](users/README.md).
- **`config`** — Django settings, root URLconf, sitemaps, middleware and
  permissions. `DJANGO_SETTINGS_MODULE` is `config.settings`.

### Frontend

`frontend/` is a **Next.js 16 App Router** application: React 19, TypeScript,
Tailwind CSS v4, Radix primitives for the interactive components, and TanStack
Query for server state. Routes live in `src/app/`; each `page.tsx` is thin and
delegates to a component in `src/page_components/`. All calls to the Django API
go through `src/services/apiClient.ts`.

See [`frontend/README.md`](frontend/README.md) to run it and
[`frontend/AGENTS.md`](frontend/AGENTS.md) before changing it.

---

## Local development

### Backend

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements_dev.txt
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py runserver
```

`requirements.txt` is the lean production set; `requirements_dev.txt` adds the
test stack and the ML libraries that substitution generation needs. The API
runs at `http://127.0.0.1:8000`.

You will need a local `.env` — see [Configuration](#configuration) below — and
a MySQL database.

### Frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:3000` and proxies `/api/*` through
`DJANGO_API_URL`.

### Resetting the database

`reset_django_project_robust.ps1` resets the database, deletes and regenerates
the migration files for `products`, `companies`, `pipeline` and `users`, and
applies a fresh schema. It does **not** drop the MySQL schema itself — it stops
and asks you to do that by hand first, and prints the two ways to do it. Read
the script before running it; it deletes migration history.

To rebuild the _data_ rather than the schema, use `manage.py reset_db`, which
replays the tracked archive and regenerates derived state. See
[`_docs/pipeline.md`](_docs/pipeline.md).

## Verify

```powershell
.\venv\Scripts\python.exe -m pytest
cd frontend
npm run check
npm run build
```

There is no CI in this repository. Nothing runs these for you.

### The commit hook

```powershell
git config core.hooksPath .githooks
```

**Once per clone, by hand.** `.git/` is never committed, so a fresh clone has
no hooks and says nothing about it — a missing hook looks exactly like a
passing one. That one line points git at the tracked `.githooks/` directory.

`.githooks/pre-commit` typechecks the frontend when anything under `frontend/`
is staged, and Prettier-checks the staged files. It is deliberately not the
full suite: a hook that takes minutes is a hook people bypass, and a rule
bypassed once stops being one. `pytest` and `npm run check` stay where the
verification table in [`AGENTS.md`](AGENTS.md) puts them — run by whoever
changed that area.

## Configuration

Create a `.env` in the repository root:

```
API_SERVER_URL="https://api.your-domain.com/"
EMAIL_HOST_PASSWORD=your_email_password
SECRET_KEY="your_django_secret_key"
INTERNAL_API_KEY="your_internal_api_key"
DEBUG=False
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=3306
```

`INTERNAL_API_KEY` authenticates the local machine to the server for the
internal endpoints the scrape and upload steps use; `API_SERVER_URL` is where
those endpoints live. Both are read in `config/settings.py`.

The frontend reads `DJANGO_API_URL` (server-side rewrite target),
`NEXT_PUBLIC_DJANGO_API_URL` (browser-side base) and `NEXT_PUBLIC_SITE_URL`
from `frontend/.env.local`.

## Deployment

The Django API is deployed to PythonAnywhere and served at
`api.splitcart.com.au`. The Next.js frontend is deployed to Vercel and served
at `www.splitcart.com.au`. Django does not serve the frontend.

On the API host:

```bash
git clone https://github.com/ethanbetts63/splitcart.git
cd splitcart
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

`collectstatic` gathers Django's own admin and DRF assets into `staticfiles/`.
There is no frontend build step here.

The WSGI file:

```python
import os
import sys

path = '/home/your_username/splitcart'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```
