import sys

def print_progress_bar(iteration, total, lat, lon, store_count):
    """Displays a simplified progress message with store count and coordinates."""
    sys.stdout.write(f'\rProgress: Stores Found: {store_count} | Coords: ({lat:.2f}, {lon:.2f})')
    sys.stdout.flush()
