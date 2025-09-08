import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'splitcart.settings')
django.setup()

from companies.models import Company, Category
from products.models import Product
from collections import defaultdict

def list_all_categories():
    """Lists all categories for all companies to help with debugging."""
    print("--- Listing All Categories ---")
    companies = Company.objects.all()
    if not companies.exists():
        print("No companies found in the database.")
        return

    for company in companies:
        print(f"\n--- {company.name} ---")
        cats = Category.objects.filter(company=company)
        if cats.exists():
            for cat in cats:
                print(f"  - {cat.name}")
        else:
            print(f"  No categories found for {company.name}.")

if __name__ == '__main__':
    list_all_categories()