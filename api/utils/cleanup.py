import os

def cleanup(file_paths: list):
    """
    Deletes a list of files from the filesystem.

    Args:
        file_paths: A list of absolute paths to the files to be deleted.
    """
    if not file_paths:
        print("Cleanup: No files to delete.")
        return

    print(f"--- Cleaning up {len(file_paths)} raw data files... ---")
    
    success_count = 0
    fail_count = 0

    for file_path in file_paths:
        try:
            # Check if the file exists before trying to delete it
            if os.path.exists(file_path):
                os.remove(file_path)
                # To keep the output clean, we can comment out the line-by-line print
                # print(f"  - Deleted {os.path.basename(file_path)}")
                success_count += 1
            else:
                print(f"  - Warning: File not found for deletion: {os.path.basename(file_path)}")
                fail_count += 1
        except OSError as e:
            print(f"  - FAILED to delete {os.path.basename(file_path)}. Error: {e}")
            fail_count += 1
    
    print(f"Cleanup complete. Successfully deleted: {success_count}. Failed: {fail_count}.")


