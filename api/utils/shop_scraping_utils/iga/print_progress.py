import sys

def print_progress(current_id, total_ids, found_count, message=""):
    """Displays a detailed, single-line progress bar."""
    percentage = 100 * (current_id / total_ids)
    bar_length = 30
    filled_length = int(bar_length * current_id // total_ids)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    status_message = message.ljust(40)
    sys.stdout.write(f'\rProgress: |{bar}| {percentage:.2f}% | Found: {found_count} | {status_message}')
    sys.stdout.flush()