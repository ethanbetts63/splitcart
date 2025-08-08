from api.utils.scraper_utils.checkpoint_utils.read_checkpoints import read_checkpoints
from api.utils.scraper_utils.checkpoint_utils.write_checkpoints import write_checkpoints
from typing import List

def mark_category_complete(company_name: str, store: str, completed_cats: List[str], new_completed_cat: str) -> None:
    """

    Updates the checkpoint when a category is fully scraped.

    Args:
        company_name: The name of the company.
        store: The current store being scraped.
        completed_cats: The list of previously completed categories.
        new_completed_cat: The category that has just been completed.
    """
    checkpoints = read_checkpoints()
    
    updated_completed_cats = completed_cats[:]
    if new_completed_cat not in updated_completed_cats:
        updated_completed_cats.append(new_completed_cat)

    checkpoints[company_name] = {
        "current_store": store,
        "completed_categories": updated_completed_cats,
        "current_category": None,
        "last_completed_page": 0
    }
    write_checkpoints(checkpoints)