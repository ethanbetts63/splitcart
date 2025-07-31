import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify
from stores.models import Store, Category
from products.models import Product, Price

class Command(BaseCommand):
    help = 'Processes cleaned JSON files, populates the database, and archives the files.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting data processing and database population ---"))
        
        processed_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'processed_data')
        archive_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'archive')
        os.makedirs(archive_path, exist_ok=True)

        for store_name in os.listdir(processed_data_path):
            store_dir = os.path.join(processed_data_path, store_name)
            if not os.path.isdir(store_dir): continue

            self.stdout.write(self.style.SUCCESS(f"\n--- Processing Store: {store_name.capitalize()} ---"))
            store, _ = Store.objects.get_or_create(name=store_name.capitalize(), defaults={'base_url': f'https://www.{store_name}.com.au'})

            for file_name in os.listdir(store_dir):
                if not file_name.endswith('.json'): continue
                file_path = os.path.join(store_dir, file_name)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                products = data.get('products', [])
                if not products:
                    self.stdout.write(self.style.WARNING(f"  - No products found in {file_name}, skipping."))
                    continue

                self.stdout.write(f"  - Processing {len(products)} products from {file_name}")

                for product_data in products:
                    parent_cat = None
                    for dept in product_data.get('departments', []):
                        if dept.get('id'):
                            parent_cat, _ = Category.objects.get_or_create(
                                store_category_id=dept.get('id'),
                                defaults={
                                    'name': dept.get('name'),
                                    'slug': slugify(dept.get('name')),
                                    'parent': None,
                                    'store': store
                                }
                            )
                        else:
                            parent_cat, _ = Category.objects.get_or_create(
                                name=dept.get('name'),
                                parent=None,
                                store=store,
                                defaults={'slug': slugify(dept.get('name'))}
                            )

                    child_cat = parent_cat
                    for cat in product_data.get('categories', []):
                        if cat.get('id'):
                            child_cat, _ = Category.objects.get_or_create(
                                store_category_id=cat.get('id'),
                                defaults={
                                    'name': cat.get('name'),
                                    'slug': slugify(f"{parent_cat.name}-{cat.get('name')}"),
                                    'parent': parent_cat,
                                    'store': store
                                }
                            )
                        else:
                            child_cat, _ = Category.objects.get_or_create(
                                name=cat.get('name'),
                                parent=parent_cat,
                                store=store,
                                defaults={'slug': slugify(f"{parent_cat.name}-{cat.get('name')}")}
                            )
                        parent_cat = child_cat

                    final_cat = child_cat
                    for sub_cat in product_data.get('subcategories', []):
                        if sub_cat.get('id'):
                            final_cat, _ = Category.objects.get_or_create(
                                store_category_id=sub_cat.get('id'),
                                defaults={
                                    'name': sub_cat.get('name'),
                                    'slug': slugify(f"{child_cat.name}-{sub_cat.get('name')}"),
                                    'parent': child_cat,
                                    'store': store
                                }
                            )
                        else:
                            final_cat, _ = Category.objects.get_or_create(
                                name=sub_cat.get('name'),
                                parent=child_cat,
                                store=store,
                                defaults={'slug': slugify(f"{child_cat.name}-{sub_cat.get('name')}")}
                            )
                        child_cat = final_cat

                    product, created = Product.objects.update_or_create(
                        name=product_data.get('name'),
                        brand=product_data.get('brand', 'N/A'),
                        size=product_data.get('package_size', 'N/A'),
                        defaults={
                            'barcode': product_data.get('barcode'),
                            'category': final_cat
                        }
                    )

                    Price.objects.create(
                        product=product,
                        store=store,
                        price=product_data.get('price', 0.0),
                        was_price=product_data.get('was_price', 0.0),
                        is_on_special=product_data.get('is_on_special', False),
                        scraped_at=data['metadata']['scraped_at']
                    )

                archive_file_path = os.path.join(archive_path, store_name, os.path.basename(file_path))
                os.makedirs(os.path.dirname(archive_file_path), exist_ok=True)
                os.rename(file_path, archive_file_path)
                self.stdout.write(f"    - Archived {file_name}")

        self.stdout.write(self.style.SUCCESS("\n--- All data processing and population complete ---"))
