import os
import json
import shutil
from companies.models import Category, CategoryLink
from api.database_updating_classes.exact_category_matcher import ExactCategoryMatcher

INBOX_DIR = 'api/data/category_link_inbox'
PROCESSED_DIR = os.path.join(INBOX_DIR, 'processed')

def run_automatic_category_linker(command):
    """Processes equivalence decisions from the inbox directory."""
    # --- Run automatic exact matcher first ---
    matcher = ExactCategoryMatcher(command)
    matcher.run()


