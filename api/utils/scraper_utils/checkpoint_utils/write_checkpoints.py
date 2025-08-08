import json
import os
from typing import Dict, Any

CHECKPOINT_FILE = os.path.join('api', 'data', 'checkpoints.json')

def write_checkpoints(data: Dict[str, Any]) -> None:
    """Writes the entire checkpoint file."""
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(data, f, indent=2)