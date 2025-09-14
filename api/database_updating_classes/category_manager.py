from django.utils.text import slugify
from products.models import Product
from companies.models import Category, Company

class CategoryManager:
    """
    Handles the creation of categories and their relationships to products.
    This version uses a company-aware cache and re-fetches categories after
    bulk creation to ensure data integrity on all database backends.
    """
    def __init__(self, command):
        self.command = command
        self.category_cache = {
            (c.name, c.company_id): c 
            for c in Category.objects.select_related('company').all()
        }

    def process_categories(self, consolidated_data, product_cache, store_obj):
        self.command.stdout.write("--- Pass 3: Batch creating category relationships (Company-Aware) ---")
        
        if not consolidated_data:
            return

        try:
            company_name = next(iter(consolidated_data.values()))['metadata']['company']
            company_obj, _ = Company.objects.get_or_create(name__iexact=company_name, defaults={'name': company_name})
        except (StopIteration, KeyError):
            self.command.stderr.write(self.command.style.ERROR("Could not determine company from file data. Skipping category processing."))
            return

        all_category_paths = self._collect_all_paths(consolidated_data)
        self._create_new_categories(all_category_paths, company_obj)
        self._create_parent_child_links(all_category_paths, company_obj)
        self._link_products_to_categories(consolidated_data, product_cache, company_obj)

    def _collect_all_paths(self, consolidated_data):
        all_paths = set()
        for data in consolidated_data.values():
            path = data.get('product', {}).get('category_path')
            if path and isinstance(path, list):
                all_paths.add(tuple(path))
        return all_paths

    def _create_new_categories(self, all_category_paths, company_obj):
        self.command.stdout.write("  Part A: Ensuring all categories exist...")
        all_required_cat_tuples = {(name, company_obj.id) for path in all_category_paths for name in path}
        
        existing_cat_tuples = set(self.category_cache.keys())
        new_cat_tuples = all_required_cat_tuples - existing_cat_tuples

        if not new_cat_tuples:
            self.command.stdout.write("    - No new categories to create for this company.")
            return

        self.command.stdout.write(f"    - Creating {len(new_cat_tuples)} new categories for {company_obj.name}...")
        new_category_names = {t[0] for t in new_cat_tuples}
        new_categories_to_create = [
            Category(name=name, slug=slugify(name), company=company_obj) 
            for name in new_category_names
        ]
        
        try:
            # NOTE: ignore_conflicts is not fully supported on SQLite with multi-column constraints,
            # but we proceed assuming names within a company are not duplicated in the source file.
            Category.objects.bulk_create(new_categories_to_create, ignore_conflicts=True)

            # --- THE FIX --- 
            # Re-fetch newly created categories to get complete objects with DB IDs,
            # as bulk_create on SQLite does not return them.
            self.command.stdout.write("    - Refreshing cache with newly created categories...")
            newly_created_cats = Category.objects.filter(company=company_obj, name__in=new_category_names)
            
            for category in newly_created_cats:
                self.category_cache[(category.name, category.company_id)] = category

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"An error occurred during category creation: {e}"))

    def _create_parent_child_links(self, all_category_paths, company_obj):
        self.command.stdout.write("  Part B: Creating parent-child relationships...")
        CategoryParents = Category.parents.through
        links_to_create = []
        seen_links = set()

        for path in all_category_paths:
            for i in range(len(path) - 1):
                parent_name = path[i]
                child_name = path[i+1]
                
                parent_cat = self.category_cache.get((parent_name, company_obj.id))
                child_cat = self.category_cache.get((child_name, company_obj.id))

                if parent_cat and child_cat:
                    # Use parent and child IDs for the seen_links key to be robust
                    link_key = (parent_cat.id, child_cat.id)
                    if link_key not in seen_links:
                        links_to_create.append(
                            CategoryParents(from_category_id=child_cat.id, to_category_id=parent_cat.id)
                        )
                        seen_links.add(link_key)
        
        if links_to_create:
            self.command.stdout.write(f"    - Creating {len(links_to_create)} unique parent-child links for {company_obj.name}...")
            CategoryParents.objects.bulk_create(links_to_create, ignore_conflicts=True, batch_size=999)

    def _link_products_to_categories(self, consolidated_data, product_cache, company_obj):
        self.command.stdout.write("  Part C: Creating product-category relationships...")
        ProductCategory = Product.category.through
        links_to_create = []
        seen_links = set()

        for key, data in consolidated_data.items():
            product = product_cache.get(key)
            path = data.get('product', {}).get('category_path')
            if product and path and isinstance(path, list):
                leaf_category_name = path[-1]
                category = self.category_cache.get((leaf_category_name, company_obj.id))
                if category:
                    link_key = (product.id, category.id)
                    if link_key not in seen_links:
                        links_to_create.append(
                            ProductCategory(product_id=product.id, category_id=category.id)
                        )
                        seen_links.add(link_key)
        
        if links_to_create:
            self.command.stdout.write(f"    - Creating {len(links_to_create)} unique product-category links...")
            ProductCategory.objects.bulk_create(links_to_create, ignore_conflicts=True, batch_size=999)
