import json
import os
from typing import Dict, Any, List

CHECKPOINT_FILE = os.path.join('api', 'data', 'checkpoints.json')

def _read_checkpoints() -> Dict[str, Any]:
    """Reads the entire checkpoint file."""
    if not os.path.exists(CHECKPOINT_FILE):
        return {}
    try:
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def _write_checkpoints(data: Dict[str, Any]) -> None:
    """Writes the entire checkpoint file."""
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def read_checkpoint(company_name: str) -> Dict[str, Any]:
    """
    Reads the progress checkpoint for a specific company.

    Args:
        company_name: The name of the company (e.g., 'woolworths').

    Returns:
        A dictionary with the last saved progress, or a default structure if none exists.
    """
    checkpoints = _read_checkpoints()
    return checkpoints.get(company_name, {
        "current_store": None,
        "completed_categories": [],
        "current_category": None,
        "last_completed_page": 0
    })

def update_page_progress(company_name: str, store: str, completed_cats: List[str], current_cat: str, page_num: int) -> None:
    """
    Updates the checkpoint file with the latest page progress for a company.

    Args:
        company_name: The name of the company.
        store: The current store being scraped.
        completed_cats: A list of categories already completed for this store.
        current_cat: The category currently being scraped.
        page_num: The last successfully completed page number.
    """
    checkpoints = _read_checkpoints()
    checkpoints[company_name] = {
        "current_store": store,
        "completed_categories": completed_cats,
        "current_category": current_cat,
        "last_completed_page": page_num
    }
    _write_checkpoints(checkpoints)

def mark_category_complete(company_name: str, store: str, completed_cats: List[str], new_completed_cat: str) -> None:
    """

    Updates the checkpoint when a category is fully scraped.

    Args:
        company_name: The name of the company.
        store: The current store being scraped.
        completed_cats: The list of previously completed categories.
        new_completed_cat: The category that has just been completed.
    """
    checkpoints = _read_checkpoints()
    
    updated_completed_cats = completed_cats[:]
    if new_completed_cat not in updated_completed_cats:
        updated_completed_cats.append(new_completed_cat)

    checkpoints[company_name] = {
        "current_store": store,
        "completed_categories": updated_completed_cats,
        "current_category": None,
        "last_completed_page": 0
    }
    _write_checkpoints(checkpoints)

def clear_checkpoint(company_name: str) -> None:
    """
    Clears the checkpoint for a company once scraping is fully complete.

    Args:
        company_name: The name of the company.
    """
    checkpoints = _read_checkpoints()
    if company_name in checkpoints:
        del checkpoints[company_name]
        _write_checkpoints(checkpoints)
