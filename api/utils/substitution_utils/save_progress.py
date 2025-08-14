
import json
from typing import Set

def save_progress(file_path: str, remaining_ids: Set[str]):
    """
    Saves the set of remaining product IDs to a JSON progress file.

    Args:
        file_path: The path to the progress file.
        remaining_ids: The set of product IDs that are still to be processed.
    """
    with open(file_path, 'w') as f:
        json.dump({'remaining_ids': list(remaining_ids)}, f, indent=4)
