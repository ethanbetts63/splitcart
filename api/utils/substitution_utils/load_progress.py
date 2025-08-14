
import json
from typing import Set, Optional

def load_progress(file_path: str) -> Optional[Set[str]]:
    """
    Loads the set of remaining product IDs from a JSON progress file.

    Args:
        file_path: The path to the progress file.

    Returns:
        A set of product IDs to process, or None if the file doesn't exist.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return set(data.get('remaining_ids', []))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None
