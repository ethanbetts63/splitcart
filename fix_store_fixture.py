import json
import os

# The path to your fixture file
# This assumes the script is run from the project root directory
fixture_path = os.path.join('data_management', 'data', 'archive', 'db_backups', '2025-09-28', 'companies.store.json')

# List of fields to remove from the 'companies.store' model
fields_to_remove = [
    'is_active',
    'is_online_shopable',
    'phone_number',
    'address_line_2',
    'trading_hours',
    'facilities',
    'is_trading',
    'scheduled_at',
    'email',
    'status',
    'available_customer_service_types',
    'alcohol_availability',
]

print(f"Processing fixture file: {fixture_path}")

try:
    # Read the original fixture file
    with open(fixture_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Iterate over each object in the fixture and remove the specified fields
    for obj in data:
        if obj.get('model') == 'companies.store':
            for field in fields_to_remove:
                if field in obj['fields']:
                    del obj['fields'][field]

    # Write the modified data back to the file
    with open(fixture_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print("Successfully removed obsolete fields from the fixture.")

except FileNotFoundError:
    print(f"Error: Fixture file not found at {fixture_path}")
except json.JSONDecodeError:
    print("Error: Could not decode JSON. The file may be corrupt.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
