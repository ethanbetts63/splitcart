# Pipeline Private Data Refactor

## Current State

Splitcart now uses a top-level Django app named `pipeline`.

```text
pipeline/
  data/          # transient local/server pipeline files, ignored by parent repo
  private_data/  # nested private git repo location, ignored by parent repo
```

`config/settings.py` defines:

```python
PIPELINE_DATA_DIR = BASE_DIR / "pipeline" / "data"
PIPELINE_PRIVATE_DATA_DIR = BASE_DIR / "pipeline" / "private_data"
```

The parent repo ignores both `/pipeline/data/` and `/pipeline/private_data/`.

## Private Data

The private repo setup is intentionally manual. Once the private GitHub repo and SSH key are ready, clone it into:

```powershell
git clone git@github-splitcart-private:ethanbetts63/splitcart_private.git pipeline\private_data
```

Private files moved there so far:

```text
pipeline/private_data/outboxes/product_outbox/
pipeline/private_data/archive/db_backups/2025-09-28/
```

## Archive Command

Private data sync is handled by:

```powershell
python manage.py archive --pull
python manage.py archive --push
```

The command runs git inside `pipeline/private_data`. It expects that directory to already be a git repo.

## Removed Workflow

The old DB fixture archive workflow has been removed. The word `archive` now means private repo sync only.

## Follow-Up Checks

- After cloning the private repo, run `git -C pipeline/private_data status`.
- Run `python manage.py archive --push` once private data is ready to commit.
- Keep moving hardcoded pipeline file paths toward `settings.PIPELINE_DATA_DIR` and `settings.PIPELINE_PRIVATE_DATA_DIR` when touching nearby code.
