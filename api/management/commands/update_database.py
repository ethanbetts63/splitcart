import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from companies.models import Company, Store, Category
from products.models import Product, Price

def get_or_create_category_hierarchy(category_string, company):
    """
    Gets or creates a category hierarchy from a string like 'cat1_cat2_cat3'.
    """
    parent = None
    for category_name in category_string.split('_'):
        category, _ = Category.objects.get_or_create(
            name=category_name,
            company=company,
            parent=parent
        )
        parent = category
    return parent

class Command(BaseCommand):
    help = 'Updates the database with processed product data.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting database update process ---"))

        processed_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'processed_data')

        for root, dirs, files in os.walk(processed_data_path):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    
                    with open(file_path, 'r') as f:
                        data = json.load(f)

                    metadata = data.get('metadata', {})
                    company_name = metadata.get('company')
                    state_name = metadata.get('state')
                    store_name = metadata.get('store')
                    category_string = metadata.get('category')

                    if not all([company_name, state_name, store_name, category_string]):
                        self.stdout.write(self.style.WARNING(f"Skipping file with missing metadata: {file_path}"))
                        continue

                    for product_data in data.get('products', []):
                        # a. Get or create the Company, Store, and Category.
                        company, _ = Company.objects.get_or_create(name=company_name)
                        store, _ = Store.objects.get_or_create(name=store_name, company=company, defaults={'state': state_name})
                        category = get_or_create_category_hierarchy(category_string, company)

                        # b. Get or create the Product.
                        product, created = Product.objects.get_or_create(
                            name=product_data['name'],
                            brand=product_data.get('brand', 'N/A'),
                            size=product_data.get('size', 'N/A'),
                            defaults={
                                'category': category,
                                'image_url': product_data.get('image_url'),
                                'description': product_data.get('description'),
                                'country_of_origin': product_data.get('country_of_origin'),
                                'allergens': product_data.get('allergens'),
                                'ingredients': product_data.get('ingredients'),
                                'nutritional_information': product_data.get('nutritional_information'),
                            }
                        )
                        if created:
                            self.stdout.write(self.style.SUCCESS(f"Created new product: {product}"))

                        # c. Deactivate old prices for the product at the store.
                        Price.objects.filter(product=product, store=store).update(is_active=False)

                        # d. Create the new Price record.
                        Price.objects.create(
                            product=product,
                            store=store,
                            store_product_id=product_data.get('store_product_id'),
                            price=product_data['price'],
                            was_price=product_data.get('was_price'),
                            unit_price=product_data.get('unit_price'),
                            unit_of_measure=product_data.get('unit_of_measure'),
                            is_on_special=product_data.get('is_on_special', False),
                            is_available=product_data.get('is_available', True),
                            url=product_data.get('url'),
                        )

        self.stdout.write(self.style.SUCCESS("--- Database update process complete ---"))
