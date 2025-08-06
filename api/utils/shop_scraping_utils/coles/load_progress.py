import os
import json

def load_progress(PROGRESS_FILE, LAT_MIN, LAT_STEP, LON_MIN, LON_MAX, LON_STEP):
    """Loads the last processed coordinates from a file, handling rollover."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                last_lat = progress.get('last_lat', LAT_MIN)
                last_lon = progress.get('last_lon', LON_MIN)

                if last_lon >= LON_MAX:
                    print(f"\nCompleted row for Lat: {last_lat}. Resuming on next latitude.")
                    return last_lat + LAT_STEP, LON_MIN
                else:
                    print(f"\nResuming from Lat: {last_lat}, Lon: {last_lon + LON_STEP}")
                    return last_lat, last_lon + LON_STEP
        except (json.JSONDecodeError, IOError):
            print(f"\nWarning: {PROGRESS_FILE} is corrupted or unreadable. Starting from the beginning.")
    return LAT_MIN, LON_MIN