import os
import json
import shutil
from companies.models import Category, CategoryLink
from api.database_updating_classes.exact_category_matcher import ExactCategoryMatcher

INBOX_DIR = 'api/data/category_link_inbox'
PROCESSED_DIR = os.path.join(INBOX_DIR, 'processed')

def update_category_links_from_inbox(command):
    """Processes equivalence decisions from the inbox directory."""
    # --- Run automatic exact matcher first ---
    matcher = ExactCategoryMatcher(command)
    matcher.run()

    # --- Then, process the manual inbox files ---
    command.stdout.write(command.style.SUCCESS("--- Checking for manual category link files in inbox... ---"))

    if not os.path.exists(INBOX_DIR):
        command.stdout.write(command.style.WARNING("Category link inbox directory not found."))
        return

    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)

    files_to_process = [f for f in os.listdir(INBOX_DIR) if f.endswith('.json')]

    if not files_to_process:
        command.stdout.write("No new category link files to process.")
        return

    command.stdout.write(f"Found {len(files_to_process)} files to process.")
    total_links_created = 0

    for filename in files_to_process:
        filepath = os.path.join(INBOX_DIR, filename)
        command.stdout.write(f"  - Processing {filename}...")
        
        try:
            with open(filepath, 'r') as f:
                decisions = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            command.stderr.write(command.style.ERROR(f"    Could not read or parse file {filename}: {e}"))
            continue

        links_in_file = 0
        for decision in decisions:
            try:
                # The new format is symmetrical, using category_a_id and category_b_id
                _, created = CategoryLink.objects.get_or_create(
                    category_a_id=decision['category_a_id'],
                    category_b_id=decision['category_b_id'],
                    defaults={'link_type': decision['type']}
                )
                if created:
                    links_in_file += 1
            except Exception as e:
                command.stderr.write(command.style.ERROR(f"    Error processing decision {decision}: {e}"))
        
        if links_in_file > 0:
            command.stdout.write(command.style.SUCCESS(f"    Created {links_in_file} new category links."))
        total_links_created += links_in_file

        # Move the processed file to the archive
        shutil.move(filepath, os.path.join(PROCESSED_DIR, filename))

    command.stdout.write(command.style.SUCCESS(f"--- Finished processing category links. Total new links created: {total_links_created} ---"))
