import json
import os
from typing import Dict, Any

CHECKPOINT_FILE = os.path.join('api', 'data', 'checkpoints.json')

def read_checkpoints() -> Dict[str, Any]:
    """Reads the entire checkpoint file."""
    if not os.path.exists(CHECKPOINT_FILE):
        return {}
    try:
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}