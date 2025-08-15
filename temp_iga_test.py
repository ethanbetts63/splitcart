import requests
import uuid
from api.utils.scraper_utils.get_iga_categories import get_iga_categories

# Dummy arguments for testing
test_store_id = "14804" # Using an ID from the previous error
test_session = requests.Session()
test_session_id = str(uuid.uuid4())

print(f"Attempting to fetch categories for store ID: {test_store_id}")
print(f"Using session ID: {test_session_id}")

categories = get_iga_categories(test_store_id, test_session, test_session_id)

print("\nResulting categories:")
print(categories)
