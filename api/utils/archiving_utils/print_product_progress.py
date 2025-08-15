import sys

def print_product_progress(processed_count: int):
    """
    Prints a simple, self-updating progress message for product processing.

    Args:
        processed_count: The number of products processed so far.
    """
    # Use carriage return to keep the progress on a single line
    sys.stdout.write(f"\r  Processing product {processed_count}...")
    sys.stdout.flush()