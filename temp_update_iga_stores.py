
import os
import json
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "splitcart.settings")
django.setup()

from companies.models.store import Store

def update_iga_store_names():
    iga_stores_dir = os.path.join(os.path.dirname(__file__), 'store_data', 'stores_iga')
    for filename in os.listdir(iga_stores_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(iga_stores_dir, filename)
            with open(filepath, 'r') as f:
                data = json.load(f)
                for store_data in data.get('stores', []):
                    store_id = store_data.get('storeId')
                    store_name = store_data.get('storeName')
                    if store_id and store_name:
                        try:
                            store = Store.objects.get(store_id=store_id, company__name='Iga')
                            store.store_name = store_name
                            store.save()
                            print(f"Updated store_id {store_id} with name {store_name}")
                        except Store.DoesNotExist:
                            print(f"Store with store_id {store_id} not found.")
                        except Exception as e:
                            print(f"An error occurred: {e}")

if __name__ == "__main__":
    update_iga_store_names()
