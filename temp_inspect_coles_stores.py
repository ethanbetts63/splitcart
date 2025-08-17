
from companies.models import Store, Company

try:
    coles_company = Company.objects.get(name='Coles')
    coles_stores = Store.objects.filter(company=coles_company)

    print(f"Found {len(coles_stores)} Coles stores.")

    for store in coles_stores:
        print(f"Store ID: {store.store_id}, Store Name: {store.store_name}")

except Company.DoesNotExist:
    print("Coles company not found in the database.")
