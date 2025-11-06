
from .brand_translation_table_generator import BrandTranslationTableGenerator
from .product_translation_table_generator import ProductTranslationTableGenerator
from .product_reconciler import ProductReconciler
from .brand_reconciler import BrandReconciler
from companies.models import Company
from .category_cycle_manager import CategoryCycleManager

class PostProcessor:
    def __init__(self, command, unit_of_work):
        self.command = command
        self.unit_of_work = unit_of_work

    def run(self):


        # Regenerate the translation tables to include new variations
        BrandTranslationTableGenerator().run()
        ProductTranslationTableGenerator().run()

        # Run the product reconciler to merge duplicates based on the translation table
        product_reconciler = ProductReconciler(self.command)
        product_reconciler.run()

        # Run the brand reconciler to merge duplicates based on the translation table
        brand_reconciler = BrandReconciler(self.command)
        brand_reconciler.run()

        # Run category cycle pruning as a final cleanup step
        self.command.stdout.write(self.command.style.SUCCESS("--- Running Category Cycle Pruning ---"))
        all_companies = Company.objects.all()
        if not all_companies.exists():
            self.command.stdout.write(self.command.style.WARNING("No companies found, skipping cycle pruning."))
        else:
            for company in all_companies:
                manager = CategoryCycleManager(self.command, company)
                manager.prune_cycles()
