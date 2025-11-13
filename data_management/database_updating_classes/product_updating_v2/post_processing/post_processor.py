from django.db import transaction
from products.models import Product, Price
from companies.models import Company
from ...translation_table_generators.brand_translation_table_generator import BrandTranslationTableGenerator
from ...translation_table_generators.product_translation_table_generator import ProductTranslationTableGenerator
from .sku_reconciler import SkuReconciler
from ..product_reconciler import ProductReconciler
from ..brand_reconciler import BrandReconciler
from .category_cycle_manager import CategoryCycleManager
from ..unit_of_work import UnitOfWork

class PostProcessor:
    def __init__(self, command):
        self.command = command
        # The PostProcessor now manages its own UnitOfWork for all reconciliation tasks
        self.unit_of_work = UnitOfWork(self.command)

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("--- Post-Processing Run Started ---"))

        # Run SKU-based reconciliation first, as it's the most definitive
        sku_reconciler = SkuReconciler(self.command, self.unit_of_work)
        sku_reconciler.run()

        # Regenerate the translation tables to include new variations from the main run AND the SKU reconciliation
        BrandTranslationTableGenerator().run()
        ProductTranslationTableGenerator().run()

        # Run the name-based product reconciler, which will stage changes in the UoW
        product_reconciler = ProductReconciler(self.command, self.unit_of_work)
        product_reconciler.run()

        # Run the brand reconciler
        brand_reconciler = BrandReconciler(self.command)
        brand_reconciler.run()

        # --- Commit all staged changes from the reconcilers ---
        self.commit_reconciliation_changes(sku_reconciler, product_reconciler, brand_reconciler)

        # Run category cycle pruning as a final cleanup step
        self.command.stdout.write(self.command.style.SUCCESS("--- Running Category Cycle Pruning ---"))
        all_companies = Company.objects.all()
        if not all_companies.exists():
            self.command.stdout.write(self.command.style.WARNING("No companies found, skipping cycle pruning."))
        else:
            for company in all_companies:
                manager = CategoryCycleManager(self.command, company)
                manager.prune_cycles()
        
        self.command.stdout.write(self.command.style.SUCCESS("--- Post-Processing Run Finished ---"))

    def commit_reconciliation_changes(self, sku_reconciler, product_reconciler, brand_reconciler):
        """
        Commits all changes staged during the reconciliation process.
        """
        self.command.stdout.write(self.command.style.SUCCESS("--- Committing Reconciliation Changes ---"))
        
        prices_to_create = []
        prices_to_update = []
        
        # De-duplicate and sort prices from the UoW
        seen_product_store_pairs = set()
        for price_data in self.unit_of_work.prices_to_upsert:
            product_id = price_data['product'].id
            store_id = price_data['store'].id
            pair = (product_id, store_id)
            
            if pair in seen_product_store_pairs:
                continue
            seen_product_store_pairs.add(pair)

            existing_price = Price.objects.filter(product_id=product_id, store_id=store_id).first()
            if existing_price:
                for key, value in price_data.items():
                    if key not in ['product', 'store']:
                        setattr(existing_price, key, value)
                prices_to_update.append(existing_price)
            else:
                prices_to_create.append(Price(**price_data))

        with transaction.atomic():
            # 1. Create/Update prices staged by all reconcilers
            if prices_to_create:
                Price.objects.bulk_create(prices_to_create, batch_size=500)
                self.command.stdout.write(f"  - Bulk created {len(prices_to_create)} new prices from merged products.")

            if prices_to_update:
                update_fields = ['scraped_date', 'price', 'was_price', 'unit_price', 'unit_of_measure', 'per_unit_price_string', 'is_on_special', 'source']
                Price.objects.bulk_update(prices_to_update, update_fields, batch_size=500)
                self.command.stdout.write(f"  - Bulk updated {len(prices_to_update)} existing prices from merged products.")
            
            # 2. Handle updates to canonical products from the name-based reconciler
            if product_reconciler.products_to_update:
                Product.objects.bulk_update(product_reconciler.products_to_update, ['normalized_name_brand_size_variations'], batch_size=500)
                self.command.stdout.write(f"  - Bulk updated {len(product_reconciler.products_to_update)} canonical products with new name variations.")

            # 3. Consolidate and delete all old prices from merged duplicates
            all_prices_to_delete_ids = set(product_reconciler.prices_to_delete_ids) | set(sku_reconciler.prices_to_delete_ids)
            if all_prices_to_delete_ids:
                Price.objects.filter(id__in=all_prices_to_delete_ids).delete()
                self.command.stdout.write(f"  - Bulk deleted {len(all_prices_to_delete_ids)} old prices from all duplicate products.")

            # 4. Consolidate and delete all duplicate products
            name_based_duplicates_ids = {p.id for p in product_reconciler.duplicates_to_delete}
            sku_based_duplicates_ids = {p.id for p in sku_reconciler.products_to_delete}
            all_products_to_delete_ids = name_based_duplicates_ids | sku_based_duplicates_ids
            
            if all_products_to_delete_ids:
                Product.objects.filter(id__in=all_products_to_delete_ids).delete()
                self.command.stdout.write(f"  - Bulk deleted {len(all_products_to_delete_ids)} total duplicate products.")
