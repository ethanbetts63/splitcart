import json
import os
import random

def load_progress(PROGRESS_FILE, default_lat_min, default_lon_min):
    """
    Loads progress from a file.
    If the file exists, it reads the last coordinates, step values, and store count.
    If not, it generates random step values and returns defaults.
    """
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                # Ensure all required keys are present
                if all(k in progress for k in ['last_lat', 'last_lon', 'lat_step', 'lon_step', 'stores_found']):
                    return (
                        progress['last_lat'],
                        progress['last_lon'],
                        progress['lat_step'],
                        progress['lon_step'],
                        progress['stores_found']
                    )
                else:
                    # Corrupt or old format, start fresh
                    pass
        except (json.JSONDecodeError, KeyError):
            # If file is corrupt, start fresh
            pass
    
    # No progress file or it's corrupt/old, generate new random steps
    lat_step = random.uniform(0.25, 0.75)
    lon_step = random.uniform(0.25, 0.75)
    return default_lat_min, default_lon_min, lat_step, lon_step, 0
