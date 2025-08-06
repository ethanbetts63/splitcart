import json
import os

def load_progress(PROGRESS_FILE):
    """Loads the last processed store ID from a file."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                last_id = progress.get('last_id', 0)
                print(f"Resuming from store ID: {last_id + 1}")
                return last_id
        except (json.JSONDecodeError, IOError):
            print(f"Warning: {PROGRESS_FILE} is corrupted. Starting from beginning.")
    return 0