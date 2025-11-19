from django.db import transaction
from django.utils.text import slugify
from products.models import Product
from companies.models import Category

class CategoryManager:
    """
    Manages the creation of categories and their relationships to products and parents.
    """
    def __init__(self, command, caches, cache_updater):
        self.command = command
        self.caches = caches
        self.cache_updater = cache_updater

    def _create_new_categories(self, all_category_paths, company_obj):
        """Ensures all categories from the file exist in the database."""
        self.command.stdout.write("    - Ensuring all categories exist...")
        
        all_required_cat_tuples = {(name, company_obj.id) for path in all_category_paths for name in path}
        existing_cat_tuples = set(self.caches['categories'].keys())
        new_cat_tuples = all_required_cat_tuples - existing_cat_tuples

        if not new_cat_tuples:
            self.command.stdout.write("      - No new categories to create.")
            return

        self.command.stdout.write(f"      - Found {len(new_cat_tuples)} new categories to create for {company_obj.name}.")
        new_category_names = {t[0] for t in new_cat_tuples}
        new_categories_to_create = [
            Category(name=name, slug=slugify(name), company=company_obj) 
            for name in new_category_names
        ]
        
        try:
            with transaction.atomic():
                Category.objects.bulk_create(new_categories_to_create, ignore_conflicts=True)
            
            # Re-fetch and update cache
            newly_created_cats = Category.objects.filter(company=company_obj, name__in=new_category_names)
            for category in newly_created_cats:
                self.cache_updater('categories', (category.name, category.company_id), category)
            self.command.stdout.write("      - Shared category cache updated.")

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"      - An error occurred during category creation: {e}"))
            raise

    def _create_parent_child_links(self, all_category_paths, company_obj):
        """Creates the hierarchical links between parent and child categories."""
        self.command.stdout.write("    - Creating parent-child category relationships...")
        CategoryParents = Category.parents.through
        links_to_create = []
        
        # Fetch all existing links from the DB at once to avoid repeated queries
        seen_links = set(CategoryParents.objects.values_list('from_category_id', 'to_category_id'))

        for path in all_category_paths:
            for i in range(len(path) - 1):
                parent_name = path[i]
                child_name = path[i+1]
                
                parent_cat = self.caches['categories'].get((parent_name, company_obj.id))
                child_cat = self.caches['categories'].get((child_name, company_obj.id))

                if parent_cat and child_cat:
                    if (child_cat.id, parent_cat.id) not in seen_links:
                        links_to_create.append(
                            CategoryParents(from_category_id=child_cat.id, to_category_id=parent_cat.id)
                        )
                        seen_links.add((child_cat.id, parent_cat.id))
        
        if links_to_create:
            self.command.stdout.write(f"      - Creating {len(links_to_create)} new parent-child links.")
            with transaction.atomic():
                CategoryParents.objects.bulk_create(links_to_create, ignore_conflicts=True)
        else:
            self.command.stdout.write("      - No new parent-child links to create.")

    def _link_products_to_categories(self, raw_product_data, company_obj):
        """Links products to their leaf categories."""
        self.command.stdout.write("    - Creating product-to-category relationships...")
        ProductCategory = Product.category.through
        links_to_create = []
        
        # Fetch all existing links from the DB at once
        seen_links = set(ProductCategory.objects.values_list('product_id', 'category_id'))

        for data in raw_product_data:
            product_dict = data.get('product', {})
            path = product_dict.get('category_path')
            
            # Get product_id from shared cache
            product_id = self.caches['products_by_norm_string'].get(product_dict.get('normalized_name_brand_size'))

            if product_id and path and isinstance(path, list):
                leaf_category_name = path[-1]
                category_obj = self.caches['categories'].get((leaf_category_name, company_obj.id))
                
                if category_obj:
                    if (product_id, category_obj.id) not in seen_links:
                        links_to_create.append(
                            ProductCategory(product_id=product_id, category_id=category_obj.id)
                        )
                        seen_links.add((product_id, category_obj.id))
        
        if links_to_create:
            self.command.stdout.write(f"      - Creating {len(links_to_create)} new product-category links.")
            with transaction.atomic():
                ProductCategory.objects.bulk_create(links_to_create, ignore_conflicts=True)
        else:
            self.command.stdout.write("      - No new product-category links to create.")

    def process(self, raw_product_data, company_obj):
        """
        Orchestrates the three-step process of creating categories and their relationships.
        """
        self.command.stdout.write(f"  - CategoryManager: Processing categories for {company_obj.name}...")

        all_category_paths = {
            tuple(data['product']['category_path'])
            for data in raw_product_data
            if data.get('product', {}).get('category_path')
        }

        if not all_category_paths:
            self.command.stdout.write("    - No category paths found in file.")
            return

        # Step 1: Ensure all categories exist
        self._create_new_categories(all_category_paths, company_obj)

        # Step 2: Create parent-child links
        self._create_parent_child_links(all_category_paths, company_obj)

        # Step 3: Link products to their categories
        self._link_products_to_categories(raw_product_data, company_obj)
