
import sys

def print_progress(completed_count: int, total_count: int, substitutes_found: int):
    """
    Prints a simple progress message to the console.

    Args:
        completed_count: The number of items processed so far.
        total_count: The total number of items to process.
        substitutes_found: The total number of substitutes found so far.
    """
    # Ensure completed_count does not exceed total_count for display purposes
    display_completed = min(completed_count, total_count)
    
    text = f"Progress: {display_completed} completed out of {total_count} (found {substitutes_found} substitutes)"
    # Use carriage return to keep the progress on a single line, updating itself
    sys.stdout.write(f"\r{text}")
    sys.stdout.flush()
