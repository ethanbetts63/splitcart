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
always read C:\Users\ethan\coding\splitcart\README.md as the first thing you do. 
