import json

def save_progress(PROGRESS_FILE, lat, lon, lat_step, lon_step, stores_found):
    """Saves the last processed coordinates, step values, and store count to a file."""
    progress = {
        'last_lat': round(lat, 2),
        'last_lon': round(lon, 2),
        'lat_step': lat_step,
        'lon_step': lon_step,
        'stores_found': stores_found
    }
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=4)
