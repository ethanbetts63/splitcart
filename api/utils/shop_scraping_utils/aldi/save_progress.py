import json

def save_progress(PROGRESS_FILE, lat, lon):
    """Saves the last processed coordinates to a file."""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'last_lat': round(lat, 2), 'last_lon': round(lon, 2)}, f)
