# CLAUDE.md — Splitcart

## Project Overview

Splitcart is an Australian grocery price comparison platform. The core idea: instead of comparing single-store totals, it finds the cheapest way to split a shopping list across multiple supermarkets, accounting for delivery fees, distance, and user constraints. It normalizes messy supermarket data and matches equivalent products across different chains.

Live site: https://www.splitcart.com.au/

**Stack:** Django backend + React/TypeScript frontend. Deployed on PythonAnywhere. MySQL in production.

---

## Running Tests

```bash
./venv/Scripts/python -m pytest
```

All 355+ tests should pass.

---

## Project Structure

```
splitcart/
├── companies/          # Store, company, and geography models
├── products/           # Product, price, substitution models + primary API
├── scraping/           # Model-free app: scrapes raw data from supermarket APIs
├── data_management/    # Processes raw scraped data into the DB
├── users/              # Auth, shopping carts, price optimisation logic
├── frontend/           # React/TypeScript frontend (Vite)
├── splitcart/          # Django settings and root URL config
└── _docs/              # Architecture and feature documentation (see below)
```

Each Django app has its own `README.md` — worth a quick read before working in an unfamiliar app.

---

## _docs Directory

These files explain how specific features and subsystems work. Read the relevant one before making changes in that area. **Treat them as a guide, not ground truth — they may be out of date.**

| File | What it covers |
|---|---|
| `TESTING.md` | Testing philosophy, stack (pytest/factory_boy), directory structure, conftest fixtures |
| `scraping.md` | How the scraping pipeline works end to end |
| `scraper_testing.md` | Strategy for testing scrapers and normalization (E2E + drift detection) |
| `pipeline.md` | The full data pipeline from raw scrape to DB |
| `bargains.md` | Bargain detection logic |
| `categories.md` | Product categorisation system |
| `home.md` | Home page / featured content logic |
| `recommendations.md` | Product recommendation system |
| `savings_calc.md` | How savings are calculated |
| `store_grouping.md` | How stores are grouped for comparison |
| `substitutions.md` | Product substitution matching logic |

---
