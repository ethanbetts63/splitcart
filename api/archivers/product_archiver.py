
import sys
from datetime import datetime
from django.utils.text import slugify
from companies.models import Store
from api.archivers.base_archiver import BaseArchiver
from api.archivers.store_product_lister import StoreProductLister
from api.archivers.json_archive_writer import JsonArchiveWriter

class ProductArchiver(BaseArchiver):
    """
    Archives products for a single store.
    """

    def __init__(self, command, store_id):
        super().__init__(command)
        self.store_id = store_id
        self.json_writer = JsonArchiveWriter()

    def run(self):
        """
        Builds a JSON archive for a single store.
        """
        try:
            store = Store.objects.select_related('company').get(store_id=self.store_id)
            
            product_lister = StoreProductLister(store)
            product_list = []
            products_processed_count = 0

            for product_data in product_lister.get_products():
                product_list.append(product_data)
                products_processed_count += 1
                sys.stdout.write(f"\r  - Processed {products_processed_count} products...")
                sys.stdout.flush()

            if products_processed_count > 0:
                sys.stdout.write("\r" + " " * 50 + "\r") 
                sys.stdout.flush()

            if not product_list:
                return {'status': 'skipped', 'store_name': store.store_name, 'reason': 'No products found.'}

            store_data = {
                'metadata': {
                    'store_id': store.store_id,
                    'store_name': store.store_name,
                    'company_name': store.company.name,
                    'address_line_1': store.address_line_1,
                    'suburb': store.suburb,
                    'state': store.state,
                    'postcode': store.postcode,
                    'data_generation_date': datetime.now().isoformat(),
                    'total_products': len(product_list),
                },
                'products': product_list
            }

            company_slug = slugify(store.company.name)
            cleaned_store_id = store.store_id.split(':')[-1] if ':' in store.store_id else store.store_id

            saved_path = self.json_writer.save_store_data(company_slug, cleaned_store_id, store_data)
            return {'status': 'success', 'store_name': store.store_name, 'path': saved_path, 'products_found': len(product_list)}

        except Exception as e:
            return {'status': 'error', 'store_id': self.store_id, 'error': str(e)}
