import sys

def print_progress_bar(iteration, total, lat, lon, store_count):
    """Displays a detailed progress bar with store count."""
    percentage = 100 * (iteration / total)
    bar_length = 40
    filled_length = int(bar_length * iteration // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    sys.stdout.write(f'\rProgress: |{bar}| {percentage:.2f}% ({iteration}/{total}) | Stores Found: {store_count} | Coords: ({lat:.2f}, {lon:.2f})')
    sys.stdout.flush()