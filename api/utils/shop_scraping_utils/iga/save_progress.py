import json

def save_progress(PROGRESS_FILE, last_id):
    """Saves the last processed store ID to a file."""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'last_id': last_id}, f)
