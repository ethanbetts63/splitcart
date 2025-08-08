from api.utils.scraper_utils.checkpoint_utils.read_checkpoints import read_checkpoints
from typing import Dict, Any

def read_checkpoint(company_name: str) -> Dict[str, Any]:
    """
    Reads the progress checkpoint for a specific company.

    Args:
        company_name: The name of the company (e.g., 'woolworths').

    Returns:
        A dictionary with the last saved progress, or a default structure if none exists.
    """
    checkpoints = read_checkpoints()
    return checkpoints.get(company_name, {
        "current_store": None,
        "completed_categories": [],
        "current_category": None,
        "last_completed_page": 0
    })
