from api.utils.scraper_utils.checkpoint_utils.read_checkpoints import read_checkpoints
from api.utils.scraper_utils.checkpoint_utils.write_checkpoints import write_checkpoints
from typing import List

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
    checkpoints = read_checkpoints()
    checkpoints[company_name] = {
        "current_store": store,
        "completed_categories": completed_cats,
        "current_category": current_cat,
        "last_completed_page": page_num
    }
    write_checkpoints(checkpoints)